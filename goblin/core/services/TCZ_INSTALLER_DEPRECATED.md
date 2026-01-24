# Goblin TCZ Installer - DEPRECATION NOTICE

**Status:** DEPRECATED  
**Replacement:** Alpine APK Installer  
**Deprecation Date:** 2026-01-24  
**Migration:** See [ADR-0003-alpine-linux-migration.md](../../../docs/decisions/ADR-0003-alpine-linux-migration.md)

---

## ⚠️ This module is archived and no longer maintained.

uDOS has migrated from TinyCore Linux (.tcz packages) to Alpine Linux (.apk packages).

### What Changed

| Component       | Old (TinyCore)    | New (Alpine)          |
| --------------- | ----------------- | --------------------- |
| Package Format  | `.tcz` (squashfs) | `.apk` (APK)          |
| Package Manager | `tce-load`        | `apk add/del`         |
| Build Tool      | `mksquashfs`      | `abuild`              |
| System Type     | TinyCore-specific | Alpine Linux standard |

### Migration Path

If you're using TCZ packages:

1. **Backup** your current system configuration
2. **Boot Alpine Linux** (live USB or ISO)
3. **Install APK packages** instead (see [docs/howto/alpine-install.md](../../../docs/howto/alpine-install.md))
4. **Restore** your data to new system

### Code Status

This file (`dev/goblin/core/services/tcz_installer.py`) is kept for:

- **Historical reference** — Understanding past implementation
- **Compatibility** — Old code may reference TCZ functions
- **Documentation** — Comments explain original design

**Do not use this module for new features.** Use Alpine APK methods instead.

### Related Deprecations

- `dev/goblin/core/commands/install_handler.py` — TCZ installation UI
- `dev/goblin/core/commands/build_handler.py` — TCZ package building UI
- `dev/docs/howto/tinycore-install.md` — TinyCore installation guide
- `dev/docs/howto/tinycore-vm-test.md` — TinyCore VM testing guide

All have been marked deprecated with references to Alpine alternatives.

---

## What to Use Instead

### Package Installation

```python
# OLD (TinyCore)
from dev.goblin.core.services.tcz_installer import TCZInstaller
installer = TCZInstaller()
result = installer.install("udos-core.tcz")

# NEW (Alpine)
from core.os_specific import get_os_adapter
adapter = get_os_adapter()
success, msg = adapter.install_package("udos-core")
```

### Package Building

```python
# OLD (TinyCore)
from dev.goblin.core.services.tcz_installer import build_tcz_package()

# NEW (Alpine)
from wizard.services.plugin_factory import APKBuilder
builder = APKBuilder()
result = builder.build_apk("udos-core")
```

### System Detection

```python
# OLD (TinyCore)
from dev.goblin.core.utils.paths import is_tinycore()

# NEW (Alpine)
from core.services.os_detector import is_alpine, get_os_detector
if is_alpine():
    # Do Alpine-specific operation
```

---

## References

- **ADR:** [docs/decisions/ADR-0003-alpine-linux-migration.md](../../../docs/decisions/ADR-0003-alpine-linux-migration.md)
- **Alpine Install:** [docs/howto/alpine-install.md](../../../docs/howto/alpine-install.md)
- **Alpine Spec:** [dev/roadmap/alpine-core.md](../../../dev/roadmap/alpine-core.md)
- **OS Detector:** [core/services/os_detector.py](../../../core/services/os_detector.py)
- **APK Adapters:** [core/os_specific/](../../../core/os_specific/)

---

_Last Maintained: 2026-01-24_  
_Archive Recommendation: Move to `.archive/2026-01/tcz_installer.py` if no longer referenced_
