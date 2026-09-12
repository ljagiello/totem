#!/usr/bin/env python3
"""Validate the Mintlify docs: config, page existence, and MDX formatting.

Checks that catch the failures that actually break a Mintlify build:
  - docs.json is valid JSON
  - every page referenced in the nav has a matching .mdx/.md file
  - every .mdx has frontmatter with a title
  - no bare `{`/`}` outside code (MDX parses them as JSX expressions)
  - no unescaped `|` inside a table-cell inline-code span (breaks GFM tables)
  - balanced inline-code backticks
Exit non-zero (with GitHub ::error:: annotations) if anything fails.
"""
import sys, os, re, json

docs = sys.argv[1] if len(sys.argv) > 1 else "docs"
errors = []


def err(msg):
    errors.append(msg)
    print(f"::error::{msg}")


# 1) docs.json valid + referenced pages exist
cfg_path = os.path.join(docs, "docs.json")
if not os.path.isfile(cfg_path):
    err(f"{cfg_path} not found")
    sys.exit(1)
try:
    cfg = json.load(open(cfg_path))
except json.JSONDecodeError as e:
    err(f"{cfg_path}: invalid JSON: {e}")
    sys.exit(1)

pages = []


def collect(node):
    if isinstance(node, list):
        for x in node:
            collect(x)
    elif isinstance(node, dict):
        for k, v in node.items():
            if k == "pages" and isinstance(v, list):
                for item in v:
                    if isinstance(item, str):
                        pages.append(item)
                    else:
                        collect(item)
            else:
                collect(v)


collect(cfg.get("navigation", {}))
if not pages:
    err("no pages found in docs.json navigation")
for p in pages:
    if not (os.path.isfile(os.path.join(docs, p + ".mdx")) or
            os.path.isfile(os.path.join(docs, p + ".md"))):
        err(f"docs.json references '{p}' but {p}.mdx/.md is missing")

# 2) per-file MDX checks
mdx_files = []
for root, _, files in os.walk(docs):
    for f in files:
        if f.endswith(".mdx"):
            mdx_files.append(os.path.join(root, f))

for path in sorted(mdx_files):
    text = open(path).read()
    rel = os.path.relpath(path)

    # frontmatter with title
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        err(f"{rel}: missing frontmatter (--- ... ---)")
    elif not re.search(r"^title:\s*\S", m.group(1), re.M):
        err(f"{rel}: frontmatter has no 'title'")

    # strip fenced code blocks, then inline code spans (DOTALL handles multi-line spans)
    no_fence = re.sub(r"```.*?```", "", text, flags=re.S)
    if no_fence.count("`") % 2:
        err(f"{rel}: odd number of inline-code backticks (unterminated code span)")
    stripped = re.sub(r"`[^`]*`", "", no_fence, flags=re.S)
    stripped = re.sub(r"\bcols=\{\d+\}", "", stripped)  # allow <CardGroup cols={N}>
    if "{" in stripped or "}" in stripped:
        # locate lines for a helpful message (best effort)
        infence = False
        for i, ln in enumerate(text.split("\n"), 1):
            s = ln.strip()
            if s.startswith("```"):
                infence = not infence
                continue
            if infence:
                continue
            nc = re.sub(r"`[^`]*`", "", ln)
            nc = re.sub(r"\bcols=\{\d+\}", "", nc)
            if "{" in nc or "}" in nc:
                err(f"{rel}:{i}: bare '{{' or '}}' outside code — wrap log/format strings in backticks (MDX reads braces as JSX)")

    # unescaped pipe inside a table-cell inline-code span
    for i, ln in enumerate(text.split("\n"), 1):
        if ln.strip().startswith("|"):
            for span in re.finditer(r"`([^`]*)`", ln):
                if re.search(r"(?<!\\)\|", span.group(1)):
                    err(f"{rel}:{i}: unescaped '|' in a table-cell code span — escape it as '\\|' (breaks GFM tables)")

if errors:
    print(f"\n{len(errors)} problem(s) found.")
    sys.exit(1)
print(f"OK: docs.json valid, {len(pages)} pages present, {len(mdx_files)} MDX files well-formed.")
