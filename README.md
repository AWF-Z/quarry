<div align="center">

### Quarry

# Supercharge your AI research.

Quarry helps agents uncover better opportunities, eliminate weak directions, verify the evidence, and identify the next action worth taking.

**English** · [简体中文](docs/i18n/README.zh-CN.md) · [繁體中文](docs/i18n/README.zh-TW.md) · [Español](docs/i18n/README.es.md) · [हिन्दी](docs/i18n/README.hi.md) · [العربية](docs/i18n/README.ar.md) · [Português](docs/i18n/README.pt-BR.md) · [Français](docs/i18n/README.fr.md) · [Deutsch](docs/i18n/README.de.md) · [日本語](docs/i18n/README.ja.md) · [한국어](docs/i18n/README.ko.md) · [Русский](docs/i18n/README.ru.md) · [Bahasa Indonesia](docs/i18n/README.id.md)

</div>

![Quarry research outcomes from internal evaluations: 2.08x verified opportunities per research run; 81.7% fewer unsupported claims after evidence checks; 100% of planted source errors caught; 34 high-potential opportunities rated 8/10 or higher; complete evidence trails in 100% of runs.](docs/assets/quarry-proof-numbers.svg)

The same model, asked the same question. Quarry pushes the research past a generic answer and toward a grounded decision.

![On 17 real decision tasks with the same Claude Sonnet 5 configuration and a blind judge, Sonnet 5 alone was preferred 12% of the time and Sonnet 5 with Quarry was preferred 88%. Quarry also eliminated 4.35 weak directions per run, produced a concrete one-week test for every result, and caught existing competitors in 8 of 8 cases before recommendation. Internal evaluation.](docs/assets/quarry-sonnet-comparison.svg)

<div align="center">

### Install once. Research normally.

</div>

```text
curl -fsSL https://raw.githubusercontent.com/AWF-Z/quarry/v1.0.2/install.py | python3
```

The installer detects and configures **Claude Code, Codex, Gemini CLI, Cursor, and VS Code**. They use the same Quarry engine and skill. For any other MCP-compatible agent, it prints the standard configuration to add.

Windows PowerShell:

```powershell
py -3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/AWF-Z/quarry/v1.0.2/install.py').read())"
```

Prefer to inspect installers before running them?

```bash
curl -fsSLo quarry-install.py https://raw.githubusercontent.com/AWF-Z/quarry/v1.0.2/install.py
echo "2cf83230483bec7ae649e9ae354e44908fdba20e82ccbfd06ae11e9affad40b8  quarry-install.py" | shasum -a 256 -c -
less quarry-install.py
python3 quarry-install.py
```

Or install entirely from a reviewed checkout:

```bash
git clone --branch v1.0.2 --depth 1 https://github.com/AWF-Z/quarry.git
python3 quarry/install.py --source-dir quarry
```

Claude Code users can also use its native plugin command:

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

The installer runs its doctor automatically and verifies the skill, the four MCP tools, the hosted engine, and each detected agent registration. Restart each open agent once after installation. To recheck later from a reviewed checkout, run `python3 install.py --doctor`.

Every Quarry research answer shows which path actually ran:

```text
Full Quarry • run qr_... • 2 rounds • 12 sources verified
```

If the hosted engine was not used, the answer must instead say:

```text
Quarry Skill Only • hosted verification not run
```

There are only two user-visible execution states: Full Quarry and the clearly labeled Skill Only fallback.

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

Quarry works around the model you already use rather than replacing it. The same public MCP bridge works with Claude Code, Codex, Gemini CLI, Cursor, VS Code, and other MCP-compatible agents.

## Global access

The installer and client are portable across macOS, Linux, and Windows wherever Python 3 and a supported agent are available. Both distribution and service locations can be replaced without changing Quarry:

```text
QUARRY_DISTRIBUTION_URL=https://your-mirror.example/quarry \
QUARRY_API_URL=https://your-quarry-endpoint.example \
python3 install.py
```

This makes Quarry ready for regional mirrors and endpoints. The current public files are distributed through GitHub and the hosted engine currently runs on Fly.io, so reliable access from every network worldwide, including every mainland China network, is not yet guaranteed. See [Global availability](docs/GLOBAL_ACCESS.md).

## Numbers

The figures above come from separate internal, precommitted evaluations of the full Quarry system. The blind comparison used the same Sonnet 5 configuration on both sides across 17 real decision tasks; a tie did not count as a Quarry win. They are not third-party-replicated results and are presented as internal evidence, not a universal model benchmark.

## Privacy

The public client contains no analytics or telemetry. When the full Quarry tools are used, it sends the research question, candidate summaries, and public evidence supplied by your agent to the configured Quarry service; it should not be given private files, credentials, or private source contents. Research tools invoked by your agent remain governed by that agent platform and your own provider settings.

## Contributing

Contributions are welcome. Good places to help include research commands, public skill behavior, agent-platform integrations, examples, documentation, accessibility, and translations.

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the public extension boundary, development workflow, and validation commands.

## License

The files in this public repository are available under the [MIT License](LICENSE). Quarry product and commercial services may include separately distributed capabilities under separate terms.
