---
description: Turn a research question into a grounded, decision-ready brief.
argument-hint: <research question>
allowed-tools: WebSearch, WebFetch, Read, Agent
---

Use the Quarry skill to research this question:

$ARGUMENTS

Use the full Quarry MCP loop when its tools are available. Follow `next_tool` through submission, differentiation, and finalization rather than stopping after the first search pass.

End with the exact `execution_receipt.display` returned by `quarry_finalize`. If the MCP tools are unavailable or any full-run call fails, say so and end with `Quarry Skill Only • hosted verification not run`. Never silently substitute the skill-only path for an explicitly requested full run.

Return a decision-ready brief, not a generic summary. Identify what is known, what already exists, the strongest remaining opportunities or options, the evidence behind each important claim, weak directions that should be eliminated, the cheapest useful next test, and what result should change the recommendation.
