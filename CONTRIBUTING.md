# Contributing to Quarry

Thank you for helping improve Quarry. This repository is the public plugin and documentation surface, and contributions to that surface are welcome.

## Good Contributions

- improve the clarity, reliability, or usefulness of public research commands;
- add a new command for a broadly useful research workflow;
- improve the public Quarry skill without making it unnecessarily complicated;
- add support or documentation for another agent platform;
- improve examples, accessibility, installation, or security guidance;
- correct or extend a translation;
- fix broken links, rendering problems, or plugin metadata;
- report a reproducible bug or propose a focused feature.

Please do not include credentials, private datasets, copyrighted source material, personal research history, generated run transcripts, or confidential company information in an issue or pull request.

## Repository Map

| Path | Purpose |
|---|---|
| `.claude-plugin/` | Claude Code plugin and marketplace metadata |
| `commands/` | User-invoked research commands |
| `skills/quarry/` | Public Quarry skill behavior |
| `docs/assets/` | Approved public visuals |
| `docs/i18n/` | Localized entry pages and visuals |
| `scripts/check_public_repo.py` | Offline repository validation |

## Before You Start

For a substantial feature, open an issue first. Describe the user problem, the proposed public behavior, and how someone can verify that it works. Small fixes can go directly to a pull request.

Security vulnerabilities and accidental exposure of private information must be reported through a private GitHub security advisory, not a public issue.

## Local Setup

```bash
git clone https://github.com/AWF-Z/quarry.git
cd quarry
python3 scripts/check_public_repo.py
```

If Claude Code is installed, also validate the plugin manifest:

```bash
claude plugin validate .
```

To test installation without affecting your normal setup, use an isolated home directory:

```bash
tmp="$(mktemp -d)"
mkdir -p "$tmp/home" "$tmp/project"
cd "$tmp/project"
HOME="$tmp/home" claude plugin marketplace add AWF-Z/quarry --scope local
HOME="$tmp/home" claude plugin install quarry@quarry --scope local
HOME="$tmp/home" claude plugin list
```

## Adding or Changing a Command

Commands are Markdown files in `commands/` with YAML front matter. A command should have:

- a specific, user-facing description;
- an argument hint when input is required;
- only the tools it genuinely needs;
- a concise instruction focused on the resulting decision or artifact;
- no hidden credentials, private endpoints, or machine-specific paths.

Keep commands composable. Prefer one clear job over a large command that tries to cover every research workflow.

## Translations

Localized pages live in `docs/i18n/`. Preserve numbers, product names, commands, URLs, and the internal-evaluation label exactly. Translate meaning rather than word order, and verify that both images and every language-switcher link render correctly.

## Pull Request Checklist

- explain the user-facing problem and the change;
- keep the change focused;
- run `python3 scripts/check_public_repo.py`;
- run `claude plugin validate .` when Claude Code is available;
- update documentation or translations affected by the change;
- confirm that the PR contains no secrets, private paths, or confidential data;
- agree that your contribution is licensed under this repository's MIT License.

Maintainers may decline changes that make the public workflow harder to understand, add unverified claims, weaken privacy, or expand scope without a clear user benefit.
