# Development Scaffold (`/dev/`)

**Version:** v1.3.0
**Purpose:** Empty scaffold submodule for local development projects
**Last Updated:** 2026-02-05

---

## Overview

`/dev/` is a **public scaffold submodule** — an empty framework structure for developers to use when building their own extensions, containers, or custom projects on top of uDOS.

**This folder contains no projects or future plans.** It's a template structure you clone and populate with your own work.

**All uDOS documentation and roadmaps live in `/docs/` at the root level**, not in this submodule.

### Using This Submodule

The `/dev/` submodule is meant to be cloned into your own workspace as a starting point for:

- **Custom extensions** — Build your own uDOS extensions
- **Container development** — Create new container definitions
- **Local tooling** — Scripts and utilities for your workflows
- **Experimentation** — Test ideas without affecting the core system

**See `/dev/wiki/` for detailed instructions on using this scaffold.**

---

## Key Differences: Directories

| Directory | Purpose | Git Status | Public/Private |
|-----------|---------|------------|----------------|
| `/docs/` (root) | **uDOS documentation & roadmaps** | **Tracked** | Public |
| `/dev/` (submodule) | **Empty scaffold for your projects** | **Tracked** | Public (framework only) |
| `/.dev/` | Local dev notes | **Gitignored** | Private (local only) |
| `/.archive/` | Version history | **Gitignored** | Private (local only) |

**Important:** Your local projects in `/dev/` should be excluded via `/dev/.gitignore` so they stay private while the scaffold structure remains public.

---

## Scaffold Structure

```
dev/
├── README.md           # This file (scaffold guide)
├── wiki/               # ✅ Instructions for using this scaffold
├── scripts/            # ✅ Template scripts for development automation
├── tools/              # ✅ Template utilities
├── examples/           # ✅ Reference code & demos
├── tests/              # ✅ Template test structure
├── build/              # ✅ Build configuration templates
├── .gitignore          # ✅ Excludes your local projects from git
├── .dev/               # ✅ Local experiments (gitignored)
└── .archive/           # ✅ Cold storage (gitignored)
```

**Your Projects Go Here:**
- Clone extensions/containers into `/dev/` subdirectories
- They'll be excluded by `.gitignore` from the public scaffold
- The framework structure remains tracked for others to clone

---

## Quick Start

1. **Clone the submodule** into your workspace (see `/dev/wiki/ADD-SUBMODULE.md`)
2. **Create your project** in a new subfolder (e.g., `/dev/my-extension/`)
3. **Work freely** — your project code is gitignored
4. **Use the templates** in `/dev/scripts/`, `/dev/examples/`, etc.

---

## What This Is NOT

❌ **Not a project repository** — This is an empty scaffold
❌ **Not for uDOS documentation** — See `/docs/` at root level
❌ **Not for uDOS roadmaps** — See `/docs/roadmaps/`
❌ **Not for uDOS development** — This is for YOUR projects

---

## Subdirectory Reference

### `/dev/wiki/` ✅ Instructions
**Purpose:** How-to guides for using this scaffold
**Start here:** `wiki/ADD-SUBMODULE.md`, `wiki/DEVELOP-EXTENSION.md`

### `/dev/scripts/` ✅ Template Scripts
**Purpose:** Example automation scripts you can adapt
**Examples:** Build, test, setup, deployment templates

### `/dev/tools/` ✅ Template Utilities
**Purpose:** Example development utilities
**Examples:** Code generators, analysis tools, build utilities templates

### `/dev/examples/` ✅ Reference Code
**Purpose:** Reference implementations and examples
**Usage:** Copy and adapt for your own projects

### `/dev/tests/` ✅ Template Tests
**Purpose:** Example test structure you can follow

### `/dev/build/` ✅ Build Templates
**Purpose:** Build configuration examples

### `/dev/.dev/` ✅ Local Only
**Status:** Gitignored, local-only experiments
**Usage:** Session notes, WIP, temporary files

### `/dev/.archive/` ✅ Cold Storage
**Status:** Gitignored, historical
**Contains:** Your old versions, deprecated code

---

## Need More Info?

See `/dev/wiki/` for comprehensive guides on:
- Adding this submodule to your workspace
- Creating custom extensions
- Building container definitions
- Working with the uDOS API

---

## 🤝 Contributing & Support

### Contributing
- [**CONTRIBUTING.md**](CONTRIBUTING.md) — How to improve this scaffold
- [**Main uDOS Contributing**](https://github.com/fredporter/uDOS/blob/main/CONTRIBUTORS.md) — Core project contributions
- [**Code of Conduct**](https://github.com/fredporter/uDOS/blob/main/CODE_OF_CONDUCT.md) — Community guidelines

### Getting Help
- [**Report Scaffold Issues**](https://github.com/fredporter/uDOS-dev/issues) — Problems with this scaffold
- [**Report uDOS Issues**](https://github.com/fredporter/uDOS/issues) — Main project bugs/features
- [**Discussions**](https://github.com/fredporter/uDOS/discussions) — Questions and ideas
- [**uDOS Wiki**](https://github.com/fredporter/uDOS/wiki) — Full documentation
