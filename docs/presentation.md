# A2A, MCP & Skills
### The Three Pieces That Make AI Agents Actually Useful

*A walkthrough of how modern AI agents talk to each other, talk to your systems, and learn to do real work. ~50 minutes + Q&A.*

---

## Slide 1 — Why This Talk

AI agents on their own are isolated. They can reason. They can generate text. They can make decisions. But in the real world, an agent needs to:

1. **Talk to other agents** (that someone else built, in a different framework)
2. **Talk to your systems** (databases, APIs, file systems, internal tools)
3. **Know how to do the actual work** your business cares about

Three different problems. Three different standards have emerged to solve them: **A2A, MCP, and Skills**.

By the end of this talk:
- You'll know what each one is and what problem it solves
- You'll know **when to reach for which** — the question that matters most in practice
- You'll see how all three compose together in a real architecture

---

## Slide 2 — Quick Vocabulary: 4 Things That Look Similar

Anyone using Claude Code or GitHub Copilot has seen `prompt.md`, `instructions.md`, and `SKILL.md` files. They look similar — they do different things. The key axis is **who decides when this content is loaded**.

| | What it is | Who triggers it | When it loads |
|---|---|---|---|
| **Prompt file** (`.github/prompts/refactor.prompt.md`) | A reusable, manually invoked template | User invokes `/refactor` | Only when called |
| **Instruction file** (`CLAUDE.md`, `copilot-instructions.md`) | Always-on context for the project | Nobody — it's always on | Every turn |
| **Skill** (`SKILL.md` in a folder) | Conditionally loaded "how-to" | The agent itself, based on the task | Only when relevant |
| **Agent** | The running thing that takes actions | — | — |

**Quick analogy** — if the agent is an employee:
- **Instruction file** = the employee handbook they always follow
- **Prompt file** = a form they fill in when *you* hand it to them
- **Skill** = the SOP binder they pull off the shelf themselves when they recognize the situation

This vocabulary will matter when we discuss Skills later.

---

## Slide 3 — The Three Problems, The Three Standards

An AI agent in production has three distinct integration problems. Different problem, different solution:

| Problem | Solution |
|---|---|
| **Agent ↔ Agent** — How does my agent coordinate with one built by another team or vendor? | **A2A** (Agent-to-Agent Protocol) |
| **Agent ↔ Tools & Data** — How does my agent reach databases, APIs, internal systems? | **MCP** (Model Context Protocol) |
| **Agent ↔ Procedures** — How does my agent know our specific way of doing things? | **Skills** |

These are **complementary, not competing**. A real production agent typically uses all three.

Today: A2A is the new piece worth our time. MCP and Skills will be quick refreshers — we covered them before — but with a sharper focus on *when to use them*.

---

# Part 1: A2A — Agents Talking to Agents

---

## Slide 4 — Why A2A Exists

Imagine our retail company has built three agents over the past year:

- An **Inventory Agent** built by the supply chain team in Python
- A **Pricing Agent** built by the analytics team using a different framework
- A **Customer Support Agent** from a vendor, running as SaaS

Each works fine on its own. But what about:
- Inventory drops below threshold → pricing needs adjusting?
- A customer complaint requires checking inventory *and* recent pricing changes?

Today's answer: a developer writes glue code. Custom integration. Brittle. Has to be rewritten every time any agent changes.

**A2A's job**: give agents a standard way to discover each other and coordinate — regardless of who built them or what framework they use.

---

## Slide 5 — How A2A Works: The Agent Card

Every A2A-compatible agent publishes an **agent card** — a digital business card at a known URL.

It says: who I am, what I can do, how to reach me. Other agents read it and figure out, *"Oh, the Pricing Agent can adjust prices given a SKU and a discount — I'll send my request there."*

A simplified agent card looks like this:

