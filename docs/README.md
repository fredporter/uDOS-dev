# Why This Folder Is Mostly Empty

**tl;dr:** `/dev/docs/` stays minimal. Canonical uDOS documentation lives in `/docs/` at the root level.

---

## Documentation Structure

The `/dev/` submodule is a **scaffold framework only** — it contains no documentation or project content.

**All canonical uDOS documentation lives in:**

```
/docs/                    (Root level, not in /dev/)
├── README.md            # Documentation index
├── ARCHITECTURE-v1.3.md # System architecture
├── roadmap-spec/        # Roadmap specs (local-only, gitignored)
├── specs/               # Technical specifications
├── howto/               # How-to guides
├── decisions/           # Architecture Decision Records (ADRs)
├── devlog/              # Development logs
└── ...
```

---

## Why Not `/dev/docs/`?

The `/dev/` submodule is a public, empty scaffold that developers clone to build their own projects. It should **not** contain:

- ❌ uDOS documentation
- ❌ Project roadmaps
- ❌ Development history
- ❌ Specifications

Instead, it provides:

- ✅ Template scripts and tools
- ✅ Example code patterns
- ✅ Build configuration templates
- ✅ Scaffold-only instructions (in `/dev/wiki/`)
- ✅ Dev practices guide used by scaffold consumers

---

## Where to Find Documentation

| What You Need | Where It Lives |
|---------------|----------------|
| **System docs** | `/docs/` (root level) |
| **Roadmap specs** | `/docs/roadmap-spec/` (local-only) |
| **How-to guides** | `/docs/howto/` |
| **Using this scaffold** | `/dev/wiki/` |
| **API reference** | `/docs/specs/` |
| **Architecture decisions** | `/docs/decisions/` |

---

## Dev Practices (Exception)

Scaffold users should read the **Dev Workspace Practices** guide:

- `/dev/wiki/DEV-WORKSPACE-PRACTICES.md`

This is the only dev-practice guide kept in the scaffold layer.

## Historical Note

This folder previously contained development documentation that has been:

1. **Moved** to `/docs/` (for current documentation)
2. **Archived** to `/dev/.archive/2026-02-05-docs/` (for historical reference)

The `/dev/` submodule is now framework-only, keeping the public scaffold clean and focused.
