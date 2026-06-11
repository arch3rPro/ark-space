# Handoff Template

Use this format when work moves between callable agents.

```text
Role: <target agent path>
Reason: <why this role is the smallest useful fit>
Inputs: <files, user request, constraints>
Expected output: <artifact or decision>
Skills: <skills the target agent should use>
Verification: <how completion will be checked>
Escalation: <when to return to Orchestrator>
```

Keep handoffs short enough to preserve momentum and specific enough that the receiving agent does not start cold.

## Structured Context

For multi-step workflows, include this compact JSON block after the text handoff when the next agent needs machine-readable state.

```json
{
  "target_agent": "agents/<domain>/<agent>.md",
  "reason": "why this agent owns the next step",
  "inputs": {
    "files": [],
    "urls": [],
    "constraints": [],
    "provider": null
  },
  "expected_output": "artifact or decision",
  "verification": [],
  "stop_conditions": []
}
```

Use structured context for sequential or parallel workflows. For a simple single-agent handoff, the text template is enough.
