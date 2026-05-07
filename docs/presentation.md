# A2A, MCP & Skills
### The Three Pieces That Make AI Agents Actually Useful

*A walkthrough of how modern AI agents talk to each other, talk to your systems, and learn to do real work.*

---

## Slide 1 — Why This Talk

AI agents on their own are isolated. They can reason, they can generate text, they can make decisions — but in the real world, an agent needs to:

1. **Talk to other agents** (that someone else built, in a different framework)
2. **Talk to your systems** (databases, APIs, file systems, internal tools)
3. **Know how to do the actual work** your business cares about

Three different problems. Three different protocols / standards have emerged to solve them:

| Problem | Solution |
|---|---|
| Agent ↔ Agent communication | **A2A** (Agent-to-Agent Protocol) |
| Agent ↔ Tools and data | **MCP** (Model Context Protocol) |
| Agent ↔ Knowing how to do things | **Skills** |

By the end of this talk, you'll know what each one is, when to use which, and how they fit together.

---

## Slide 2 — A Quick Detour: Skill vs Prompt File vs Instruction File vs Agent

Before we go deep, a clarification — because anyone using Claude Code or GitHub Copilot has probably seen `prompt.md`, `instructions.md`, and now `SKILL.md` files, and they all look similar but do different things.

- **Prompt file** (e.g., `.github/prompts/refactor.prompt.md`) — a reusable, *manually invoked* template. The user types `/refactor` or picks it from a menu, and the file's contents get injected as the prompt. Always you-triggered.
- **Instruction file** (e.g., `CLAUDE.md`, `.github/copilot-instructions.md`) — context that's *always loaded* for every interaction in that project. "Use TypeScript strict mode. Our codebase uses pnpm, not npm." Applies to everything.
- **Skill** (`SKILL.md` in a folder) — *conditionally loaded* by the agent itself based on the task. The agent reads the description, decides this skill applies, then pulls in the body. Agent-triggered, not user-triggered.
- **Agent** — the running thing. The brain + tools + skills + instructions that takes actions.

**The key axis is *who decides when this content is used*:**

| | Who triggers it | When it loads |
|---|---|---|
| Prompt file | User (manually invokes it) | Only when called |
| Instruction file | Nobody — it's always on | Every turn |
| Skill | The agent (based on description match) | Only when relevant |

**Quick analogy**: If the agent is an employee, then:
- The instruction file is the employee handbook they always follow.
- A prompt file is a form they fill in when *you* hand it to them.
- A skill is the SOP binder they pull off the shelf themselves when they recognize the situation.

