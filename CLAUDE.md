# bit2atms — Physical AI Courseware

Open-source, follow-along courses on Physical AI: robot manipulation, sim-to-real transfer, Vision-Language-Action models, and more.

## Quick links

- **Live site**: https://unltd0.github.io/bit2atms/reader.html
- **Repo**: https://github.com/unltd0/bit2atms

---

## Run locally

```bash
git clone https://github.com/unltd0/bit2atms.git
cd bit2atms
python3 -m http.server 8080
# open http://localhost:8080/reader.html
```

No build step. The reader is a single HTML file that fetches Markdown at runtime.

Alternatively, open `reader.html` directly as a `file://` URL — content is then fetched from `raw.githubusercontent.com` (requires internet).

---

## Publish

Pushing to `main` publishes automatically via GitHub Pages.

```bash
git add .
git commit -m "your message"
git push
```

Changes are live at https://unltd0.github.io/bit2atms/reader.html within ~60 seconds of push.

**GitHub Pages setup** (one-time, already done): Settings → Pages → Source: `main` branch, `/` root. The `.nojekyll` file at repo root ensures `.md` files are served as static assets.

---

## Repo structure

```
bit2atms/
├── reader.html          # Single-file interactive reader (no build needed)
├── config.json          # Course + chapter manifest — the reader's source of truth
├── .nojekyll            # Disables Jekyll so GitHub Pages serves .md files
├── courses/
│   └── vla/             # Vision-Language-Action course
│       ├── OVERVIEW.md
│       ├── README.md    # Full curriculum doc
│       └── ch01_transforms/README.md … ch10_capstone/README.md
└── workspace/
    └── vla/             # Learner scratchpad — ch01_starter.py … ch10_starter.py
```

---

## Adding a course

1. Create `courses/<id>/` with `OVERVIEW.md`, `README.md`, and chapter folders
2. Add an entry to `config.json` under `courses[]` — the reader picks it up automatically
3. Add `workspace/<id>/chXX_starter.py` stubs for each chapter
4. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full walkthrough

### config.json chapter entry shape

```json
{
  "id": "ch01",
  "num": "01",
  "title": "Chapter Title",
  "file": "courses/<id>/ch01_topic/README.md",
  "time": "2–3d",
  "color": "accent"
}
```

Color options: `accent` `accentg` `accentp` `accento` `accenty` `accentr`

---

## Reader details

- **Single HTML file** — `reader.html` at repo root
- **Config-driven** — loads `config.json` at boot, no hardcoded chapter list
- **Environment detection** — auto-switches between relative paths (GitHub Pages / local HTTP) and `raw.githubusercontent.com` URLs (`file://`)
- **Default theme**: paper · **Default font**: sans
- **Themes**: paper, dusk, slate, forest, nord (user-selectable, saved to localStorage)
- **Features**: syntax highlighting, TOC, bookmarks, progress tracking, full-text search, live-reload in local HTTP mode

To change defaults, edit `applyAppearance()` in `reader.html`:

```js
const theme = LS.get('vla_theme', 'paper');   // change 'paper' to any theme id
const font  = LS.get('vla_font',  'sans');    // 'serif' | 'sans' | 'mono'
```

---

## Testing with Playwright MCP

Add the Playwright MCP server to this project in Claude Code:

```bash
claude mcp add playwright -- npx -y @playwright/mcp@latest
```

Then in a Claude Code session, start the local server and ask Claude to test the reader visually — it can navigate chapters, check theming, verify content loads, and screenshot the result.

Example prompts:
- "Start the server on 8080 and check that all 12 chapters load in the reader"
- "Take a screenshot of the reader on chapter 5 and verify the sidebar is correct"
- "Test that the paper theme applies on first load with no localStorage"

---

## Course content guidelines

- Each chapter is a single `README.md` — plain Markdown, no front matter
- YouTube URLs on their own line auto-embed in the reader
- Link liberally to papers, repos, and external docs — this is a curated guide, not a walled garden
- Every chapter should have a **Projects** section pointing learners to `workspace/<course>/chXX_starter.py`
- State hardware requirements explicitly: `Laptop only` / `GPU helpful` / `GPU 8 GB+` / `Physical robot`
