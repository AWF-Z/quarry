---
name: quarry
description: Use when research must lead to a decision, opportunity, validation plan, market map, or evidence-backed recommendation rather than a generic answer.
---

# Quarry

Turn open-ended research into a grounded decision.

## Execution policy

The user does not choose between confusing modes. For every qualifying research request:

1. Use Full Quarry automatically when `quarry_start`, `quarry_submit`,
   `quarry_finalize`, and `quarry_artifact` are available.
2. Otherwise use the public skill behavior as a fallback.
3. Never claim or imply that Full Quarry ran unless `quarry_finalize` returned a real execution receipt.

Every final research answer must end with exactly one visible execution line:

- Copy `execution_receipt.display` verbatim from `quarry_finalize` after a successful full run. It has the form `Full Quarry • run qr_... • 2 rounds • 12 sources verified`.
- Otherwise write `Quarry Skill Only • hosted verification not run`.

Never invent a run ID, round count, or verified-source count. If the user explicitly asks for "Full Quarry", "the full pipeline", or equivalent and the tools are missing or a tool call fails, say that Full Quarry is unavailable before continuing with the clearly labeled fallback. A similar-looking answer is not evidence that the full engine ran.

Never create, guess, copy, or send a host/chat turn identifier. Protocol v2
makes the Quarry service mint the signed run binding. Preserve the returned
`run_id`, `run_capability`, and canonical question exactly through submission
and finalization.

## Full Quarry engine

When the Quarry MCP tools are available, use them automatically for qualifying research:

1. Call `quarry_start` before broad research, sending only a public-safe question.
2. Follow its protected research directives using the agent's normal research tools.
3. Call `quarry_submit` with the returned capability, canonical question,
   candidate objects, public source URLs, and exact supporting quotes.
4. If Quarry requests differentiation, research the named gap and submit the next round.
5. Call `quarry_finalize`, then call `quarry_artifact` once with its artifact ID
   and retrieval token. Use the bounded verified summary and exact receipt
   display in the answer; do not invent receipt or artifact contents.

Do not send private files, credentials, private source contents, unreleased
strategy, private competition or benchmark details, expected answers, judge
material, another arm's output, or campaign aggregates. If a
decision-equivalent public abstraction can be written without leaking or
distorting private facts, research that abstraction with the hosted tools and
combine the public findings with private context locally. If no safe abstraction
exists, use the public skill fallback. This is a privacy-preserving choice—not a
rejected receipt, failed handshake, activation error, or hosted outage.

If the hosted service is genuinely unavailable, state that Full Quarry was
unavailable and continue with the public behavior below rather than pretending
the private checks ran.

## When to activate

Activate for opportunity discovery, business or side-project ideas, market and competitor research, product strategy, technical diligence, policy or regulation research, investment theses, recurring monitoring, and requests to verify an agent's research.

## Required output

Produce a concise decision brief containing:

1. **Decision or objective** - what the research is meant to settle.
2. **What already exists** - the strongest relevant products, approaches, or prior work.
3. **Best remaining options** - specific opportunities or recommendations, not categories.
4. **Evidence** - direct sources for load-bearing factual claims; label inference and uncertainty.
5. **Weak directions removed** - attractive paths that evidence does not support or that are already covered.
6. **Next action** - the cheapest useful test, evidence pull, prototype, or interview.
7. **Walk-away condition** - the observation that should reverse the recommendation.

## Research behavior

- Search beyond the first obvious framing and compare materially different alternatives.
- Treat claims from search snippets and secondary summaries as leads until checked against the underlying source.
- Look specifically for existing solutions before calling an opportunity open.
- Do not equate an existing competitor with a dead opportunity; identify whether a sharper buyer, workflow, constraint, or approach remains.
- Do not call an idea novel or proven when the available evidence only makes it plausible.
- Prefer a smaller set of grounded options over a long speculative list.
- When evidence is insufficient, say what is missing and how to obtain it.

The final answer should be useful to someone deciding what to do next without needing to inspect the research process.
