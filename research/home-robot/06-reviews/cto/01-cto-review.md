# CTO Review

**Reviewer profile:** CTO of a hardware company. 15 years building shipped products. Has launched 3 consumer hardware products and killed 2. Reads BOMs for breakfast, has opinions on supply chain, knows what the difference between a demo and a product costs in dollars and months.

**Read of:** the project as documented in `00-overview/`, `01-vision/`, `02-architecture/`, `03-hardware/`, `04-software/`, `05-reliability/`.

---

## Summary

This is a well-scoped technical project but a confused product. The architecture is sound, the BOM is honest, the reliability work is unusually mature for a hobbyist write-up. What's missing is a clear answer to "who pays for this and why" — and that vacuum is the difference between a hobbyist's clever weekend and a thing that exists in the world a year from now.

If you want this to be just a personal project: ship it, you've done the right work, my comments here don't matter.

If you want this to be a product seed: read on. There's real risk that the architecture you've designed is over-engineered for what users will actually pay for, and under-engineered for what a real product needs.

## What I like

**The honesty about budget.** Most hobbyist BOMs lie by 40-60%. This one lies by maybe 10% (the buffer is too thin; in real builds first-version-broken parts run 15-20%, not 5%). I'd push the Tier A number to ₹78-80k landed before I'd believe it, but you're directionally right. That's rare.

**The capability cuts.** Dropping acoustic speaker ID, reframing continuous observation as event-driven — these are exactly the cuts a senior engineer makes after their first home robot project. You skipped the 3 months of pain that teaches them. Reading R/robotics or watching Boston Dynamics deployment talks gets you here. You did the homework.

**The reliability chapter.** This is the document that would make me hire whoever wrote it. Specifically the "₹2,650 buys you the difference between 30-day and demo." I have shipped products without 8 of those 12 items and paid for it with field returns. The watchdog + RTC + INA226 + pogo pins + mechanical bumper are the four-or-five things every consumer hardware reviewer has criticized our industry for skipping for 30 years. You named them.

**The split-brain architecture.** ESP32 for real-time + Pi for ROS + laptop for cognition is the right shape. Stretch shipped this. Astro shipped this. Anyone who tries to do all three on one board has not yet met production load.

**The LLM hybrid recommendation.** Intent classifier + behavior tree + LLM-as-fallback is the architecture every voice-product team I've talked to in 2026 has converged on, often after burning 6 months on LLM-everywhere. You skipped that lesson too.

## What I don't like

### 1. The product story is missing. This is the biggest gap.

You've described what the robot *does*. You haven't described **what changes in a user's life because they have one.** The "where did I leave my keys" use case is technically clean but commercially weak — Apple Find My + a $30 AirTag does this with 99% reliability and zero engineering. "What happened while I was out" is closer to real value but is competing with $80 Eufy/Ring cameras that already do clip-based summaries with cloud LLMs.

The robot's *unique* value proposition has to be something a fixed camera + a phone *can't* do. From your docs, that's:
- **Embodied response** — the robot turning, looking, reporting feels different from a notification
- **Multi-room presence** — but you cut that to single mobile in v1
- **Errand execution** — "go check the kitchen" is the only one with no fixed-camera substitute

If errand execution is the killer feature, the entire product should be designed around that with everything else as supporting cast. Right now it's the third use case in the doc and gets less architectural love than memory or summarization.

**Recommendation:** rewrite the vision doc to lead with "the robot goes places for you." Everything else is secondary.

### 2. The integration cost is buried.

You quote Tier A at ₹72k landed and 3 months evening hours. From a CTO's perspective: 3 months evening hours = ~120 hours of senior-engineer time. At ₹4,000/hr loaded cost, that's ₹4.8L of effort to build one robot. The BOM is 15% of the total cost.

This is fine for a hobby project. It is not fine for a product. If this becomes a product, the integration must collapse to days, not months, which means almost the entire stack needs to be productized as software-on-a-known-hardware-platform. That is a different project than the one you've documented.

**Recommendation:** decide explicitly — hobby project (BOM is the cost) or product seed (integration is the cost). Document which.

### 3. The cloud LLM dependency is undertheorized.

Haiku 4.5 at ₹0.10/interaction × 50/day = ₹150/month is fine for one user. For 1,000 users it's ₹15L/month, and you discover Anthropic doesn't volume-discount until you're at much bigger scale than that. For 10,000 users you have a real cost-of-goods problem and you're now competing on margin against companies whose entire moat is owning the model.

