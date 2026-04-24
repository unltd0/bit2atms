# Contributing to bit2atms

## Adding a new course

1. **Create the course folder** under `courses/`:
   ```
   courses/your-course-id/
   ├── OVERVIEW.md
   ├── README.md
   ├── ch01_topic/README.md
   ├── ch02_topic/README.md
   └── ...
   ```

2. **Register it in `config.json`** — add an entry to the `courses` array:
   ```json
   {
     "id": "your-course-id",
     "title": "Your Course Title",
     "description": "One-line description.",
     "chapters": [
       { "id": "overview", "num": "○", "title": "Overview", "file": "courses/your-course-id/OVERVIEW.md" },
       { "id": "ch01", "num": "01", "title": "Chapter Title", "file": "courses/your-course-id/ch01_topic/README.md", "time": "2–3d", "color": "accent" }
     ]
   }
   ```
   Available `color` values: `accent`, `accentg`, `accentp`, `accento`, `accenty`, `accentr`

3. **Add workspace starters** in `workspace/your-course-id/`:
   ```
   workspace/your-course-id/
   ├── ch01_starter.py
   └── ...
   ```

4. Open a PR. The reader picks up the new course automatically from `config.json` — no reader.html changes needed.

## Chapter content guidelines

- Each `README.md` is standalone Markdown — no front matter needed
- Link to external resources freely; embed YouTube URLs on their own line for auto-embed
- Include a "Projects" section with concrete coding tasks pointing to `workspace/` files
- Keep hardware requirements explicit (laptop-only vs GPU vs physical robot)

## Running locally

```bash
python3 -m http.server 8080
# open http://localhost:8080/reader.html
```