```json
{
  "name": "Pricing Agent",
  "description": "Adjusts product prices based on inventory and demand signals",
  "url": "https://internal.example.com/agents/pricing",
  "skills": [
    {
      "id": "adjust-price",
      "description": "Given a SKU and discount %, updates the price",
      "input_modes": ["application/json"]
    }
  ],
  "authentication": { "schemes": ["oauth2"] }
}
```

Think of it as a **resume**. Other agents read it before deciding to collaborate. No hard-coded integrations.

---

## Slide 6 — How A2A Works: The Communication

Built on familiar web technology — there's deliberately no new transport here:

- **Transport**: plain HTTP (any web server, API gateway, or load balancer can host an A2A agent)
- **Format**: JSON-RPC 2.0 — same data layer MCP uses
- **Long-running tasks**: Server-Sent Events (SSE) for streaming progress updates

Why this matters: agents get all the benefits of existing web infrastructure for free — routing, security, logging, monitoring, auth.

**Modality-agnostic**: agents can exchange text, images, files, structured data. One agent generates a design mockup, another reviews it, a third routes it for approval — all in the same flow.

---

## Slide 7 — A2A vs MCP: The Confusion-Buster

Both A2A and MCP use JSON-RPC 2.0. Both run over HTTP. So what's actually different? This is the most common point of confusion — let's name it directly.

| | **MCP** | **A2A** |
|---|---|---|
| **Connects** | One agent ↔ tools and data | Agent ↔ another agent |
| **Other side is** | A passive server exposing tools | Another *active reasoner* with its own goals |
| **Interaction** | Call a function, get a result | Send a task, possibly negotiate, get streaming progress |
| **Mental model** | The toolbox the agent reaches into | The peer the agent talks to |
| **Discovery** | You configure which MCP servers your agent uses | Agents discover each other via agent cards |

**One-line distinction**: **MCP is for capability. A2A is for collaboration.**

A database wrapped as an MCP server is passive — it answers when called. A pricing agent reached over A2A is active — it can push back, negotiate, stream partial results, ask clarifying questions.

---

## Slide 8 — A2A in Action: Retail Order Fulfillment

A high-value order comes in for 50 units of an electronics SKU. Walk through the flow:

1. **Order Agent** asks the **Inventory Agent**: *"Do we have 50 units of SKU-9821?"*
2. **Inventory Agent**: *"Only 12 in our warehouse. 38 short."*
3. **Order Agent** reaches out to two **Supplier Agents** (different vendors, different tech stacks): *"Can you fulfill 38 units, when, and at what price?"*
4. **Supplier Agents** stream back quotes via SSE as they're calculated.
5. **Order Agent** picks the best, confirms, notifies the **Customer Notification Agent**.

**No human glue code.** Five agents, multiple companies, different tech stacks — all coordinating through one protocol they all understand.

---

## Slide 9 — Is A2A Real? Should We Bet On It?

Quick state of the world (the "is this hype?" question):

- **Originally introduced by Google** in 2025 as an open specification
- **Open protocol, not vendor-locked** — same trajectory as MCP (started at Anthropic, now industry-wide)
- **Vendor SDKs** available in Python, JavaScript, Java, .NET
- **Compatible with major agent frameworks** — works alongside LangChain, Semantic Kernel, custom agents, MCP-based agents

**For us**: not yet ubiquitous, but clearly heading toward standard. Worth knowing now so we're not surprised when it shows up in vendor product roadmaps or on our own architecture diagrams.

---

# Part 2: MCP — Quick Recap

*You've seen this before. One slide of refresh, one slide of "what it looks like in practice."*

---

## Slide 10 — MCP Recap

**The one-line refresher**: MCP is a standard interface that lets an agent reach tools and data — without rewriting integrations every time you swap a model or framework.

What you've already seen:
- **Architecture**: Host (the AI app) + Client + Server, communicating in JSON-RPC 2.0
- **Primitives**: Tools (actions the agent can take), Resources (data the agent can read), Prompts (templates)
- **Transport**: STDIO for local servers, HTTP/SSE for remote
- **Hands-on**: building an MCP server using FastAPI in Python

