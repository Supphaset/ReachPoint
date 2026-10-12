// C10 rule: screens use the shared tokens only. Fails on raw colours outside src/ui/tokens.css.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("../src", import.meta.url));
const ALLOWED = new Set([join(ROOT, "ui/tokens.css")]);
const RAW = /#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/;

function* files(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* files(p);
    else if (/\.(css|tsx?)$/.test(name) && !/\.test\.tsx?$/.test(name)) yield p;
  }
}

const bad = [];
for (const f of files(ROOT)) {
  if (ALLOWED.has(f)) continue;
  readFileSync(f, "utf8")
    .split("\n")
    .forEach((line, i) => {
      if (RAW.test(line.replace(/url\(#[\w-]+\)/g, ""))) bad.push(`${f.replace(ROOT, "src")}:${i + 1}: ${line.trim()}`);
    });
}
if (bad.length) {
  console.error("Raw colours found; use a token from src/ui/tokens.css:\n" + bad.join("\n"));
  process.exit(1);
}
console.log("Tokens check passed: no raw colours outside tokens.css");
