---
description: Search a domain for grounded opportunities and the strongest next test.
argument-hint: <domain or problem>
allowed-tools: WebSearch, WebFetch, Read, Agent
---

Use the Quarry skill to find opportunities in:

$ARGUMENTS

Use the full Quarry MCP loop when its tools are available. Follow `next_tool` through submission, differentiation, and finalization rather than stopping after the first search pass.

End with the exact `execution_receipt.display` returned by `quarry_finalize`. If the MCP tools are unavailable or any full-run call fails, say so and end with `Quarry Skill Only • hosted verification not run`. Never silently substitute the skill-only path for an explicitly requested full run.

Do not return a generic idea list. Compare the strongest candidates against existing products, approaches, and evidence. Remove weak or already-covered directions. For each surviving opportunity, name who needs it, what remains unsolved, why it may matter now, the fastest validation test, and a clear walk-away condition.
