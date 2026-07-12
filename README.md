<div align="center">

### Quarry

# Supercharge your AI research.

Quarry helps agents uncover better opportunities, eliminate weak directions, verify the evidence, and identify the next action worth taking.

**English** · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [Español](README.es.md) · [हिन्दी](README.hi.md) · [العربية](README.ar.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Русский](README.ru.md) · [Bahasa Indonesia](README.id.md)

</div>

![Quarry research outcomes from internal evaluations: 2.08x verified opportunities per research run; 81.7% fewer unsupported claims after evidence checks; 100% of planted source errors caught; 34 high-potential opportunities rated 8/10 or higher; complete evidence trails in 100% of runs.](docs/assets/quarry-proof-numbers.svg)

The same model, asked the same question. Quarry pushes the research past a generic answer and toward a grounded decision.

![On 17 real decision tasks with the same Claude Sonnet 5 configuration and a blind judge, Sonnet 5 alone was preferred 12% of the time and Sonnet 5 with Quarry was preferred 88%. Quarry also eliminated 4.35 weak directions per run, produced a concrete one-week test for every result, and caught existing competitors in 8 of 8 cases before recommendation. Internal evaluation.](docs/assets/quarry-sonnet-comparison.svg)

<div align="center">

### Install once. Research normally.

</div>

```text
/plugin marketplace add AWF-Z/quarry && /plugin install quarry@quarry
```

Then ask your agent naturally:

```text
Find a side project in healthcare that is worth testing.
Map this market and show me the strongest remaining opportunity.
Research whether this product idea is already covered.
Compare these strategies and tell me what evidence should change the decision.
```

Quarry activates when the work calls for research, opportunity discovery, validation, market mapping, or evidence checking. You can also call `/quarry:research` or `/quarry:discover` directly.

## A better result, not just a longer answer

```text
Question: Find a side project in healthcare.

Normal AI: Build an AI billing tool for hospitals.

Quarry:  Buyer: revenue-cycle manager
         What already exists: named billing and claims products
         Remaining opportunity: patient-specific payment-rate integrity
         Evidence: sourced market pain and competitor coverage
         Fastest test: audit 25 paid claims
         Walk away if: an incumbent already covers the recalculation
```

Quarry is useful whenever research must lead to a decision, not just an answer:

| | |
|---|---|
| business and side-project discovery | competitor and market research |
| product strategy | technical due diligence |
| regulation and policy research | investment and research theses |
| debugging agent research and source claims | recurring market and topic monitoring |

## What Quarry adds

- broader opportunity and alternative discovery;
- explicit competitor and existing-solution checks;
- sourced claims separated from assumptions;
- weak directions removed before they consume more work;
- a concrete next test and a clear walk-away condition.

Quarry works around the model you already use rather than replacing it. The public plugin currently targets Claude Code; additional agent adapters are planned.

## Numbers

The figures above come from separate internal, precommitted evaluations of the full Quarry system. The blind comparison used the same Sonnet 5 configuration on both sides across 17 real decision tasks; a tie did not count as a Quarry win. They are not third-party-replicated results and are presented as internal evidence, not a universal model benchmark.

## Privacy

The public plugin contains no analytics, telemetry, credentials, or background network service. Research tools invoked by your agent remain governed by that agent platform and your own provider settings.

## License

The files in this public repository are available under the [MIT License](LICENSE). Quarry product and commercial services may include separately distributed capabilities under separate terms.
