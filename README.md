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
| [VLA — Vision-Language-Action](courses/vla/OVERVIEW.md) | Transforms, MuJoCo, kinematics, RL, imitation learning, VLA models, ROS 2, real hardware | 4–8 weeks |

More courses coming. See [CONTRIBUTING.md](CONTRIBUTING.md) to propose one.

## How it works

1. **Fork** this repo on GitHub
2. Work through a course using the reader
3. Do exercises in your `workspace/` folder
4. Commit your work (or keep it local — up to you)

The `workspace/` folder is your personal scratchpad. It's tracked by git so you can commit progress if you want, or just leave it local.

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
