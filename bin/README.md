# `/dev/bin/` — Template Scripts

This folder is for **template scripts** you can copy and adapt for your projects.

---

## Purpose

The `/dev/bin/` directory provides example executable scripts that demonstrate common development patterns:

- **Build scripts** — Compile and package your extension/container
- **Test runners** — Execute your test suites
- **Development servers** — Start local development environments
- **Deployment scripts** — Deploy to various targets

---

## Usage

1. **Copy a template** to your project directory
2. **Customize** for your specific needs
3. **Make it executable:** `chmod +x your-script.sh`
4. **Run it:** `./your-script.sh`

---

## Template Examples (Coming Soon)

We'll be adding template scripts like:

- `build-extension-template.sh` — Package extension for distribution
- `test-runner-template.sh` — Run tests with proper setup
- `dev-server-template.sh` — Start development server
- `deploy-template.sh` — Deploy to production

---

## Your Scripts

When you create scripts for your own projects, keep them in **your project directory**, not here:

```
dev/
├── bin/              ← Templates (public, tracked)
│   └── README.md
└── my-extension/     ← Your project (private, gitignored)
    └── bin/
        └── build.sh  ← Your actual build script
```

The `.gitignore` ensures your project scripts stay private.

---

## Contributing Templates

If you create useful, generic scripts that others could adapt:

1. **Generalize it** — Remove project-specific details
2. **Add comments** — Explain what each section does
3. **Test thoroughly** — Ensure it works as a template
4. **Submit a PR** — Share with the community

---

**Back to:** [Main README](../README.md) • [Wiki](../wiki/README.md)
