# Evidence Levels For R&D PRDs

Use this reference whenever the available product evidence is unclear or weaker than a running product with a working backend.

## Evidence Modes

| Mode | Acceptable evidence | Can specify as observed | Must mark as unverified |
|---|---|---|---|
| Local app with backend | Browser screenshots, network-visible behavior, persisted state after reload | UI state, interaction result, async completion, persisted object, visible errors | Production-only behavior not exercised |
| Demo or staging URL | Browser screenshots, visible success/failure, accessible workflow output | UI state, exposed workflow, visible response, allowed operation | Internal data model, background jobs, integrations not exposed |
| Interactive prototype | Prototype screenshots, clickable transitions, prototype-defined states | Layout, navigation, control presence, intended page states | Persistence, permissions, backend-generated output, task completion guarantees |
| Static screenshots or design frames | Visual reference images | Visual layout only | Workflow completion, button behavior, data writes, async states |
| Requirements only | User decisions, meeting notes, written source material | Confirmed business requirement | UI evidence, functional screenshots, implemented behavior |

## Required Labels

Use one of these labels when evidence is mixed:

- Observed UI: directly visible in the product, demo, staging site, or interactive prototype.
- Required behavior: product decision that R&D must implement.
- Unverified behavior: required or expected behavior that the available evidence cannot prove.
- Decision needed: a product or technical choice that must be confirmed before writing a final requirement.

## Writing Rules

- Do not use static design screenshots as functional proof.
- Do not use meeting recordings as product screenshots.
- Do not fake completion states when a prototype cannot execute the action.
- Do not claim persistence without checking reload, return navigation, or another reliable persistence signal.
- Do not claim generated content correctness from prototype screens.
- Do not describe a backend contract as observed unless it comes from source, API documentation, logs, or R&D-confirmed evidence.
