#!/usr/bin/env python3
"""
User Config Migration Tool for uDOS v1.0.0.44+

Converts old user.json configs to new schema (v1.0.0).

Usage:
    python scripts/migrate_user_config.py [--dry-run] [--backup]

Options:
    --dry-run   Show changes without applying
    --backup    Create backup before migration

Old Format (uppercase keys):
    {
        "USER_PROFILE": {"NAME": "user", "TIMEZONE": "UTC"},
        "LOCATION_DATA": {"CITY": "Sydney"},
        ...
    }

New Format (lowercase keys):
    {
        "version": "1.0.0",
        "user_profile": {"username": "user", "timezone": "UTC"},
        "location_data": {"city": "Sydney"},
        ...
    }
"""

import json
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.services.user_config import UserConfigManager


def find_user_configs() -> list:
    """Find all user.json files in the workspace."""
    from core.utils.paths import PATHS

    configs = []

    # Primary location
    primary = PATHS.MEMORY_BANK / "user" / "user.json"
    if primary.exists():
        configs.append(primary)

    # Legacy locations
    legacy_paths = [
        PATHS.MEMORY_SYSTEM_USER / "user.json",
        PATHS.MEMORY / "user.json",
        PROJECT_ROOT / "user.json",
    ]

    for path in legacy_paths:
        if path.exists() and path not in configs:
            configs.append(path)

    return configs


def is_old_format(config: dict) -> bool:
    """Check if config uses old uppercase format."""
    # Old format has uppercase keys like USER_PROFILE
    old_keys = ["USER_PROFILE", "LOCATION_DATA", "SPATIAL_DATA", "SESSION_DATA"]
    return any(key in config for key in old_keys)


def migrate_config(
    config_path: Path, dry_run: bool = False, backup: bool = True
) -> dict:
    """
    Migrate a single config file to new format.

    Args:
        config_path: Path to user.json
        dry_run: If True, don't write changes
        backup: If True, create .bak file before migration

    Returns:
        Migration result dict
    """
    result = {
        "path": str(config_path),
        "status": "unknown",
        "old_format": False,
        "migrated": False,
        "backup_path": None,
        "error": None,
    }

    try:
        # Load config
        with open(config_path) as f:
            old_config = json.load(f)

        # Check if migration needed
        if not is_old_format(old_config):
            if "version" in old_config:
                result["status"] = "already_migrated"
                return result
            else:
                result["status"] = "unknown_format"
                return result

        result["old_format"] = True

        # Use UserConfigManager to migrate
        manager = UserConfigManager(config_path)
        new_config = manager._migrate_config(old_config)

        if dry_run:
            result["status"] = "dry_run"
            result["new_config"] = new_config
            return result

        # Create backup
        if backup:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = config_path.with_suffix(f".json.bak-{timestamp}")
            shutil.copy2(config_path, backup_path)
            result["backup_path"] = str(backup_path)

        # Write migrated config
        with open(config_path, "w") as f:
            json.dump(new_config, f, indent=2)

        result["status"] = "migrated"
        result["migrated"] = True

    except json.JSONDecodeError as e:
        result["status"] = "error"
        result["error"] = f"Invalid JSON: {e}"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def main():
    """Main migration entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate user.json to new schema")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without applying"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create backup before migration",
    )
    parser.add_argument(
        "--no-backup", action="store_false", dest="backup", help="Skip backup"
    )
    parser.add_argument("--path", type=Path, help="Specific config file to migrate")

    args = parser.parse_args()

    print("=" * 60)
    print("uDOS User Config Migration Tool v1.0.0.44")
    print("=" * 60)
    print()

    # Find configs to migrate
    if args.path:
        configs = [args.path] if args.path.exists() else []
    else:
        configs = find_user_configs()

    if not configs:
        print("❌ No user.json files found to migrate")
        return 1

    print(f"Found {len(configs)} config file(s):")
    for c in configs:
        print(f"  • {c}")
    print()

    if args.dry_run:
        print("🔍 DRY RUN - No changes will be made")
        print()

    # Migrate each config
    results = []
    for config_path in configs:
        print(f"Processing: {config_path}")
        result = migrate_config(config_path, dry_run=args.dry_run, backup=args.backup)
        results.append(result)

        if result["status"] == "migrated":
            print(f"  ✅ Migrated successfully")
            if result["backup_path"]:
                print(f"  📁 Backup: {result['backup_path']}")
        elif result["status"] == "already_migrated":
            print(f"  ⏭️  Already in new format")
        elif result["status"] == "dry_run":
            print(f"  � Would migrate (old format detected)")
        elif result["status"] == "error":
            print(f"  ❌ Error: {result['error']}")
        else:
            print(f"  ⚠️  Status: {result['status']}")
        print()

    # Summary
    migrated = sum(1 for r in results if r["migrated"])
    errors = sum(1 for r in results if r["status"] == "error")
    skipped = sum(1 for r in results if r["status"] == "already_migrated")

    print("=" * 60)
    print("Summary:")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped:  {skipped}")
    print(f"  Errors:   {errors}")
    print("=" * 60)

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