The local-Qwen-fallback is a smart hedge for offline. It's not a hedge for unit economics.

**Recommendation:** if this is a product, model the COGS at 1k/10k/100k users. If COGS doesn't work, redesign so the agent loop runs locally with Qwen as primary, cloud as fallback — opposite of what's documented.

### 4. The privacy story is good but un-marketed.

Event-driven recording, local-first inference, no continuous storage — these are real advantages and you're not foregrounding them. In an Indian market where DPDPA enforcement is ramping and in a global market where Ring is still recovering from the consent debacle, a robot that says *"never sees what doesn't matter"* is a real position.

The reliability doc should be a privacy doc. Or there should be a privacy doc.

**Recommendation:** write a `06-privacy.md` that documents the architectural privacy guarantees, what data exists where, what leaves the home, and how the user opts in to cloud. Make it readable by a non-engineer.

### 5. The supply chain is single-threaded.

Look at the BOM. RPLidar C1 — single supplier (Slamtec). XVF3800 — single supplier (XMOS via Seeed). Pi 5 — single supplier (Raspberry Pi Foundation, currently allocating). N20 motors — quality lottery suggests no real supplier; just commodity.

For a personal project this is fine. For a product, you have three single-points-of-failure on the supply chain. RPi shortage in 2021-2023 killed multiple products. Slamtec has been acquired-and-divested twice. XMOS is healthy but small. Each of these is a 6-month-delay risk.

**Recommendation:** for product readiness, identify a second source for each critical component. Specifically: dual-source LiDAR (LD19 alternate), dual-source mic array (XVF3000 v3.0 alternate already noted), dual-source compute (Orange Pi 5 as Pi 5 alternate, even if performance is worse).

### 6. The design space for "form factor" is unexplored.

You've defaulted to a TurtleBot-shape. ~25cm diameter, diff-drive, 60cm tall implied. This is the worst of all worlds — too big to live on a desk, too small to be useful in a real room, ugly enough that a partner will object to it being on the floor.

The form factor decision is the hardest in consumer hardware. It is not solved by "we picked a chassis kit." It needs explicit thought about: where does the robot live when not in use, how does the user move it, what does the partner think when they walk in, does it fit through doorways, can it climb the threshold to the bathroom.

**Recommendation:** before any parts are ordered, write a one-page form factor doc. Sketch the robot. Mock it up in cardboard at full size. Walk it around your house. The number of products that died at form factor is staggering.

### 7. The 3-use-case scope is right but unprioritized.

You list three flagship use cases. They're not equivalently important. UC1 (find things) competes with AirTags. UC2 (what happened) competes with smart cameras. UC3 (go check) is uncontested.

**Recommendation:** lead with UC3. Build UC3 to bulletproof. Make UC1 and UC2 be by-products of the data UC3 produces.

## What's missing entirely

- **A field test plan.** Who is using this besides you? After how many weeks? In what kind of home? With what failure-reporting mechanism? Without a field test plan, "30 days reliable" is a hope, not a measurement.

- **A failure budget.** What % of skills can fail per week before the user gives up? Real consumer robots target <0.1%. Hobby robots that ship at 5% get binned. Where are you?

- **A user manual.** What do they do when it stops working? When the SD corrupts? When the dock is dirty? Without this, every failure is a project death.

- **A second-user test.** The first home you build for is yours. The second home is the one that surfaces every assumption you didn't know you were making. Plan for it.

- **A teardown spec.** How do you replace the battery in 3 years? What tools? How is the cable harness routed? This is the "Year 3 product survives" decision and it's invisible until you need it.

## My recommendation, blunt

If this is a personal project: build Tier A, ship it for yourself, learn enormously, write it up. The work documented here would let you do that. Skip the rest of this review.

If this is a product seed: pause hardware. Spend two weeks on the product story, the form factor, the field test plan, the COGS model. Then come back to the BOM. The current state of the docs assumes the product question is solved; it isn't.

I'd happily work on this. The team that wrote these docs has the technical chops to ship it. What's missing is a layer above the architecture that decides which 30% of the architecture matters.

Score, if forced: 8/10 as engineering, 4/10 as a product brief, 6/10 average. The gap is product, not engineering. That's a fixable gap.
