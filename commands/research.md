---
description: Turn a research question into a grounded, decision-ready brief.
argument-hint: <research question>
allowed-tools: WebSearch, WebFetch, Read, Agent
---

Use the Quarry skill to research this question:

$ARGUMENTS

Use the full Quarry MCP loop when its tools are available. Never send a host/chat
turn identifier. Start with a public-safe question, preserve the service-minted
run capability and canonical question, follow `next_action` through submission
and finalization, then retrieve `quarry_artifact` once.

End with the exact `execution_receipt.display` returned by `quarry_finalize`. If the MCP tools are unavailable or any full-run call fails, say so and end with `Quarry Skill Only • hosted verification not run`. Never silently substitute the skill-only path for an explicitly requested full run.

Keep private strategy and competition details local. If no decision-equivalent
public abstraction is safe, use Skill Only and describe it as a privacy choice,
not a rejected activation, handshake, turn identifier, or receipt.

Return a decision-ready brief, not a generic summary. Identify what is known, what already exists, the strongest remaining opportunities or options, the evidence behind each important claim, weak directions that should be eliminated, the cheapest useful next test, and what result should change the recommendation.
