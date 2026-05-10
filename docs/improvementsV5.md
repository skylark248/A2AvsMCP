# Presentation Improvement Notes
### Comprehensive review of the PPT built from the markdown

A complete pass covering visual design, content, delivery, and structure. Organized by priority so you can decide what to fix based on time available.

---

## Context & Goal

**Presenter**: Shivansh Choudhary, Senior Software Engineer at Morgan Stanley, Portfolio Accounting Tech division.

**Audience**: Mixed — technical engineers + product/management/leadership from the Portfolio Accounting Tech division at Morgan Stanley.

**Format**: ~1 hour total. 45–50 minutes of presentation + 10–15 minutes of Q&A.

**Topic**: A2A (Agent-to-Agent Protocol), MCP (Model Context Protocol), and Skills — three open standards that solve different integration problems for AI agents.

**Goal of the presentation**:
- Give the audience clarity on what A2A, MCP, and Skills are and what problem each one solves.
- Help them understand **when to reach for which** — the practical "which tool fits which problem?" question.
- Help them visualize how all three concepts compose together in a real production architecture.
- Address the confusion that even after prior sessions, the audience does not have full clarity on MCP, agents, and Skills — A2A is entirely new to them.

**Why each section is weighted the way it is**:
- **A2A is the headline new content** (most slides) — it's the only one of the three that hasn't been covered before.
- **MCP is a recap** (fewer slides) — there have been two prior sessions on MCP, including a hands-on session on building MCP servers with FastAPI in Python.
- **Skills is partly recap, partly clarification** — there was a prior session on Skills, but the audience benefits from clearer "when to use what" framing.

**Recurring example domain**: Generic retail / e-commerce — chosen because it's universally understood and avoids domain-specific finance jargon for a mixed audience. The synthesis section uses retail high-value returns as the worked example.

**Manager feedback that shaped the deck**:
- Breeze through MCP basics since the team had a prior session on it.
- Same for Skills — emphasize *how they're used* and *what's the need* for them, since that's where confusion still lives.
- Earlier feedback also asked to keep the "Why this talk" framing as the opener.

**Prior sessions the audience has attended**:
- MCP basics (architecture, primitives, JSON-RPC, transport layer)
- Building MCP servers with FastAPI in Python
- Skills (format, `.github/skills/<name>/SKILL.md` structure, generic vs pat folders, design principles, progressive disclosure)
- *No prior session on A2A — this is the first introduction.*

**Tone & framing principles for the deck**:
- Respectful of the prior sessions — frame recaps as "you'll recall…" rather than "you've forgotten this."
- Open standards angle (no vendor lock-in) is a recurring credibility thread.
- "Three problems, three standards — complementary, not competing" is the core mental model the audience should leave with.
- The "**when to reach for which**" question is the central thread the deck must answer.

---

## Top Priority — Fix These First

These are the changes most likely to improve audience comprehension and the overall feel of the deck. If you only have time for a handful of edits, do these.

### 1. Split Slide 17 ("Why Skills Exist") into two slides

**Problem**: This slide currently combines two distinct ideas — *why skills exist as a concept* and *the decision tree for when something should be a skill*. Both are heavy. Together they overwhelm.

**Fix**:
- **Slide 17a — Why Skills Exist**: keep the left-side content (LLMs don't know your company's specific procedures, the three pain points, the "Skills solve this by packaging procedures" line). Make this slide breathe.
- **Slide 17b — Decision Tree**: give the decision tree its own slide. Add the "Skill is the right answer when…" / "Skill is the wrong answer when…" content from the original markdown back in. This is the slide that does the most teaching work in the Skills section — it deserves its own real estate.

**Why this matters**: the decision tree is the answer to the central question of the talk ("when do I use what?"). Cramming it onto a busy slide undersells it.

### 2. Increase JSON code font on Slide 8 (Agent Card)

**Problem**: At presentation distance, the JSON code block on Slide 8 is unreadable for anyone past row 3. The four right-side callouts (Identity, Capabilities, Authentication, Discovery) are doing the actual teaching work; the code is illustrative.