**The one thing worth re-emphasizing today** (because it'll come up later): **MCP servers are passive**. They expose capability. They don't reason or plan or negotiate. That's what distinguishes them from A2A peers.

---

## Slide 11 — MCP in Action: Retail Customer Support

A customer writes: *"I want to return the headphones I ordered last month, but I lost the order number."*

Behind the scenes, the support agent uses MCP to:

1. **CRM MCP server** → look up the customer by email, pull recent orders
2. **Returns MCP server** → check eligibility for the matching order
3. **Logistics MCP server** → generate the return label
4. **Email MCP server** → send the label to the customer

Four backend systems. Zero custom integration code in the agent itself. **That's the MCP value prop in one slide.**

---

# Part 3: Skills — The Procedures

---

## Slide 12 — Why Skills Exist

LLMs are excellent reasoners. They know a lot. What they *don't* know is **how your company specifically does things**:

- The exact steps for handling a high-value return
- How your firm reconciles inventory across regional warehouses on month-end
- The compliance checks that must run before issuing a refund over $10,000

Without skills, you have two bad options:

1. **Stuff everything into the system prompt / instruction file** → bloats context for every interaction, even when most of it isn't relevant
2. **Re-explain the procedure every time** → the user becomes the SOP document. Doesn't scale.

**Skills solve this** by packaging procedures into files the agent loads only when the task calls for them.

---

## Slide 13 — When Is It a Skill? (The Decision That Matters)

This is where most teams get confused. Three nearby concepts — instructions, prompts, skills. Walk through this decision tree:

```
Is the content used every interaction?
  └─ YES → Instruction file (always-on context)
  └─ NO ↓

Does the user explicitly invoke it each time?
  └─ YES → Prompt file (user-triggered template)
  └─ NO ↓

Should the agent decide on its own when to use it,
based on the task at hand?
  └─ YES → Skill ✓
```

**Skill is the right answer when**:
- The procedure has *specific steps* that must run in order
- It applies to a *category* of tasks, not every task
- The agent should recognize when it applies, not wait to be told

**Skill is the *wrong* answer when**:
- It's a general behavior rule ("always use TypeScript strict mode") → instruction
- It's a one-off transformation triggered manually → prompt
- It's pure factual lookup with no procedure → that's RAG
- It's a tool capability ("I can call this API") → that's MCP

---

## Slide 14 — Skills vs MCP vs RAG: The Mental Model

The most useful frame: **toolbox / reference manual / SOP**.

| Method | What it provides | Retail example |
|---|---|---|
| **MCP** | The *capability* — the tools | "I can call `create_refund` on the API" |
| **RAG** | The *facts* — the reference manual | "Our return policy says 30 days" |
| **Skills** | The *procedure* — the SOP binder | "For returns over $10K: check eligibility → manager approval → compliance log → refund → email customer" |

A real skill almost always *uses* MCP tools (to act) and may *reference* RAG-retrieved policies (to decide). The skill is the **orchestration layer** — *when* and *in what order*.

**Mental model**: MCP is the toolbox. RAG is the reference manual. Skills are the SOP that tells the worker which tool to pick up and which page of the manual to read first.

---

## Slide 15 — Skills in Action: Concrete Examples

Some scenarios where a skill is the right answer:

| Scenario | Why a skill fits |
|---|---|
| Quarterly inventory reconciliation across warehouses | Same procedure quarterly. Specific steps, specific report format. |
| New vendor onboarding (KYC, document collection, approvals) | Multi-step, has rules, repeats often. |
| Handling a high-value return that needs compliance routing | Decision tree the agent should follow, not invent. |
| Generating a regulatory filing using a standard template | Specific format requirements. The agent should not improvise. |

**A skill in plain form** — `high-value-return`:

```yaml
---
name: high-value-return
description: Use when a customer requests a return for an order over $10,000.
              Handles compliance checks, manager approval routing, refund processing.
---
```

The body contains the actual steps. The agent loads this skill *only* when the description matches — high-value return scenarios. The other 99% of conversations don't pay the cost.

---

# Part 4: Putting It All Together

---

## Slide 16 — The Big Picture

How the three compose in a real system:

```
        ┌────────────────────────────────────────────────────┐
        │  Customer Support Agent                            │
        │   • Skills: handle-return, escalate-complaint      │
        │   • MCP: CRM, orders DB, email, returns API        │
        └────────────────────────────────────────────────────┘
                              ↕  A2A
        ┌────────────────────────────────────────────────────┐
        │  Inventory Agent (different team)                  │
        │   • Skills: quarterly-reconciliation, low-stock    │
        │   • MCP: inventory DB, warehouse system            │
        └────────────────────────────────────────────────────┘
                              ↕  A2A
        ┌────────────────────────────────────────────────────┐
        │  Supplier Agent (external)                         │
        └────────────────────────────────────────────────────┘
```

Three layers, three roles:

- **A2A** = how agents coordinate with peers (horizontal arrows)
- **MCP** = how each agent reaches its tools and data (into the agent)
- **Skills** = the procedural knowledge each agent uses to do work (inside the agent)

This is the architecture diagram you want to be able to draw on a whiteboard.

---

## Slide 17 — How They Work Together: One Scenario, End to End

A high-value return request comes in. Watch all three pieces fire:

| Step | What happens | Which piece |
|---|---|---|
| 1 | Customer message arrives. Agent recognizes "return over $10K" → loads `handle-high-value-return` skill | **Skill** |
| 2 | Skill says: pull customer + order details. Agent calls CRM and orders MCP servers. | **MCP** |
| 3 | Skill says: check inventory before approving refund. Agent calls **Inventory Agent** for current stock context. | **A2A** |
| 4 | Skill says: route for manager approval. Agent calls approval MCP server. | **MCP** |
| 5 | Skill says: log to compliance. Agent calls audit MCP server. | **MCP** |
| 6 | Skill says: notify customer. Agent calls email MCP server. | **MCP** |

**One agent, one skill, several MCP tools, one A2A peer.** That's the shape of a real production agent workflow.

---

## Slide 18 — When To Use What: Decision Cheat Sheet

The slide to photograph.

| If you need… | Reach for… |
|---|---|
| Two or more agents to coordinate, possibly across teams or vendors | **A2A** |
| An agent to read/write data, call APIs, touch the file system | **MCP** |
| An agent to follow a specific multi-step procedure | **Skills** |
| The agent to know a fact ("what's our cutoff time?") | **RAG** |
| Always-on behavior rules ("respond formally", "use TypeScript") | **Instruction file** |
| User-invoked reusable templates (`/refactor`, `/explain-bug`) | **Prompt file** |

A common pattern in production: **multiple of these at once**. A2A for coordination, MCP for capability, Skills for know-how, instruction files for project-wide rules.

---

## Slide 19 — What This Means For Our Team

Three takeaways for Portfolio Accounting Tech:

1. **MCP servers are our integration leverage.** Every internal system we wrap as an MCP server (position DB, ledger, trade store, regulatory reporting) becomes available to *every* future agent we build. Write once, reuse forever.

2. **Skills are how we encode our institutional knowledge.** The procedures our team has refined over years — month-end recon, position break investigation, regulatory filing prep — are exactly what skills are for. Reviewable, version-controlled, reusable across agents.

3. **A2A is the bet for the next 12 months.** As more teams across the firm build agents, A2A is what lets them compose without us writing custom integration code per pair. Worth tracking even before we adopt it.

The good news: all three are open standards. What we build today carries forward.

---

## Slide 20 — Discussion / Q&A

Some prompts to kick things off:

- Where in our current systems would A2A reduce custom integration code?
- Which of our internal systems would benefit most from being wrapped as an MCP server?
- What internal procedures (the boring, repeatable kind) would make good first skills?
- Where do you see the biggest risk or skepticism in adopting any of this?

*Open floor.*

---

*Thank you.*