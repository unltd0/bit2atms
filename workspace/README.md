# workspace/

This is your personal scratchpad. Each course has a subfolder here with starter files for every chapter.

## How to use

1. Fork this repo on GitHub
2. Clone your fork locally
3. Work through a course — exercises tell you which file to edit (e.g. `workspace/vla/ch01_starter.py`)
4. Commit your progress if you want to track it, or just keep it local

Your changes to `workspace/` are yours. The starter files in this repo are minimal stubs — replace them completely.

## Folders

| Folder | Course |
|---|---|
| `vla/` | Vision-Language-Action curriculum |

## Staying in sync with upstream

If you want to pull in new course content from the original repo without overwriting your work:

```bash
git remote add upstream https://github.com/OWNER/bit2atms.git
git fetch upstream
git merge upstream/main --no-edit
# resolve any conflicts in workspace/ in favour of your version
```
