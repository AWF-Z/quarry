# Global availability

Quarry uses one MCP client and one skill across supported agents. There is no Claude-only, Codex-only, or China-specific version of the product.

## Supported agent hosts

The universal installer detects and configures:

- Claude Code
- Codex
- Gemini CLI
- Cursor
- Visual Studio Code

For another MCP-compatible host, the installer prints a standard `mcpServers` entry containing the local Quarry client command. The host must support a local stdio MCP server.

The installer also places the Quarry skill in the shared Agent Skills location at `~/.agents/skills/quarry/SKILL.md`. Hosts that implement the Agent Skills standard can discover the same research behavior without a Quarry-specific edition.

## Regional portability

Two environment variables remove infrastructure lock-in:

- `QUARRY_DISTRIBUTION_URL` selects the public file mirror used by the installer.
- `QUARRY_API_URL` selects the Quarry engine endpoint used by the client.

A mirror must preserve these public paths:

```text
client/quarry_mcp.py
skills/quarry/SKILL.md
```

Example:

```text
QUARRY_DISTRIBUTION_URL=https://mirror.example/quarry \
QUARRY_API_URL=https://api.example.cn \
python3 install.py
```

## Mainland China

The software is compatible, but the current production route cannot promise reliable access on every mainland China network. The default installer downloads public files from GitHub and the hosted engine is outside mainland China.

A dependable mainland launch requires:

1. a China-accessible public distribution mirror;
2. a tested regional or mainland engine endpoint;
3. monitoring from multiple mainland networks;
4. any hosting, filing, privacy, and security requirements applicable to the chosen operator and deployment.

The installer and client already support the first two without a fork. Until those deployment steps are completed and measured, describe Quarry as globally portable, not universally reachable.