**Fix options** (pick one):
- **Option A (preferred)**: Bump the code font size by ~30%, even if it means dropping 2-3 lines from the JSON example. Show only `name`, `description`, `url`, and one skill entry — that's enough to convey "agent card looks like a structured manifest."
- **Option B**: Keep all the JSON but increase contrast (lighter background, darker text, or vice versa).
- **Option C**: Replace the literal JSON with a simplified pseudo-structure with friendlier formatting.

### 3. Tighten Slide 9 (How A2A Works: Communication)

**Problem**: Four boxes on the left + a multi-bullet "Why this matters" callout on the right makes the slide feel cramped. The "Modality-Agnostic" box is the weakest of the four — it's a *consequence* of the format, not a peer concept.

**Fix**: Remove the "Modality-Agnostic" box. Fold one line about it into the Format box ("Format — JSON-RPC 2.0 (text, images, files all in the same flow)") or drop it entirely. This gives the right-side "Why this matters" callout room to breathe.

---

## High Priority — Visual Design Improvements

### 4. Slide 1 (Agenda) — Strengthen section labels

**Observations**:
- The numerals (1, 2, 3, 4) are clean and visually strong.
- However, the descriptions under each numeral are slightly small for back-row readability.
- "A2A Protocol", "MCP Protocol", "Skills", "Composing All Three" are doing all the work — the descriptions could be lighter.

**Improvements**:
- Bold the section headings ("A2A Protocol" etc.) so they're the visual anchor.
- Consider adding part labels above each number: "Part 1: A2A Protocol", "Part 2: MCP Protocol" etc. This sets up the expectation that A2A is the biggest section.
- Optional: add an estimated time per section ("~15 min", "~7 min", etc.) so the audience knows where the talk is weighted.

### 5. Slide 2 (Why This Talk) — Strong as-is, minor tweak

**Observations**:
- Three-column layout with "Talk to other agents / Talk to your systems / Know how to do the actual work" is great.
- "By the end of this talk:" bullet list at the bottom is the strongest part of the slide for setting expectations.

**Optional improvement**:
- Bold the three "when to reach for which" / "what each one is" / "how all three compose" phrases — these are the value prop.

### 6. Slide 3 (Quick Vocabulary: 4 Things That Look Similar) — Acknowledge density

**Observations**:
- This is the densest slide in the deck — 4-row comparison table + 3-box analogy section below.
- Mixed audiences may glaze over here.

**Improvements**:
- Consider visually separating the table from the analogy with a horizontal line or different background tone for the analogy section — it's a different kind of content.
- Bold "**The agent decides**" in the Skill row of the table — it's the key distinction that pays off later in the Skills section.
- During delivery, plan to walk through this slide slowly. Don't try to rush past it.
- Optional: Move the analogy *above* the table. People grasp the analogy faster than the formal comparison; leading with the SOP-binder image makes the table easier to parse.

### 7. Slide 5 (Three Problems, Three Standards) — Strengthen the protocol callouts

**Observations**:
- Icons (people, plug, book) are good but could be larger.
- "→ A2A Protocol", "→ MCP Protocol", "→ Skills" at the bottom of each column reads as small text rather than as the punchline.

