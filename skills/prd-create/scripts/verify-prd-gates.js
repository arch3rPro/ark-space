#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const REQUIRED_GATES = [
  "Sources, meeting decisions, and conflict lists were read; conflicts were treated as questions until confirmed.",
  "Product access and evidence mode were recorded before drafting detailed behavior.",
  "Every module workflow record was completed before its detailed PRD section was written.",
  "Every detailed workflow uses explicit step headings with operation, page response, controls, R&D requirements, constraints, exceptions, and evidence status.",
  "Each workflow step has a browser screenshot captured from the accessible product or prototype; screenshots are not static design, desktop, meeting, or historical images.",
  "Observed UI, required behavior, unverified behavior, and decision-needed gaps are labeled instead of inferred.",
  "`node scripts/validate-prd-images.js <prd.md>` passed with no missing, duplicate, absolute, or empty links.",
  "`node scripts/verify-prd-gates.js <prd.md> <checklist.md>` passed.",
  "Review decisions were synchronized into the PRD, or no review decision was applicable.",
];
const REQUIRED_STEP_FIELDS = [
  "Operation",
  "Page response",
  "Controls",
  "R&D requirements",
  "Constraints",
  "Exceptions",
  "Evidence status",
];
const MODULE_GATES = [
  "Module workflow record is complete for the active module.",
  "Screenshots are captured for every active-module workflow step.",
  "The active module is written and checked before any next module begins.",
];


function usage() {
  console.error("Usage: verify-prd-gates.js <prd.md> <execution-checklist.md> [--module <module-name>]");
  process.exit(2);
}

const args = process.argv.slice(2);
const [prdPath, checklistPath, flag, moduleName] = args;
if (
  !prdPath ||
  !checklistPath ||
  (flag && (flag !== "--module" || !moduleName)) ||
  args.length > (flag ? 4 : 2)
) usage();

const prd = readRequired(prdPath, "PRD");
const checklist = readRequired(checklistPath, "Execution checklist");
const failures = [];
const mode = parseEvidenceMode(checklist, failures);
validateDecisionGate(checklistPath, checklist, mode, failures);


if (moduleName) {
  validateActiveModule(checklist, moduleName, failures);
  validateCheckedGates(checklist, MODULE_GATES, "module gate", failures);
  validateActiveModuleRecord(checklist, moduleName, failures);

} else {
  validateCompletionGates(checklist, failures);
  validateNoActiveModule(checklist, failures);
}

if (mode === "requirements-only") {
  if (/!\[[^\]]*]\([^)]+\)/.test(prd)) {
    failures.push("requirements-only PRD must not reference screenshots");
  }
  failures.push("requirements-only evidence can produce a requirements draft, not an R&D-ready PRD");
} else if (mode) {
  const scope = moduleName ? selectModule(prd, moduleName, failures) : prd;
  if (scope) validateWorkflows(scope, failures);
  validateImages(prdPath, failures);
}

