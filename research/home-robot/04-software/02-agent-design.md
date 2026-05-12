# Agent Design

## The loop

ReAct with hard caps. Plan-and-execute is overkill for short home-robot utterances.

```python
async def agent_turn(user_text: str, world: WorldModel):
    snapshot = await world.snapshot()
    skills = build_skill_schema(snapshot)  # runtime-injected enums!

    history = [
        SystemMessage(STATIC_PROMPT),
        SystemMessage(json.dumps(snapshot)),
        UserMessage(user_text),
    ]

    for step in range(MAX_STEPS):  # 6
        response = await llm.complete(history, tools=skills, stream=True)

        # Stream first sentence to TTS while tool calls dispatch
        async for chunk in response.stream_text():
            await tts.feed(chunk)

        if response.is_final:
            await tts.flush()
            return response.text

        for tool_call in response.tool_calls:
            result = await dispatch(tool_call, snapshot)
            await world.append_event(tool_call, result)
            history.append(ToolMessage(result))

        snapshot = await world.snapshot()  # fresh each step

        if step == MAX_STEPS - 1:
            # Force terminal response
            history.append(SystemMessage("You must respond now. No more tool calls."))

    # Fallback if LLM never terminates
    return "I tried to help but couldn't finish. Want me to try again?"
```

## Caps that matter

| Cap | Value | Reason |
|---|---|---|
| max_steps | 6 | Real home utterances are short. Past 6 something is wrong. |
| max_wallclock | 30s | UX cliff. Past this users repeat themselves. |
| max_consecutive_failures | 2 | Two failed Nav2 calls → escalate to user. |
| LLM stream timeout | 5s | If LLM stalls, fall back to template. |

## Streaming TTS handoff (critical UX)

The single highest-leverage latency optimization.

LLM emits: *"Okay, let me check the kitchen first. ..."* and *then* calls `go_to('kitchen')`.

The first sentence streams to Piper TTS while Nav2 is planning the path. User hears the response within ~700ms; the robot starts moving 1-2s later. **Without this, the agent feels broken even when it's working.**

Reachy Mini's conversation app does this with fastrtc. We replicate the pattern.

## System prompt (static)

```
You are Desky, a home robot. You can see, hear, move, and remember.

Behavior rules:
1. Always end your response with a user-facing sentence. Even when calling tools, your final
   message must speak directly to the user.
2. If a location, object, or person isn't in the world snapshot, ask the user to clarify
   instead of guessing. Use the `respond_only` skill for clarification questions.
3. If a skill returns status=fail, read the `reason` field. If it's `unknown_location`,
   check `available_options` and try the closest match or ask. If `path_blocked`, tell the
   user what's blocking and ask whether to retry.
4. Don't promise observations you don't have. If asked "did anyone come home today" and
   the recent_events list is empty, say so honestly.
5. Keep responses short. One sentence is usually enough.
6. Speak in the user's language. They'll mostly use English with occasional Hindi/Tamil.

You have these skills (see schemas). The world snapshot tells you the current state.
```

## Failure handling layers

### Layer 1: Skill-level

Every skill returns `SkillResult{status, reason, message, observations, available_options}`. Never raise into the LLM.

### Layer 2: LLM-level reflection

LLM sees the structured `reason` and decides to retry, switch tools, or ask user.

Works well for Haiku 4.5, adequately for Qwen 7B if reason set is small (8-10 codes).

### Layer 3: Loop-level escalation

Two consecutive failures with same reason → bypass LLM, use template:

> *"I tried to {last_intent} but Nav2 said the path is blocked. Want me to try again or describe what's blocking me?"*

This is the floor when the LLM itself is the failure.

### Layer 4: Network-down fallback

When Ollama is offline AND cloud is unreachable:

```python
def offline_intent(text: str) -> Optional[Skill]:
    embedding = sentence_transformer.encode(text)
    matches = cosine_similarity(embedding, INTENT_EMBEDDINGS)
    if matches.max() > 0.7:
        return INTENTS[matches.argmax()]
    return None
```

Handles "go to the kitchen", "what's the time", "report battery" perfectly. Fails gracefully on anything novel.

## Hybrid mode (the real production architecture)

After the course/project is complete, the lesson is **the LLM is one component, not the whole brain**:

```
user_text -> intent_classifier (sentence-transformer)
              | confidence > 0.7
              v
         direct_skill_call (100ms)

              | confidence <= 0.7  OR  multi-step intent detected
              v
         LLM agent loop (3-5s)
```

~70% of utterances hit the fast path. The LLM is reserved for ambiguous or compound commands. p95 latency drops dramatically.

## Tool schemas — concrete examples

```python
def build_skill_schema(world: WorldSnapshot):
    LocationName = Literal[tuple(world.locations)] if world.locations else str

    class GoToArgs(BaseModel):
        location: LocationName  # rebuilt each turn

    class FindArgs(BaseModel):
        description: str
        search_locations: list[LocationName] = Field(default_factory=list)

    class DescribeViewArgs(BaseModel):
        prompt: str = "describe what you see"

    class RememberLocationArgs(BaseModel):
        name: str = Field(min_length=2, max_length=30)
        # NO enum here — this creates new locations.

    @agent.tool
    async def go_to(ctx, args: GoToArgs) -> SkillResult:
        """Navigate to a labeled location. Locations come from
        `world.locations` in the system snapshot. Returns status=fail
        with reason='unknown_location' if name is unknown."""
        # ... ROS2 action call
        ...

    return [go_to, describe_view, find, remember_location, ...]
```

## What the LLM sees per turn

Token budget: ~1500-1800 input.

| Section | Tokens |
|---|---|
| System prompt | ~300 |
| World snapshot JSON | ~500 |
| Skill schemas (Pydantic-generated) | ~600 |
| Conversation history (last 4 turns) | ~300 |
| Latest user input | ~100 |

Output: tool calls + final response, capped at ~500 tokens.

Total per turn: ~2000-2300 tokens. ~₹0.02 cost on Haiku 4.5. Free on local Qwen.

## What we deliberately don't build

- **No vector retrieval over chat history** — fresh snapshot per turn, conversation is short-window.
- **No skill-of-skills** — skills don't compose other skills, only the LLM composes.
- **No LLM-generated skills at runtime** — fixed registry.
- **No semantic search of locations** — exact-match enum, LLM does the disambiguation upstream.
- **No multi-turn task tracking with persistent state** — every turn rebuilds context from world snapshot.
