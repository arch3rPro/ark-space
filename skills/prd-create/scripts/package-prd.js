#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const cp = require("child_process");

function usage() {
  console.error("Usage: package-prd.js <prd.md> <output-dir> [supporting-file ...]");
  process.exit(2);
}

const [prdPath, outputDir, ...supportingFiles] = process.argv.slice(2);
if (!prdPath || !outputDir) usage();

const absPrd = path.resolve(prdPath);
const absOut = path.resolve(outputDir);
if (!fs.existsSync(absPrd)) {
  console.error(`PRD not found: ${absPrd}`);
  process.exit(2);
}

if (fs.existsSync(absOut)) {
  console.error(`Output directory already exists: ${absOut}`);
  process.exit(2);
}

const zipPath = `${absOut}.zip`;
if (fs.existsSync(zipPath)) {
  console.error(`Output zip already exists: ${zipPath}`);
  process.exit(2);
}

fs.mkdirSync(absOut, { recursive: true });

const prdRoot = path.dirname(absPrd);
const prdText = fs.readFileSync(absPrd, "utf8");
const imageRefs = [...prdText.matchAll(/!\[[^\]]*]\(([^)]+)\)/g)].map((m) => m[1].trim());

copyFile(absPrd, path.join(absOut, path.basename(absPrd)));

for (const ref of imageRefs) {
  if (isExternal(ref) || path.isAbsolute(ref)) continue;
  const src = path.resolve(prdRoot, ref);
  if (!fs.existsSync(src)) continue;
  copyFile(src, path.join(absOut, ref));
}

for (const file of supportingFiles) {
  const abs = path.resolve(file);
  if (!fs.existsSync(abs) || !fs.statSync(abs).isFile()) continue;
  copyFile(abs, path.join(absOut, "supporting-docs", path.basename(abs)));
}

const manifest = [
  "# PRD Package",
  "",
  `- Package time: ${new Date().toISOString()}`,
  `- Main PRD: ${path.basename(absPrd)}`,
  `- Referenced screenshots: ${imageRefs.length}`,
  `- Supporting docs: ${supportingFiles.length}`,
  "",
].join("\n");
fs.writeFileSync(path.join(absOut, "PACKAGE_MANIFEST.md"), manifest);

cp.execFileSync("zip", ["-qr", zipPath, path.basename(absOut)], { cwd: path.dirname(absOut) });

console.log(JSON.stringify({ packageDir: absOut, zipPath }, null, 2));

function copyFile(src, dest) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
}

function isExternal(ref) {
  return /^https?:\/\//i.test(ref) || /^data:/i.test(ref);
}