The progressive disclosure trick (which we'll cover on Slide 13) is what makes skills different from just dumping everything into the instruction file — you can have hundreds of skills without bloating context.

We'll come back to skills in detail later — for now, just know they're agent-triggered, not user-triggered.

---

# Part 1: A2A — Agents Talking to Agents

---

## Slide 3 — The Problem A2A Solves

Imagine our retail company has built three agents over the past year:

- An **Inventory Agent** built by the supply chain team in Python
- A **Pricing Agent** built by the analytics team using a different framework
- A **Customer Support Agent** built by a vendor as a SaaS product

Each agent works fine in isolation. But what happens when:
- Inventory drops below a threshold and pricing needs to be adjusted?
- A customer complaint requires checking inventory *and* recent pricing changes?

Today, the answer is usually: a developer writes glue code. Custom integration. Brittle. One-off. Has to be rewritten when any agent changes.

**A2A's job**: give agents a standard way to discover each other and talk — regardless of who built them or what framework they use.

---

## Slide 4 — How A2A Works: The Agent Card

Every A2A-compatible agent publishes an **agent card** — basically a digital business card.

It says:
- Who I am
- What I can do (skills/services I offer)
- How to reach me

Other agents can discover these cards and figure out, "Oh, the Pricing Agent can adjust prices given a SKU and a discount percentage — I'll send my request there."

Think of it as a **resume** that agents read about each other before deciding to collaborate.

---

## Slide 5 — How A2A Works: The Communication

Under the hood, A2A is built on familiar web technology:

- **Transport**: plain HTTP (any web server, API gateway, or load balancer can host an A2A agent)
- **Format**: JSON-RPC 2.0 (structured, language-agnostic messages)
- **Long-running tasks**: Server-Sent Events (SSE) for streaming progress updates

Why this matters: you get all the benefits of existing web infrastructure for free — routing, security, logging, monitoring, rate limiting.

**Modality-agnostic**: agents can exchange text, images, files, structured data. One agent generates a design mockup, another reviews it, a third gets client approval — all in the same flow.

---

## Slide 6 — A2A in Action: Retail Order Fulfillment

Picture an order coming in for a high-value electronics product:

1. **Order Agent** receives the order and asks the Inventory Agent: "Do we have 50 units of SKU-9821?"
2. **Inventory Agent** responds: "Only 12 in our warehouse. 38 short."
3. **Order Agent** reaches out to two **Supplier Agents** (different vendors, different companies, different tech stacks): "Can you fulfill 38 units, when, and at what price?"
4. **Supplier Agents** stream back quotes as they're calculated.
5. **Order Agent** picks the best, confirms, and notifies the **Customer Notification Agent**.

No human glue code. The agents discovered each other, exchanged structured messages, and coordinated — across company boundaries.

---

# Part 2: MCP — Agents Talking to Tools and Data

---

## Slide 7 — The Problem MCP Solves

A2A handled agent-to-agent. But what does a single agent do when it needs to:

- Read a product catalog from a database?
- Pull a customer's order history?
- Update a record in the CRM?
- Read or write files?

The naive answer: write custom code for each integration. The problem: you rewrite that code every time you change the model, swap the framework, or add a new tool.

**MCP's job**: give agents a *standard interface* to reach tools, data, and external systems — write the integration once, reuse it everywhere.

---

## Slide 8 — How MCP Works: Host, Server, Primitives

The architecture has two main pieces:

- **MCP Host** — the AI application where the agent runs (your chatbot, your IDE plugin, your internal tool)
- **MCP Server** — knows how to talk to a specific resource (a database, GitHub, Slack, the file system)

The server exposes three kinds of "primitives" the agent can use:

| Primitive | What it is | Retail example |
|---|---|---|
| **Tools** | Functions the agent can invoke | `search_products`, `update_inventory`, `create_refund` |
| **Resources** | Data the agent can read | Product catalog, order history, current stock levels |
| **Prompts** | Pre-built templates | "Generate a return-reason summary using this format…" |

The agent doesn't need to know that the inventory lives in PostgreSQL or that orders are in MongoDB. It just calls `update_inventory(...)` and the MCP server handles the translation.

---

## Slide 9 — How MCP Works: Transport

Same JSON-RPC format A2A uses, but the transport depends on where the server runs:

- **Local server** (e.g., an IDE plugin reading your local files) → standard input/output
- **Remote server** (e.g., a hosted CRM connector) → HTTP with streaming

The big win: **MCP servers are reusable**. Write one MCP server for your CRM once, and any MCP-compatible agent — built by anyone, using any model — can use it.

There's already a growing ecosystem of pre-built MCP servers for GitHub, Slack, Google Drive, Postgres, Stripe, and many more.

---

## Slide 10 — MCP in Action: Customer Support Agent

A customer writes in: *"I want to return the headphones I ordered last month, but I lost the order number."*

Behind the scenes, the support agent uses MCP to:

1. Call the **CRM MCP server** → tool: `find_customer_by_email`
2. Call the same server → resource: read recent orders for that customer
3. Call the **Returns MCP server** → tool: `check_return_eligibility(order_id)`
4. Call the **Logistics MCP server** → tool: `generate_return_label(order_id)`
5. Call the **Email MCP server** → tool: `send_email(customer, label_pdf)`

Five different backend systems. The agent didn't need to know any of their APIs directly. Each system has an MCP server; the agent just orchestrates.

---

# Part 3: Skills — Teaching Agents How to Do the Work

---

## Slide 11 — The Problem Skills Solve

LLMs know a lot. They can explain Kubernetes architecture, recite the history of SQL, write a sonnet about your inventory management.

But they don't know **your company's specific procedures**. Like:
- The exact 47-step process for handling a high-value return
- How your firm reconciles inventory across regional warehouses on month-end
- The compliance checks that have to run before issuing a refund over $10,000

Today, the choices are bad: either someone prompts the agent through every step every time, or the agent guesses (which is worse).

**Skills' job**: package up *procedural knowledge* — how to do specific tasks the way your business actually does them — and let the agent pull it in when needed.

---

## Slide 12 — What a Skill Actually Is

A skill is comically simple. It's just a folder with a `SKILL.md` file in it.

```
high-value-return/
├── SKILL.md           ← required (instructions)
├── scripts/           ← optional (executable code)
├── references/        ← optional (extra docs)
└── assets/            ← optional (templates, files)
```

The `SKILL.md` file has two parts:

**1. YAML front matter** (the metadata)
```yaml
---
name: high-value-return
description: Use this when a customer requests a return for an order over $10,000.
              Handles compliance checks, manager approval routing, and refund processing.
---
```

**2. The instructions** — plain markdown describing the workflow, rules, examples.

That's it. Version-controllable. Portable. Reviewable like any code change.

---

## Slide 13 — Progressive Disclosure: Why Skills Scale

What if you have 200 skills installed? Won't they blow through the agent's context window?

No — skills use **progressive disclosure** in three tiers:

- **Tier 1 (always loaded)** — Just the name + description of every skill. A few tokens each. Like a table of contents.
- **Tier 2 (loaded when relevant)** — When a request matches a skill's description, the full `SKILL.md` body gets pulled in.
- **Tier 3 (loaded on demand)** — Scripts, references, and assets only load if the specific task needs them.

The agent decides on its own which skill to invoke based on the description matching the user's request. **That's why a clear, specific description is the most important field in a skill.**

---

## Slide 14 — Skills vs Other Ways of Adding Knowledge

Skills aren't the only way to give an agent knowledge. Here's how they compare:

| Method | What it gives the agent | Example |
|---|---|---|
| **MCP** | Tool access | "I can call the inventory API" |
| **RAG** | Factual lookup | "Let me search our policy docs" |
| **Fine-tuning** | Baked-in knowledge | Permanent, expensive, redo on model change |
| **Skills** | Procedural know-how | "Here's exactly how we handle a high-value return" |

These are **complementary**, not competing. A skill might *use* MCP tools and *reference* RAG-retrieved policy docs as part of its workflow. The skill provides the judgment of *when* and *how*; MCP provides the *capability*; RAG provides the *facts*.

---

## Slide 15 — A Cognitive Science Analogy

Humans have three types of memory, and AI agent architectures are starting to mirror this:

| Human memory | Example | Agent equivalent |
|---|---|---|
| **Semantic** (facts) | "Rome is the capital of Italy" | RAG / knowledge bases |
| **Episodic** (experiences) | "I went to Rome last summer" | Conversation logs / interaction history |
| **Procedural** (skills) | "How to ride a scooter through Rome traffic" | **Skills** |

Skills give agents the kind of memory that humans use when they "just know how" to do something they've practiced.

---

## Slide 16 — Skills in Action: A Retail Example

Imagine a skill called `quarterly-inventory-reconciliation`:

```yaml
---
name: quarterly-inventory-reconciliation
description: Use at quarter-end to reconcile inventory counts across all
              warehouses, flag discrepancies > 2%, and generate the
              compliance report for finance.
---
```

The instructions inside walk the agent through:
1. Pull current stock levels from each warehouse (via MCP → inventory DB)
2. Compare against the system-of-record
3. For discrepancies > 2%, run a re-count workflow
4. Generate the report using the template in `assets/report-template.docx`
5. Email finance using the script in `scripts/notify_finance.py`

When someone asks the agent "run quarter-end reconciliation," it pulls in this skill — and now it knows exactly how *your firm* does it.

---

## Slide 17 — A Word on Skill Safety

Skills can include executable scripts that touch the file system, environment variables, and API keys. That's what makes them powerful — and what makes trust important.

Audits of publicly available skills have found:
- Prompt injection attempts
- Tool poisoning (skills that misuse the tools they're given)
- Hidden malware in scripts

**Treat skill installation like any other software dependency**: review it, understand what it does, only install from trusted sources. The same hygiene you'd apply to an npm package or a pip install.

---

# Part 4: Putting It All Together

---

## Slide 18 — The Big Picture

Here's how the three fit together in a real retail system:

```
        ┌───────────────────────────────────────────────────┐
        │  Customer Support Agent                            │
        │   • Skills: handle-return, escalate-complaint     │
        │   • MCP: CRM, orders DB, email, returns API       │
        └───────────────────────────────────────────────────┘
                              ↕  A2A
        ┌───────────────────────────────────────────────────┐
        │  Inventory Agent                                   │
        │   • Skills: quarterly-reconciliation, low-stock   │
        │   • MCP: inventory DB, warehouse system           │
        └───────────────────────────────────────────────────┘
                              ↕  A2A
        ┌───────────────────────────────────────────────────┐
        │  Supplier Agent (external)                         │
        └───────────────────────────────────────────────────┘
```

- **A2A** = how the agents talk to each other (horizontal arrows)
- **MCP** = how each agent reaches its tools and data (vertical, into the agent)
- **Skills** = the procedural knowledge each agent uses to actually get work done

---

## Slide 19 — When to Use What: Decision Cheat Sheet

| If you need… | Reach for… |
|---|---|
| Two or more agents to coordinate, possibly across teams or vendors | **A2A** |
| An agent to read/write data, call APIs, touch the file system | **MCP** |
| An agent to follow your company's specific multi-step procedure | **Skills** |
| The agent to know a fact ("what's our return policy?") | **RAG** (not covered today, but worth knowing) |
| To bake in a behavior permanently into the model itself | **Fine-tuning** (rarely the right first answer) |

A common pattern in production systems: **all three at once**. A2A for coordination, MCP for capability, Skills for know-how.

---

## Slide 20 — Why This Matters for Us

Three takeaways:

1. **These are open standards**, not vendor lock-in. A2A, MCP, and Skills (agentskills.io, Apache 2.0) are adopted across major platforms — Claude, OpenAI Codex, and others. What you build today carries forward.

2. **They're complementary, not competitive.** The interesting question is no longer "which one do I use?" but "how do I combine them for our use case?"

3. **The hard part isn't the protocol — it's the design.** Which agents should exist? What tools should each one reach? What procedures should be skills vs. instructions? That's the architecture work, and it's where engineering judgment comes in.

---

## Slide 21 — Questions / Discussion

Some prompts to kick off discussion:

- Where in our current systems would A2A reduce custom integration code?
- What internal procedures (the boring, repeatable kind) would make good first skills?
- Which of our existing systems would benefit most from being wrapped as an MCP server?

---

*Thank you.*