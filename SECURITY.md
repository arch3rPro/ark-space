# Security Policy

## Supported Versions

ArkSpace is currently pre-1.0. Security fixes target the current `main` branch unless a maintainer states otherwise.

## Reporting a Vulnerability

Do not publish sensitive vulnerability details in a public issue.

Use the most appropriate private maintainer contact channel available for the repository. If no private channel is available, open a minimal public issue asking for a private contact path and omit exploit details, tokens, private URLs, or user data.

Please include:

- Affected files or package areas.
- Impact and likely severity.
- Reproduction steps or proof of concept, if safe to share privately.
- Any suggested fix or mitigation.

## Scope

Security-sensitive areas include:

- Plugin manifests and installation metadata.
- Scripts under `scripts/`.
- Skill instructions that could cause unsafe file, network, credential, or publishing behavior.
- Documentation that instructs agents to run commands.

## Handling

Maintainers should acknowledge reports when practical, investigate scope, prepare a fix, and disclose only after a mitigation is available.
