---
name: link-to-markdown
description: Use when a user provides a public http/https webpage link and asks to extract or work with the page as Markdown.
---

# Link to Markdown

## Overview

Convert a user-provided URL into Markdown using the markdown conversion MCP tool, then return or save the result in a clean, reusable format.

## Required Input

- A valid `http://` or `https://` URL

## When Not to Use

- Local files, private intranet URLs, or links requiring unavailable authentication
- Non-web assets where direct URL-to-Markdown conversion is not supported

## Workflow

1. Validate input URL
   - Accept only `http` or `https` links.
   - If input is missing or invalid, request a corrected link.

2. Convert URL to Markdown
   - Call the markdown conversion tool with the exact URL.
   - Treat tool output as the source of truth.
   - Retry at most once if the first call fails transiently.

3. Post-process output
   - Remove obvious noise only when needed (empty headings, duplicate separators).
   - Preserve headings, links, and code blocks.

4. Deliver result
   - If user asks for raw output, return Markdown directly.
   - If user asks for a file, save content to a `.md` file in the workspace.
   - Use a deterministic default filename like `page-content.md` when none is provided.
   - If user asks for summary/extraction, perform that task from the converted Markdown.

## Tool Usage

- Use the MCP markdown conversion tool that accepts a URI and returns Markdown.
- Prefer a single conversion call per URL unless retry is required.

## Failure Handling

- If conversion fails due to access limits, auth walls, or unsupported content:
  - Report the failure reason plainly.
  - Ask for an alternate public URL or pasted content.
- If output is too large, provide a concise summary first and offer the full Markdown in a file.

## Output Quality Rules

- Preserve factual fidelity to converted content.
- Do not invent missing sections.
- Keep links and attribution intact where present.
---
## Memory-Bank Reference
See .github/MEMORY-BANK-PATCH.md for repository memory-bank lifecycle and rules.

