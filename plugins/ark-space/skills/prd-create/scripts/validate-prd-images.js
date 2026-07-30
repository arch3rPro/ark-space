#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

function usage() {
  console.error("Usage: validate-prd-images.js <prd.md>");
  process.exit(2);
}

const docPath = process.argv[2];
if (!docPath) usage();

const absDoc = path.resolve(docPath);
if (!fs.existsSync(absDoc)) {
  console.error(`PRD not found: ${absDoc}`);
  process.exit(2);
}

const root = path.dirname(absDoc);
const text = fs.readFileSync(absDoc, "utf8");
const imageRefs = [...text.matchAll(/!\[[^\]]*]\(([^)]+)\)/g)].map((m) => m[1].trim());
const allLinks = [...text.matchAll(/(?<!!)\[[^\]]+]\(([^)]*)\)/g)].map((m) => m[1].trim());

const missing = imageRefs.filter((ref) => !isExternal(ref) && !fs.existsSync(path.resolve(root, ref)));
const duplicateImages = [...new Set(imageRefs.filter((ref, i) => imageRefs.indexOf(ref) !== i))];
const absoluteImages = imageRefs.filter((ref) => path.isAbsolute(ref));
const emptyLinks = allLinks.filter((ref) => ref === "").length;

const result = {
  imageRefs: imageRefs.length,
  missing,
  duplicateImages,
  absoluteImages,
  emptyLinks,
};

console.log(JSON.stringify(result, null, 2));

if (missing.length || duplicateImages.length || absoluteImages.length || emptyLinks) {
  process.exit(1);
}

function isExternal(ref) {
  return /^https?:\/\//i.test(ref) || /^data:/i.test(ref);
}
