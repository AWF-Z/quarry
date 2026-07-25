<div align="center">

### Quarry

# Supercharge your AI research.

Quarry helps agents uncover better opportunities, eliminate weak directions, verify the evidence, and identify the next action worth taking.

**English** · [简体中文](docs/i18n/README.zh-CN.md) · [繁體中文](docs/i18n/README.zh-TW.md) · [Español](docs/i18n/README.es.md) · [हिन्दी](docs/i18n/README.hi.md) · [العربية](docs/i18n/README.ar.md) · [Português](docs/i18n/README.pt-BR.md) · [Français](docs/i18n/README.fr.md) · [Deutsch](docs/i18n/README.de.md) · [日本語](docs/i18n/README.ja.md) · [한국어](docs/i18n/README.ko.md) · [Русский](docs/i18n/README.ru.md) · [Bahasa Indonesia](docs/i18n/README.id.md)

</div>

The same model, asked the same question. Quarry pushes the research past a generic answer and toward a grounded decision.

<div align="center">

### Install once. Research normally.

</div>

```text
curl -fsSL https://raw.githubusercontent.com/AWF-Z/quarry/v1.0.3/install.py | python3
```

The installer detects and configures **Claude Code, Codex, Gemini CLI, Cursor, and VS Code**. They use the same Quarry engine and skill. For any other MCP-compatible agent, it prints the standard configuration to add.

Windows PowerShell:

```powershell
py -3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/AWF-Z/quarry/v1.0.3/install.py').read())"
```

Prefer to inspect installers before running them?

```bash
curl -fsSLo quarry-install.py https://raw.githubusercontent.com/AWF-Z/quarry/v1.0.3/install.py
echo "5746481e6abd2806f8c34071297f31c05c0d3888d9765f0d1dd30de7a2f33861  quarry-install.py" | shasum -a 256 -c -
less quarry-install.py
python3 quarry-install.py
```

Or install entirely from a reviewed checkout:

```bash
git clone --branch v1.0.3 --depth 1 https://github.com/AWF-Z/quarry.git
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

The installer runs its doctor automatically and verifies the skill, the four
protocol-v2 MCP tools, the hosted engine's v2 contract, and each detected agent
registration. Protocol v2 uses a server-minted signed run binding and does not
require a host/chat turn identifier. Restart each open agent once after
installation. To recheck later from a reviewed checkout, run
`python3 install.py --doctor`.

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

Benchmarks in progress. Every result, including the negative ones, is published.

Earlier internal figures have been withdrawn from this page. They were produced under an output contract that asked the Quarry arm for fields the control arm was never asked for, so they measured schema asymmetry rather than research quality, and they are not re-earnable in that form. The replacement evaluations use an identical output contract for both arms, a real comparator, and a scoring rubric written before the contracts. Their results will be published here whichever way they fall.

## Privacy

The public client contains no analytics or telemetry. When the full Quarry tools are used, it sends the research question, candidate summaries, and public evidence supplied by your agent to the configured Quarry service; it should not be given private files, credentials, or private source contents. Research tools invoked by your agent remain governed by that agent platform and your own provider settings.

## Contributing

Contributions are welcome. Good places to help include research commands, public skill behavior, agent-platform integrations, examples, documentation, accessibility, and translations.

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the public extension boundary, development workflow, and validation commands.

## License

The files in this public repository are available under the [MIT License](LICENSE). Quarry product and commercial services may include separately distributed capabilities under separate terms.
