# Why This Folder Is Empty

**tl;dr:** `/dev/docs/` should not exist. All documentation lives in `/docs/` at the root level.

---

## Documentation Structure

The `/dev/` submodule is a **scaffold framework only** — it contains no documentation or project content.

**All uDOS documentation lives in:**

```
/docs/                    (Root level, not in /dev/)
├── README.md            # Documentation index
├── ARCHITECTURE-v1.3.md # System architecture
├── roadmaps/            # Project roadmaps (local-only, gitignored)
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
- ✅ Instructions (in `/dev/wiki/`)

---

## Where to Find Documentation

| What You Need | Where It Lives |
|---------------|----------------|
| **System docs** | `/docs/` (root level) |
| **Roadmaps & planning** | `/docs/roadmaps/` (local-only) |
| **How-to guides** | `/docs/howto/` |
| **Using this scaffold** | `/dev/wiki/` |
| **API reference** | `/docs/specs/` |
| **Architecture decisions** | `/docs/decisions/` |

---

## Historical Note

This folder previously contained development documentation that has been:

1. **Moved** to `/docs/` (for current documentation)
2. **Archived** to `/dev/.archive/2026-02-05-docs/` (for historical reference)

The `/dev/` submodule is now framework-only, keeping the public scaffold clean and focused.
