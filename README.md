# bit2atms — Physical AI Courseware

Open-source, follow-along courses for building intelligent physical systems — from robot manipulation to Vision-Language-Action models.

## Read online

**[Open the reader →](https://unltd0.github.io/bit2atms/reader.html)**

Or clone and open locally:

```bash
git clone https://github.com/unltd0/bit2atms.git
cd bit2atms
python3 -m http.server 8080
# open http://localhost:8080/reader.html
```

> You can also open `reader.html` directly as a file — content will be fetched from GitHub (requires internet).

## Courses

| Course | Topics | Duration |
|---|---|---|
| [VLA — Vision-Language-Action](courses/vla/README.md) | Transforms, MuJoCo, kinematics, RL, imitation learning, VLA models, ROS 2, real hardware | 4–8 weeks |

More courses coming. See [CONTRIBUTING.md](CONTRIBUTING.md) to propose one.

## How it works

1. **Fork** this repo on GitHub
2. Work through a course using the reader
3. Do exercises in your `workspace/` folder
4. Commit your work (or keep it local — up to you)

The `workspace/` folder is your personal scratchpad. It is **not tracked by git** by default (gitignored). To track your progress in your fork, remove the ignore rule:

```bash
# in workspace/.gitignore, delete the line: **
# then:
git add workspace/
git commit -m "start tracking workspace"
```

## Workspace setup

Run once after cloning to create the folder structure and empty placeholder files for every chapter:

```bash
bash scripts/reset_workspace.sh
```

If `workspace/vla/` already has files, the script backs them up to `workspace_old/<timestamp>.zip` before resetting. The backup directory is gitignored — it never gets committed.

As you work through each chapter, copy code from the reader into the corresponding file in your workspace. The reader shows the save path above each code block (e.g. `workspace/vla/ch01/read_robot_state.py`).

## Repo layout

```
bit2atms/
├── reader.html        # Interactive course reader
├── config.json        # Course + chapter manifest
├── courses/
│   └── vla/           # VLA course content (Markdown)
└── workspace/
    └── vla/           # Your exercise files go here
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Content: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
