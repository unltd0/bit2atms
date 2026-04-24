# workspace/

This is your personal scratchpad. Create files here as you work through each chapter's projects.

## How to use

1. Fork this repo on GitHub
2. Clone your fork locally
3. Work through a course — each chapter's projects tell you what to build and where to put it
4. Commit your progress if you want to track it, or just keep it local

## Folders

| Folder | Course |
|---|---|
| `vla/` | Vision-Language-Action curriculum |

## Staying in sync with upstream

If you want to pull in new course content from the original repo without overwriting your work:

```bash
git remote add upstream https://github.com/unltd0/bit2atms.git
git fetch upstream
git merge upstream/main --no-edit
# resolve any conflicts in workspace/ in favour of your version
```
