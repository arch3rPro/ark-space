#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

function usage() {
  console.error("Usage: audit-prd-portability.js [--terms=term1,term2] <file-or-directory> [more paths...]");
  process.exit(2);
}

const rawArgs = process.argv.slice(2);
const termArg = rawArgs.find((arg) => arg.startsWith("--terms="));
const customTerms = termArg ? termArg.slice("--terms=".length).split(",").map((term) => term.trim()).filter(Boolean) : [];
const targets = rawArgs.filter((arg) => !arg.startsWith("--terms="));
if (!targets.length) usage();

const checks = [
  { name: "Chinese characters", pattern: /[\u3400-\u9fff]/ },
  { name: "Codex-specific wording", pattern: /\bCodex\b|\.codex|openai\.yaml/i },
  { name: "One-off project wording", pattern: /one-off|project-specific|this project only|current project only/i },
  { name: "Screenshot anti-patterns", pattern: /desktop screenshot|meeting video screenshot|old screenshot|fake screenshot/i },
];

if (customTerms.length) {
  checks.push({
    name: "Configured domain terms",
    pattern: new RegExp(customTerms.map(escapeRegExp).join("|"), "i"),
  });
}

const files = targets.flatMap(collectFiles).filter((file) => /\.(md|yaml|yml|txt)$/i.test(file));
const findings = [];

for (const file of files) {
  const text = fs.readFileSync(file, "utf8");
  const lines = text.split(/\r?\n/);
  lines.forEach((line, index) => {
    for (const check of checks) {
      if (isInstructionalException(check.name, line)) continue;
      if (check.pattern.test(line)) {
        findings.push({
          file,
          line: index + 1,
          check: check.name,
          text: line.trim(),
        });
      }
    }
  });
}

console.log(JSON.stringify({ files: files.length, findings }, null, 2));
process.exit(findings.length ? 1 : 0);

function collectFiles(target) {
  const abs = path.resolve(target);
  if (!fs.existsSync(abs)) return [];
  const stat = fs.statSync(abs);
  if (stat.isFile()) return [abs];
  if (!stat.isDirectory()) return [];
  return fs.readdirSync(abs, { withFileTypes: true }).flatMap((entry) => {
    if (entry.name === ".git" || entry.name === "node_modules") return [];
    return collectFiles(path.join(abs, entry.name));
  });
}

function isInstructionalException(checkName, line) {
  const trimmed = line.trim();
  if (checkName === "Screenshot anti-patterns") {
    return /^- Do not\b/i.test(trimmed) || /\bnot desktop screenshot\b/i.test(trimmed) || /\bUse only screenshots\b/i.test(trimmed);
  }
  return false;
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
