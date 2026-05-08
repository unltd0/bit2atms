# bit2atms — Physical AI Courseware

Open-source, follow-along courses on Physical AI: robot manipulation, sim-to-real, VLA models, and more.

## Ground rules

- **Never `git commit` or `git push` without explicit user permission.**
- **Before every commit:** show what's staged and ask for confirmation. Each commit is its own confirmation. "Push" is separate from "commit".

## Quick links

- **Live site**: https://unltd0.github.io/bit2atms/reader.html
- **Repo**: https://github.com/unltd0/bit2atms

## Run locally

```bash
python3 -m http.server 8080  # then open http://localhost:8080/reader.html
```

No build step. `reader.html` fetches Markdown at runtime — over HTTP it uses relative paths, over `file://` it pulls from `raw.githubusercontent.com`.

## Publish

`git push` to `main` → live within ~60s via GitHub Pages. `.nojekyll` at root makes Pages serve `.md` files raw.

## Folder conventions

| Path | Purpose |
|---|---|
| `courses/<id>/chXX/` | Single `README.md` per chapter, plain Markdown, no frontmatter. |
| `courses/<id>/chXX/assets/` | Images **referenced from that chapter's README** via `![alt](assets/x.png)`. Not for student download. |
| `resources/<id>/` | Files students **download or read directly**: Dockerfiles, launch files, SDFs, scripts, layouts. The chapter README can also embed them as collapsible code blocks (see below). |
| `workspace/<id>/` | Bind-mount target. Two roles: (1) student scratchpad, (2) runtime scaffold — files the container needs at startup must be pre-placed. Source-of-truth lives in `resources/<id>/`; `scripts/reset_workspace.sh` copies them in. |

`config.json`: course/chapter manifest. Resource entries must point to a `README.md`, not a raw file (the reader only renders Markdown).

## Reader features used by chapters

The reader extends standard Markdown. Authors should know these:

### Code blocks with file paths

The fenced-code info string accepts a path after the language. Behaviour depends on the path prefix:

| Syntax | Behaviour |
|---|---|
| ` ```python ` | Plain code block. |
| ` ```python my_node.py ` | Plain code block, but header label = `my_node.py`. |
| ` ```python workspace/ros2/ch02/foo.py ` | Inline body, header shows the workspace path (clickable to copy). For "save this file as…" snippets. |
| ` ```python courses/ros2/ch02_simulation/code/foo.py ` | Body fetched from that path, syntax-highlighted, header = filename. For displaying committed source. |
| ` ```python resources/ros2/ground_truth_relay.py ` | Same — fetches and displays the file. Use for any committed file under `resources/`. |

### `+collapsed` flag (default-collapsed code blocks)

Append `+collapsed` to the language token to render the block collapsed by default. Click the header to expand. Works on any code block — inline or file-fetch.

```text
```python+collapsed resources/ros2/ground_truth_relay.py
```
```

Use for long source files referenced from prose ("here's the wiring if you want to see it"), where forcing the reader to scroll past the full file would interrupt the flow.

### Auto-embedded YouTube

A YouTube URL on its own line auto-embeds as an iframe.

## Adding a course

1. Create `courses/<id>/` with `README.md` + chapter folders.
2. Add a `courses[]` entry to `config.json` — title and time are read from the chapter's `README.md`, no need to duplicate.
3. Add `workspace/<id>/` if students need a scratchpad/runtime area.

Chapter entry shape:

```json
{ "id": "ch01", "num": "01", "file": "courses/<id>/ch01_topic/README.md", "color": "accent" }
```

Color options: `accent` `accentg` `accentp` `accento` `accenty` `accentr`.

## Workspace scaffold

`scripts/reset_workspace.sh` creates placeholder files under `workspace/<course>/` and copies runtime files from `resources/<course>/` (the source-of-truth) into `workspace/<course>/`. Update the `*_CHAPTERS` and `ROS2_RESOURCE_FILES` arrays in the script when chapter filenames change or new runtime files are added.

- `bash scripts/reset_workspace.sh` — backup existing workspace, then reset
- `bash scripts/reset_workspace.sh --add-only` — only create missing files
- `FORCE=1 bash scripts/reset_workspace.sh` — reset without backup prompt

## Testing the reader with Playwright

The Playwright MCP is configured. Useful prompts:
- "Start localhost:8080 and screenshot ch02 to verify the embed blocks render collapsed."
- "Navigate every chapter and report any console errors or missing assets."

## Course content guidelines

Per-chapter rules (audience, tone, what to include): [courses/vla/course_guideline_for_claude.md](courses/vla/course_guideline_for_claude.md).

- Each chapter is one `README.md`. Plain Markdown, no frontmatter.
- Link liberally to papers, repos, external docs — this is a curated guide, not a walled garden.
- Every chapter has a **Projects** section pointing students at `workspace/<id>/chXX/`.
- State hardware up front: `Laptop only` / `GPU helpful` / `GPU 8GB+` / `Physical robot`.
