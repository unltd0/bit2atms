# Skill Registry and World Model

## The skill registry

A small, fixed set of skills. The LLM composes them; it doesn't define new ones at runtime.

### Skills

```python
# Locomotion
go_to(location_name: Literal[*KNOWN_LOCATIONS]) -> SkillResult
dock_now() -> SkillResult
return_home() -> SkillResult  # to docking station

# Perception
describe_view(prompt: str = "describe what you see") -> SkillResult
find(object_description: str, search_locations: list[str] = None) -> SkillResult
look_around(rotations: int = 1) -> SkillResult  # 360 pan, capture frames

# Memory
remember_location(name: str) -> SkillResult  # store current pose as named
where_was(object_name: str) -> SkillResult
recent_events(time_range: str, location: str = None, type: str = None) -> SkillResult

# Communication
report(text: str) -> SkillResult  # speak
ask(question: str) -> SkillResult  # speak + wait for STT response

# Meta
respond_only(text: str) -> SkillResult  # used when no other skill fits
```

### SkillResult schema

Every skill returns this, never raises:

```python
class SkillResult(BaseModel):
    status: Literal["ok", "fail", "partial"]
    reason: Literal[
        "completed",
        "unknown_location",
        "unknown_object",
        "path_blocked",
        "battery_low",
        "timeout",
        "user_interrupted",
        "perception_failed",
        "no_match"
    ]
    message: str  # human-readable
    observations: dict  # structured facts to write to world model
    available_options: list[str] | None  # e.g. valid locations when unknown_location
```

### Why this shape

- **status + reason as enums** — the LLM can reason about specific failure modes without parsing English.
- **observations field** — every skill call is also a memory event. The world model writes from this automatically.
- **available_options** — when the LLM hallucinates "garage" but the home has no garage, the result includes the actual list, and the LLM auto-corrects on next step.

## The world model

A small persistent service. Three tables in SQLite + one Chroma collection.

### Schema

```sql
-- Named places. Created by remember_location().
CREATE TABLE locations (
    name TEXT PRIMARY KEY,
    frame_id TEXT,        -- 'map'
    x REAL, y REAL, theta REAL,
    created_at TIMESTAMP,
    last_visited_at TIMESTAMP
);

-- Append-only event log. Source of truth for "what happened."
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TIMESTAMP NOT NULL,
    type TEXT NOT NULL,        -- 'observation', 'utterance', 'skill_call', 'navigation'
    location TEXT,             -- nullable
    payload_json TEXT NOT NULL,
    image_thumbnail_path TEXT  -- for VLM observations only
);

-- Object registry. Last-seen index over events.
CREATE TABLE objects (
    id TEXT PRIMARY KEY,        -- 'keys', 'red_mug', 'amazon_box'
    description TEXT,
    last_seen_ts TIMESTAMP,
    last_seen_location TEXT,
    last_seen_event_id INTEGER REFERENCES events(id),
    embedding_id TEXT           -- references chroma collection
);
```

Plus a Chroma collection for object embeddings (CLIP / SigLIP) so `find('the red one')` can do semantic search.

### Query API (HTTP, used by agent and LLM tools)

```
GET  /locations                     -> list of named locations
POST /locations                     -> add (used by remember_location skill)
GET  /objects?text=red+mug          -> semantic search
GET  /objects/{name}/last_seen      -> last-seen lookup
GET  /events?since=&location=&type= -> filtered event log
POST /events                        -> append (used by every skill that observes)
GET  /snapshot                      -> the JSON blob injected into LLM context
```

### The LLM context snapshot

Built fresh on every agent turn. ~500 tokens.

```json
{
  "now": "2026-05-09T14:32:11+05:30",
  "robot": {
    "pose_at": "kitchen",
    "battery_pct": 78,
    "docked": false,
    "current_speaker": "Guru"
  },
  "locations": [
    "kitchen", "living_room", "bedroom", "bathroom",
    "front_door", "guru_desk", "couch", "dining_table"
  ],
  "recent_observations": [
    {"t": "14:30", "where": "kitchen", "what": "person (Guru)"},
    {"t": "14:28", "where": "living_room", "what": "keys on sofa"},
    {"t": "14:15", "where": "front_door", "what": "amazon_box on doormat"}
  ],
  "objects_known": {
    "keys": "sofa, living_room (last seen 14:28)",
    "phone": "unknown",
    "amazon_box": "front_door (last seen 14:15)"
  },
  "last_user_request": "find my keys"
}
```

## The runtime-injected enum trick

The single biggest reliability lever for tool-call hallucination.

### Wrong (static enum)

```python
class GoToArgs(BaseModel):
    location: Literal["kitchen", "living_room", "bedroom"]  # baked at startup
```

The LLM still hallucinates "garage" if the conversation mentions it.

### Right (runtime-injected)

```python
def build_skill_schema(world: WorldSnapshot):
    LocationName = Literal[tuple(world.locations)]  # rebuilt each turn

    class GoToArgs(BaseModel):
        location: LocationName

    @agent.tool
    def go_to(ctx, args: GoToArgs) -> SkillResult: ...

    return [go_to, describe_view, find, ...]
```

With this trick, hallucination rate on Qwen 2.5 7B drops from ~15% to ~2%.

## What the LLM sees, end to end

Every turn, the agent assembles:

1. **System prompt** (static, ~300 tokens) — robot identity, behavior rules, "always emit a final user-facing response when done"
2. **World snapshot** (dynamic, ~500 tokens) — JSON blob above
3. **Skill schemas** (dynamic, ~600 tokens) — Pydantic-generated JSON schemas for each skill, with runtime enums
4. **Conversation so far** (dynamic, capped at 4 turns)
5. **Latest user input** (~50-100 tokens)

Total: ~1500-1800 tokens input per turn. Well within Haiku 4.5's 200k context, well within Qwen 2.5 7B's 128k.

Output: tool call(s) or final response. Cap at 6 tool calls per request.

## What we explicitly do NOT do

- **No vector retrieval over conversation history.** Conversation is short-window only. Persistent memory is in the structured event log, not in a vector store of chat turns.
- **No skill-of-skills.** Skills do not call other skills. The LLM is the only composer.
- **No LLM-generated skills at runtime.** The skill registry is fixed. No code-gen. No "if you need to do X, write a Python function and run it."
- **No semantic search of locations.** Locations are an exact-match enum. "the kitchen" must match `kitchen` literally — the LLM does the disambiguation upstream.