**Improvements**:
- Increase the protocol name font size — they should be the visual punchline of each column.
- Make the arrows visually heavier (thicker, or replace with a chunkier arrow glyph).
- Consider color-coding each column (e.g., the same colors you use later in Slide 22's "Which Piece" column) so visual continuity carries through the deck.

### 8. Slide 6 (Why A2A Exists) — Looks good, minor copy edit

**Observations**:
- Three-team scenario lands well.
- "Today's answer / A2A's job" framing is clean.

**Improvements**:
- "A2A's job" is highlighted with bold — good. Consider also bolding "**discover each other and coordinate**" within that sentence; that's the actual functional definition of A2A.

### 9. Slide 7 (Agent Card) — JSON readability (covered in Top Priority #2)

See above.

### 10. Slide 8 (A2A vs MCP) — Excellent, very minor tweak

**Observations**:
- This is one of the best slides in the deck. Clean comparison table with the punchline at the bottom.
- "MCP is for capability. A2A is for collaboration." is the one-liner the audience will remember.

**Improvements**:
- Bold "capability" and "collaboration" in the bottom callout (they may already be — hard to tell from photo).
- Consider adding row-stripe coloring (alternating very light gray) to make it easier to track across columns.

### 11. Slide 11 (A2A in Action: Order Fulfillment) — Strong, copy edit

**Observations**:
- Five-step horizontal flow is exactly right for showing a process.
- Icons are clear and distinguishable.

**Improvements**:
- "Suppliers stream" in Step 4 — replace with "Suppliers respond (streaming)" or "Suppliers send quotes". The word "stream" alone is jargon-y for management folks.
- Consider adding "(SSE)" in parentheses in Step 4 if you want to remind the technical audience about the streaming protocol — but this can also be discussed in delivery rather than shown.

### 12. Slide 12 (Is A2A Real?) — Good, content tightening

**Observations**:
- Bullet structure works well.
- "For us" callout on the right is the slide's centerpiece.

**Improvements**:
- "Originally introduced by Google" with sub-bullet "Launched in 2025 as an open specification" feels redundant. Consider merging into one line: "Originally introduced by Google in 2025 as an open specification."
- Consider adding one more concrete signal — e.g., "Multiple major vendors shipping A2A-compatible products" — if you can verify this. Helps the "is it real?" case.
- "Early signal: the same vendors adopting MCP are now adding A2A support." — this is a strong line. Make sure it's bold or visually emphasized in the callout box.

### 13. Slide 14 (MCP Recap) — Re-anchor to the prior session

**Observations**:
- Four icons (Architecture, Primitives, Transport, Framework-agnostic) work well visually.
- However, "Framework-agnostic" is more of a *benefit* than a peer-level concept like the other three.

**Improvements**:
- Replace "Framework-agnostic" with "**Hands-on**: built one with FastAPI in our prior session" — this explicitly recalls the previous session and reinforces "we've already done this together." Helps the recap framing land.
- Alternatively, replace with "**Open ecosystem**: GitHub, Slack, Postgres servers ready to use" if you want to convey that there's lots of pre-built MCP servers.
- Make sure the "Key point: MCP servers are passive…" callout is visually emphasized — that line is the seed for the A2A vs MCP distinction.

### 14. Slide 15 (MCP in Action: Customer Support) — Excellent, no changes

**Observations**:
- Clean four-server walkthrough with icons.
- "Four backend systems. Zero custom integration code in the agent itself" is the right takeaway.

**Improvements**:
- None. This slide is doing its job.

### 15. Slide 18 (Skills vs MCP vs RAG) — Good, minor improvement

**Observations**:
- Toolbox / Reference Manual / SOP analogy lands cleanly.
- Three-column layout is consistent with the deck's rhythm.

**Improvements**:
- The example quotes in italics ("I can call create_refund on the API", "Our return policy says 30 days", "For returns over $10K…") are the most useful part of this slide. Make them slightly larger or visually distinguished from the descriptions above them.
- Consider adding a fourth column for fine-tuning if your audience might confuse it with these — but only if you have space. Otherwise it's fine to handle fine-tuning on the cheat sheet at the end.

### 16. Slide 19 (Skills in Action: Concrete Examples) — Decongest

**Observations**:
- Top scenarios table is good.
- Bottom section ("When a Skill is the wrong answer" + "A skill in plain form") is cramped.

**Improvements**:
- The YAML snippet at the bottom is hard to read. Either move it to its own slide (probably too much) or significantly enlarge it.
- Consider whether the "When a Skill is the wrong answer" four boxes are actually needed here, since the same content appears in the decision tree on Slide 17. If so, drop them — they're duplicative.
- Removing the "wrong answer" boxes would give the YAML snippet room to breathe at a readable size.

### 17. Slide 21 (The Big Picture) — Tone down color saturation

**Observations**:
- Three colored bands (blue / green / purple) for the three agents are striking.
- However, the saturation is high enough that the color *itself* draws the eye before the labels do.

**Improvements**:
- Reduce the band colors to ~30% opacity / lighter tints. The labels (Customer Support Agent, Inventory Agent, Supplier Agent) should be the visual focus, not the band color.
- The "↕ A2A" labels between agents are good but could be slightly larger.
- The bottom row ("A2A = how agents coordinate with peers" etc.) is the visual recap — make sure it's anchored visually with a different background tint or a separator line above it.

### 18. Slide 22 (End-to-End: All Three Pieces) — Excellent, don't change

**Observations**:
- Single-table walkthrough with the "Which Piece" column color-coded — exactly right.
- Six rows is the right length, neither too few nor too many.
- "One agent, one skill, several MCP tools, one A2A peer" is a memorable closing line.

**Improvements**:
- Verify the color coding in the "Which Piece" column matches the colors used on Slide 21 (Big Picture). If they don't match, fix that — visual continuity matters here.
- Consider bolding "Step 3" since it's the only A2A step among five MCP steps — it's the moment when A2A enters the workflow. Drawing the eye there reinforces the synthesis.

### 19. Slide 23 (Decision Cheat Sheet) — Hard to assess from photo

The slide is angled in the photo. From what I can read:

**Observations**:
- Good two-column structure (If You Need / Reach For).
- Six rows seems right.
- Common production pattern callout at the bottom.

**Improvements (assuming the layout is what I think it is)**:
- Bold the "Reach For" column entries — they should be visually stronger than the descriptions on the left.
- Verify each row has exactly *one* answer in the "Reach For" column. If any have multiple, split them into separate rows.
- This is the "photograph this slide" moment. Consider adding a small visual cue like a camera icon or a "Save this" tag to encourage people to actually capture it.

### 20. Slide 24 (What This Means For Our Team) — Strong, minor edits

**Observations**:
- Three numbered points + one closing line is the right structure.
- "MCP servers are our integration leverage" is the right opener — leads with the most concrete takeaway.

**Improvements**:
- Bold the lead-in phrases ("MCP servers are our integration leverage", "Skills encode our institutional knowledge", "A2A is the bet for the next 12 months") — they're the takeaways.
- The "All three are open standards" closing line is doing important work but is visually de-emphasized. Consider boxing it or making it the same visual weight as the three numbered points.

### 21. Slide 25 (Discussion / Q&A) — Strong as-is

**Observations**:
- Blue background contrasts with the white slides preceding it — good signal that we've shifted modes.
- Four discussion prompts is the right number.

**Improvements**:
- None. Strong closing slide.
- Optional: add your name and contact info for follow-up questions.

---

## Medium Priority — Content & Copy Polish

### 22. Add slide numbers visibly

**Observation**: Slide numbers are present in the footer but small.

**Improvement**: Make them slightly more visible. During Q&A, attendees often refer to slides by number, and it's frustrating when nobody can read the slide number from the back.

### 23. "Confidential / Not for External Use — Do Not Forward" footer is consistent

**Observation**: Good, this is consistent across all slides. No change needed.

### 24. Consider a "section divider" slide between Parts

**Observation**: Currently the parts (A2A, MCP, Skills, Synthesis) flow without explicit dividers. This is fine, but for a 50-minute presentation, a one-second visual reset between sections helps the audience reorient.

**Improvement**: Optional — add a quarter-slide-style divider before each Part transition. Just the part name and number on a contrasting background. Three extra slides total. Don't add this if you're already at slide budget.

### 25. Standardize bold usage

**Observation**: Some slides bold key phrases liberally; others sparingly.

**Improvement**: Pass through the deck once with one rule: bold *only* the specific phrase that captures the slide's takeaway. Two-three bold phrases per slide max. Over-bolding makes nothing stand out.

### 26. Code blocks — consider a consistent visual style

**Observation**: Slide 8 (Agent Card JSON) and Slide 19 (Skill YAML) both have code blocks but they look slightly different in styling.

**Improvement**: Use the same code block visual style — same font, same background, same padding — across all code samples. Tiny detail, but it makes the deck feel more polished.

### 27. Icon consistency

**Observation**: Icons are used consistently (people for agents, plug for tools, book for procedures) — this is good.

**Improvement**: Verify the same icon represents the same concept across slides. Specifically, the "Agent" representation on Slide 5 should match the "Agent" representation on Slide 21. If they're already the same, ignore this.

---

## Lower Priority — Delivery Considerations (not slide changes)

These aren't slide fixes, but observations to keep in mind when presenting.

### 28. Slide 3 (Quick Vocabulary) is the eye-glaze risk

This is the densest content slide. Plan to:
- Walk through one row at a time, not all four at once.
- Use the analogy section (handbook / form / SOP binder) as your primary explainer; refer back to the table to anchor each.
- Spend ~3 minutes on this slide rather than rushing.

### 29. Slide 8 (A2A vs MCP) is the comprehension pivot

This is where confusion either dies or amplifies. Plan to:
- Read the bottom one-liner ("MCP is for capability. A2A is for collaboration.") *twice* — once entering the slide, once leaving it.
- Pause after this slide before moving on. Take questions if needed.

### 30. Slide 17 (decision tree) needs delivery practice

If you split this into two slides as recommended:
- The decision tree can feel mechanical when delivered. Practice walking through it conversationally — "okay, is this used every interaction? No, only when X happens. So is it manually invoked? No, the agent decides. So that's a skill."
- Don't read the tree. Walk through one example each time.

### 31. Slide 22 (End-to-End) is the synthesis moment

This is the slide that makes everything click. Plan to:
- Spend 4-5 minutes on this slide.
- Walk through each step out loud, naming which protocol/concept is firing.
- Land hard on the closing line: "One agent, one skill, several MCP tools, one A2A peer."

### 32. Q&A prep

Anticipate questions:
- "Is anyone at Morgan Stanley actually using A2A yet?" — be ready with a candid answer.
- "How is this different from microservices?" — A2A peers are AI agents that reason; microservices follow deterministic logic.
- "Why not just use REST APIs between agents?" — you could, but agent cards + A2A give you discovery and standardized task semantics that REST doesn't.
- "Won't this proliferate complexity?" — yes, if used badly. The cheat sheet on Slide 23 is the antidote.

---

## Structural Observations About the Deck Overall

### 33. The Skills section lacks an "in action" walkthrough comparable to A2A and MCP

**Observation**: A2A has Slide 11 (Order Fulfillment walkthrough). MCP has Slide 15 (Customer Support walkthrough). Skills has Slide 19, but it's a list of scenarios + a YAML snippet — not a walkthrough.

**Possible fix**: Either accept this asymmetry (Skills will land slightly more abstractly), or add a sixth "in action" slide showing a skill *executing* — e.g., a high-value return scenario walked through step by step. The end-to-end slide (22) sort of covers this but is positioned as a synthesis.

This is a real choice, not a clear-cut error. Mention this to your audience during delivery: "You'll notice the Skills section has fewer concrete walkthroughs — that's because skills are best understood in the context of a full system, which we'll see in the synthesis."

### 34. The deck weighting is right

**Observation**: A2A gets 6 slides, MCP gets 2, Skills gets 4, synthesis gets 4. This matches your stated goal (A2A is the new content; MCP/Skills are recaps).

**No change needed** — the weighting is appropriate.

### 35. The retail example threading works

**Observation**: Order Fulfillment for A2A, Customer Support for MCP, High-Value Return for Skills — all retail. The synthesis on Slide 22 also uses Returns. Consistent worldbuilding.

**No change needed** — this is a strength.

### 36. Consider whether to mention RAG more prominently

**Observation**: RAG appears on Slide 18 (mental model) and Slide 23 (cheat sheet) but isn't given its own dedicated treatment.

**Decision**: This is correct. RAG isn't the focus of this talk. But be ready in Q&A — someone will ask "what about RAG?" and you should have a clean 30-second answer.

---

## Summary: The Three Changes That Matter Most

If you make only three changes:

1. **Split Slide 17 into two slides** — Why Skills Exist + Decision Tree get their own real estate.
2. **Make the JSON code on Slide 8 readable from the back row** — bigger font, even if it means showing fewer fields.
3. **Tighten Slide 9** — drop the Modality-Agnostic box so the rest can breathe.

If you have more time:

4. Polish Slide 17b (the decision tree) with the "right answer when / wrong answer when" framing from the original markdown.
5. Reduce color saturation on Slide 21's three-band diagram.
6. Re-anchor Slide 14's fourth icon to your prior FastAPI session.
7. Bold takeaway phrases consistently across all slides — one rule, applied uniformly.

Everything else is polish.

---

*The deck is in good shape overall. These are improvements, not rescues. The structure, examples, and visual rhythm are all working — what's left is fine-tuning.*