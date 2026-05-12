# User Review — Anita, the Skeptic

**Persona:** Anita, 52, professor of cognitive science at IIT Madras. Lives alone in a faculty flat. Owns a Kindle, a laptop, an old iPad. No smart speakers — actively dislikes them. Has read enough about AI ethics, surveillance capitalism, and household labor to be wary of everything in this category. Curious about robotics intellectually; skeptical of it commercially.

**Reading:** the project pitch + use cases.

---

## My honest reaction

Several pages of detailed engineering, written with care. The author is clearly competent. But I read this and I think: *who asked for this*.

That's not rhetorical. It's the question I want answered.

## What this product is, stripped of jargon

A robot that watches you, listens to you, learns where things are in your home, and does errands. The errands it can do are: drive to a room and report back. That's it.

Everything else is sensing and remembering. The "doing" is one thing.

For this to be valuable, the sensing-and-remembering has to be valuable enough on its own to justify a ₹72,000 device that lives in your living room. I am not convinced it is.

## My objections

### 1. The use cases are not real problems for me.

"Where did I leave my keys" — I have a hook by the door. They're there.

"What happened while I was out" — nothing happened while I was out. I live alone. If something happened, my building has CCTV.

"Go check if I left the stove on" — I would never let a robot tell me whether I left the stove on. I would walk back and check. The cost of being wrong is too high, and I do not trust a robot to be right.

These are not the problems of a 52-year-old academic living alone. They might be the problems of the author's life. The author has projected those problems onto a generic "user."

### 2. The robot does what most people don't want.

The defining experience of the last decade of consumer technology has been: products that watch us in our homes for our convenience, until we discover the cost. Echo Dots that record snippets of our living rooms. Doorbell cameras that subpoena themselves. TVs that monitor what we watch. The trajectory has not been good.

This robot is more invasive than any of those — it has a camera, a microphone, *and* it moves. It can come into the bathroom while I'm changing. It can park outside the bedroom door. The ability to be told "go away" is technically a feature, but the burden is now on me to remember to tell it that.

I have spent decades carving out a home that is *not* observed. I would not invite this in.

### 3. The privacy story is engineering, not ethics.

The doc says: event-driven recording, local-first inference, opt-in cloud. These are all good engineering decisions. None of them address my actual concern, which is *I do not want the robot, regardless of how well it implements privacy*.

The deeper issue: the question is not "what data leaves the home." The question is "what kind of home life is one in which I have a sensor that watches me."

This is not a technical objection that better engineering can fix. It's a values objection. The doc does not engage with it.

### 4. The architecture is impressive, but it's solving the wrong problem.

The author has done excellent work on reliability, BOM, software stack. The work is competent and serious. But it's all in service of an artifact whose existence in my home I would not want.

It's like reading a beautifully designed diesel engine for a car I don't want to drive. The craft is real; the project is misdirected.

### 5. The "for ageing parents" angle is not addressed.

The most defensible version of this product is for elder care — a robot that tells me when my 80-year-old mother has fallen, has not eaten, has not taken her medication. The architecture you've designed could absolutely do this. The doc does not mention it.

If I were going to recommend this product to anyone, it would be to my brother who lives 3,000 km away and worries about my mother. The robot for *him* watching *her* (with her consent) is a real product.

The robot for *me* in my own home is not.

### 6. The doc reflects a generation gap.

The author is, I am guessing, 30-45 years old. The use cases reflect that life: kids, busy schedule, want to optimize household time. These are not bad use cases. But they are the use cases of one demographic.

The 50+ Indian academic, the empty-nester, the introvert, the privacy-conscious, the spiritual home-keeper — none of these people's lives are visible in the doc. The robot is designed for the author's life.

That's fine for a personal project. It is not "general home robot."

## What I'd want to see addressed

If this becomes a product, I'd want the author to grapple with:

1. **Why does this exist.** Not "what does it do." Why was it built. What human need does it serve that wasn't already served. The "find the keys" use case is not a human need; it's a household nuisance, and AirTags exist.

2. **Who decides whether it's in the home.** In a multi-person household, the robot is a co-imposition. If one person wants it and others don't, what happens? Engineering can give you off-buttons; it can't resolve the social problem.

3. **What happens when it fails.** Not technically — emotionally. When the robot misunderstands you, or watches you when you didn't realize, or tells you it knows where you put something and is wrong. These accumulate. When does the user become demoralized?

4. **What does it mean to live with it.** A pet, a device, a tool, a roommate? The robot is none of those cleanly. The user has to invent the relationship. Is that a feature?

5. **What is lost.** A home without a sensing robot has a quality of being unobserved. That quality is itself valuable. The cost of installing the robot includes losing that quality. What replaces it?

These are the questions a thoughtful product addresses. They are not in the doc.

## What I'd actually find useful

If I were to be persuaded that a robot belongs in my home, it would have to do one of:

- **Eldercare for my mother**, with her consent, with my involvement, with clear off-switches.
- **Disability assistance** — the same tech for someone with mobility limits is not a nuisance; it's an aid.
- **Specific assistance for me** — fetch the book I left on the kitchen counter when I'm in bed; reach the top shelf I can't; carry the laundry basket. *Things I cannot easily do.*

The current spec serves none of these. It serves "convenient affluent able-bodied person whose problems are minor."

## What's good about the project

I want to be fair. Several things are admirable:

- **The honesty about scope.** "We don't do manipulation. We don't do continuous recording. We don't do speaker ID well." Most products lie. This one doesn't.

- **The reliability investment.** The author has thought about what happens at week 4, week 8, year 2. Most consumer products don't.

- **The privacy architecture.** Within the assumption that the robot exists, the architecture minimizes what's recorded, what leaves the home, what's stored. Within the assumption.

- **The open-source orientation.** A device whose code I can read, fork, modify is more trustworthy than one that's a black box. This matters.

If I were forced to have a household robot, I'd rather have this one than anything sold by Amazon or Google.

## My recommendation

The author should build this for himself. He clearly wants to. The work is competent. He'll learn enormously.

He should not, in my view, ship it as a consumer product without significantly more reflection on the questions above. The market readiness reviewer probably said something similar.

If the project has commercial potential, it's in eldercare or disability assistance, not in the affluent-techie market the doc implicitly targets. Those are harder, more regulated, more meaningful problems. They're also where the architecture would have to grow up.

## Score

As an engineering artifact: high.
As a thing I'd want in my home: not at any price.
As a thing I'd want for my mother (with her consent): possibly.
As a public good (open-source reference): valuable.

The author is clearly capable of building something useful. The question is whether the artifact described is that useful thing. I am unconvinced.