if (failures.length) {
  console.error(JSON.stringify({ ready: false, failures }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({
  ready: true,
  evidenceMode: mode,
  ...(moduleName ? { moduleVerified: moduleName } : {}),
}, null, 2));

function readRequired(filePath, label) {
  const absolute = path.resolve(filePath);
  if (!fs.existsSync(absolute)) {
    console.error(`${label} not found: ${absolute}`);
    process.exit(2);
  }
  return fs.readFileSync(absolute, "utf8");
}

function parseEvidenceMode(text, failures) {
  const match = text.match(/^- Evidence mode:\s*`?(local-app|demo-staging|interactive-prototype|requirements-only)`?\s*$/m);
  if (!match) {
    failures.push("checklist must declare one evidence mode: local-app, demo-staging, interactive-prototype, or requirements-only");
    return null;
  }
  return match[1];
}

function validateDecisionGate(checklistPath, text, mode, failures) {
  const blocking = text.match(/^- Blocking decisions:\s*`?([^`\n]+)`?\s*$/m);
  const authorized = text.match(/^- Product access authorized:\s*`?(yes|no)`?\s*$/mi);
  const decisionPath = text.match(/^- Decision checklist:\s*`?([^`\n]+)`?\s*$/m);

  if (!blocking) {
    failures.push("checklist must declare Blocking decisions");
  } else if (mode !== "requirements-only" && blocking[1].trim().toLowerCase() !== "none") {
    failures.push(`blocking decisions remain: ${blocking[1].trim()}`);
  }
  if (mode !== "requirements-only" && (!authorized || authorized[1].toLowerCase() !== "yes")) {
    failures.push("product access is not authorized");
  }
  if (!decisionPath) {
    failures.push("checklist must declare a Decision checklist path or none");
    return;
  }

  const reference = decisionPath[1].trim();
  if (reference.toLowerCase() === "none") return;
  const absolute = path.resolve(path.dirname(path.resolve(checklistPath)), reference);
  if (!fs.existsSync(absolute)) {
    failures.push(`decision checklist not found: ${absolute}`);
    return;
  }
  const decisions = fs.readFileSync(absolute, "utf8");
  const blockingRows = [...decisions.matchAll(/^\|([^|\n]+)\|.*\|\s*blocking\s*\|.*$/gim)]
    .map((match) => match[1].trim())
    .filter((id) => id && id !== "ID");
  if (mode !== "requirements-only" && blockingRows.length) {
    failures.push(`decision checklist contains blocking decisions: ${blockingRows.join(", ")}`);
  }
}

function validateActiveModuleRecord(text, module, failures) {
  const row = [...text.matchAll(/^\|\s*([^|\n]+)\s*\|.*$/gm)]
    .find((match) => match[1].trim() === module);
  if (!row) {
    failures.push(`module workflow record not found for '${module}'`);
    return;
  }
  const cells = row[0].split("|").map((cell) => cell.trim());
  const workflowConfirmed = (cells[6] || "").toLowerCase();
  const questionStatus = (cells[8] || "").toLowerCase();
  if (!["yes", "confirmed", "已确认"].includes(workflowConfirmed)) {
    failures.push(`active module '${module}' workflow is not confirmed`);
  }
  if (questionStatus === "blocking" || questionStatus === "阻塞") {
    failures.push(`active module '${module}' has blocking open questions`);
  } else if (!["confirmed", "non-blocking", "已确认", "非阻塞"].includes(questionStatus)) {
    failures.push(`active module '${module}' must classify open questions as confirmed, non-blocking, or blocking`);
  }
}

function validateActiveModule(text, module, failures) {
  const match = text.match(/^- Active module:\s*`?([^`\n]+)`?\s*$/m);
  if (!match) {
    failures.push("checklist must declare an Active module before module verification");
  } else if (match[1].trim() !== module) {
    failures.push(`active module '${match[1].trim()}' does not match requested module '${module}'`);
  }
}

function validateNoActiveModule(text, failures) {
  const match = text.match(/^- Active module:\s*`?([^`\n]+)`?\s*$/m);
  if (!match || match[1].trim().toLowerCase() !== "none") {
    failures.push("final readiness requires '- Active module: `none`' after every module has been verified");
  }
}

function validateCheckedGates(text, gates, label, failures) {
  for (const gate of gates) {
    const escaped = escapeRegExp(gate);
    if (new RegExp(`^- \\[x\\] ${escaped}$`, "m").test(text)) continue;
    if (new RegExp(`^- \\[ \\] ${escaped}$`, "m").test(text)) {
      failures.push(`unchecked ${label}: ${gate}`);
    } else {
      failures.push(`missing ${label}: ${gate}`);
    }
  }
}

function selectModule(prd, module, failures) {
  const headings = [...prd.matchAll(/^## .+$/gm)];
  const matching = headings.filter((heading) => new RegExp(escapeRegExp(module), "i").test(heading[0]));
  if (matching.length !== 1) {
    failures.push(`expected exactly one level-two module heading containing '${module}', found ${matching.length}`);
    return null;
  }
  const heading = matching[0];
  const next = headings.find((candidate) => candidate.index > heading.index);
  return prd.slice(heading.index, next ? next.index : prd.length);
}

function validateCompletionGates(text, failures) {
  for (const gate of REQUIRED_GATES) {
    const escaped = escapeRegExp(gate);
    if (new RegExp(`^- \\[x\\] ${escaped}$`, "m").test(text)) continue;
    if (new RegExp(`^- \\[ \\] ${escaped}$`, "m").test(text)) {
      failures.push(`unchecked completion gate: ${gate}`);
    } else {
      failures.push(`missing completion gate: ${gate}`);
    }
  }
}

function validateWorkflows(prd, failures) {
  const confirmationOffsets = [...prd.matchAll(/^### .*Workflow Confirmation\s*$/gim)].map((match) => match.index);
  const workflowMatches = [...prd.matchAll(/^### .*Main Workflow.*$/gim)];
  if (!workflowMatches.length) {
    failures.push("PRD must include at least one 'Main Workflow' section");
    return;
  }

  for (const workflow of workflowMatches) {
    if (!confirmationOffsets.some((offset) => offset < workflow.index)) {
      failures.push(`workflow '${workflow[0]}' appears before any Workflow Confirmation section`);
    }
    const nextWorkflow = workflowMatches.find((candidate) => candidate.index > workflow.index);
    const boundary = nextWorkflow ? nextWorkflow.index : prd.length;
    const workflowText = prd.slice(workflow.index, boundary);
    const steps = [...workflowText.matchAll(/^#### Step\s+\d+:.+$/gim)];
    if (!steps.length) {
      failures.push(`workflow '${workflow[0]}' has no explicit '#### Step N: …' headings`);
      continue;
    }
    for (const [index, step] of steps.entries()) {
      const nextStep = steps[index + 1];
      const stepText = workflowText.slice(step.index, nextStep ? nextStep.index : workflowText.length);
      const label = step[0].trim();
      if (!/!\[[^\]]*]\([^)]+\)/.test(stepText)) {
        failures.push(`${label} has no screenshot`);
      }
      for (const field of REQUIRED_STEP_FIELDS) {
        if (!new RegExp(`^- ${escapeRegExp(field)}:\s*.+$`, "mi").test(stepText)) {
          failures.push(`${label} is missing '${field}'`);
        }
      }
      const evidence = stepText.match(/^- Evidence status:\s*(.+)$/mi);
      if (evidence && !/^(observed|required|unverified|decision needed)$/i.test(evidence[1].trim())) {
        failures.push(`${label} has invalid Evidence status '${evidence[1].trim()}'`);
      }
    }
  }
}

function validateImages(prdPath, failures) {
  const validator = path.join(__dirname, "validate-prd-images.js");
  const result = spawnSync(process.execPath, [validator, prdPath], { encoding: "utf8" });
  if (result.status !== 0) {
    failures.push(`image validation failed: ${(result.stdout || result.stderr).trim()}`);
  }
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
