#!/usr/bin/env python3
"""
uDOS Credits Sync Tool
Synchronizes library credits from container.json files to wiki/credits.json

Usage:
    python -m core.services.credits_sync          # Sync all credits
    python -m core.services.credits_sync --check  # Check credits status
    python -m core.services.credits_sync --generate-md  # Generate CREDITS.md

This tool scans:
- /library/*/container.json
- /wizard/library/*/container.json

And updates wiki/credits.json and wiki/CREDITS.md

Alpha v1.0.0.68 - 2026-01-07
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


def load_container_json(container_path: Path) -> Optional[Dict[str, Any]]:
    """Load a container.json file."""
    if not container_path.exists():
        return None

    try:
        with open(container_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def scan_library_containers(library_path: Path) -> List[Dict[str, Any]]:
    """Scan a library directory for container.json files."""
    containers = []

    if not library_path.exists():
        return containers

    for item in library_path.iterdir():
        if item.is_dir():
            container_json = item / "container.json"
            data = load_container_json(container_json)

            if data and "container" in data:
                container_info = data["container"]
                metadata = data.get("metadata", {})
                policy = data.get("policy", {})

                containers.append(
                    {
                        "id": container_info.get("id", item.name),
                        "name": container_info.get("name", item.name),
                        "author": metadata.get("maintainer", "Unknown").split(" / ")[0],
                        "license": metadata.get("license", "Unknown"),
                        "license_note": metadata.get("license_note"),
                        "repository": container_info.get("source", ""),
                        "original_repo": metadata.get("original_repo"),
                        "description": container_info.get("description", ""),
                        "location": str(item.relative_to(get_project_root())),
                        "wizard_only": policy.get("wizard_only", False),
                        "version": container_info.get("version"),
                    }
                )

    return containers


def categorize_library(lib: Dict[str, Any]) -> str:
    """Categorize a library based on its properties."""
    lib_id = lib["id"].lower()
    desc = lib["description"].lower()

    # AI/ML
    if any(
        term in lib_id or term in desc
        for term in ["ai", "llm", "gemini", "mistral", "ollama", "ml"]
    ):
        return "ai_ml"

    # Voice/Audio
    if any(
        term in lib_id or term in desc
        for term in ["voice", "tts", "stt", "speech", "audio", "song", "music"]
    ):
        return "voice_audio"

    # Markdown/Documentation
    if any(
        term in lib_id or term in desc
        for term in ["markdown", "md", "pdf", "slide", "presentation", "remark", "marp"]
    ):
        return "markdown_docs"

    # Networking
    if any(
        term in lib_id or term in desc
        for term in ["mesh", "network", "p2p", "transport"]
    ):
        return "networking"

    # Editors
    if any(term in lib_id or term in desc for term in ["editor", "micro", "typo"]):
        return "editors"

    # Games
    if any(term in lib_id or term in desc for term in ["game", "nethack", "roguelike"]):
        return "games"

    # Forms
    if any(term in lib_id or term in desc for term in ["form", "typeform"]):
        return "forms"

    return "other"


def sync_credits() -> Dict[str, Any]:
    """Sync credits from container.json files."""
    root = get_project_root()

    # Scan main library
    main_libs = scan_library_containers(root / "library")

    # Scan wizard library
    wizard_libs = scan_library_containers(root / "wizard" / "library")

    # Categorize main libraries
    categorized: Dict[str, List[Dict]] = {}
    for lib in main_libs:
        category = categorize_library(lib)
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(lib)

    # Build license summary
    license_summary: Dict[str, List[str]] = {}
    all_libs = main_libs + wizard_libs
    for lib in all_libs:
        license_type = lib["license"]
        if license_type not in license_summary:
            license_summary[license_type] = []
        license_summary[license_type].append(lib["id"])

    # Build credits JSON
    credits = {
        "$schema": "./credits.schema.json",
        "meta": {
            "version": "1.0.0",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "description": "Version-controlled credits for uDOS libraries and dependencies",
            "auto_generated": True,
            "source": "core.services.credits_sync",
        },
        "libraries": categorized,
        "wizard_library": wizard_libs,
        "fonts": {
            "system_fonts": [
                {
                    "name": "SF Mono",
                    "purpose": "Code/monospace",
                    "fallbacks": ["Monaco", "Cascadia Code", "Consolas", "monospace"],
                    "license": "System font (Apple)",
                },
                {
                    "name": "SF Pro Text",
                    "purpose": "UI text",
                    "fallbacks": ["system-ui", "sans-serif"],
                    "license": "System font (Apple)",
                },
                {
                    "name": "Avenir",
                    "purpose": "Humanist sans-serif",
                    "fallbacks": ["Helvetica Neue", "sans-serif"],
                    "license": "System font",
                },
                {
                    "name": "Georgia",
                    "purpose": "Old-style serif",
                    "fallbacks": ["Times New Roman", "serif"],
                    "license": "System font (Microsoft)",
                },
            ]
        },
        "retro_influences": [
            {
                "name": "Teletext/Ceefax",
                "era": "1970s-2000s",
                "influence": "Tile-based information display, 40-column layouts, block graphics",
            },
            {
                "name": "BBC Micro",
                "era": "1981",
                "influence": "Mode 7 teletext graphics, educational computing philosophy",
            },
            {
                "name": "Commodore 64",
                "era": "1982",
                "influence": "PETSCII character graphics, retro color palettes",
            },
            {
                "name": "AmigaOS",
                "era": "1985",
                "influence": "Workbench aesthetics, copper bars, four-color schemes",
            },
            {
                "name": "MS-DOS",
                "era": "1981-2000",
                "influence": "Command-line interface patterns, text-mode UI",
            },
            {
                "name": "ANSI Art",
                "era": "1980s-1990s",
                "influence": "Terminal graphics, BBS aesthetic",
            },
        ],
        "groovebox": {
            "description": "Audio synthesis and data transmission using MML (Music Macro Language)",
            "sound_design": {
                "imperial_sounds": {
                    "name": "Imperial Data Transport",
                    "author": "uDOS Team",
                    "license": "Public Domain / CC0",
                    "description": "Dark synth sounds for acoustic data transfer - mathematically generated, no external samples",
                    "influences": [
                        "80s Synthesizer music",
                        "Star Wars Imperial aesthetic",
                        "Dialup modem sounds",
                        "Vocoder effects",
                    ],
                },
            },
            "mml_standard": {
                "name": "Music Macro Language (MML)",
                "license": "Public Domain",
                "description": "Standard music notation format from 1970s-80s home computers",
                "historical_implementations": [
                    "NEC PC-8801 (1981)",
                    "MSX BASIC (1983)",
                    "Sharp X68000 (1987)",
                    "Commodore 64 SID",
                ],
            },
            "scale_data": {
                "name": "Musical Scale Frequencies",
                "license": "Public Domain",
                "description": "Standard A440 tuning with 12-TET temperament",
                "source": "International standard (ISO 16)",
            },
        },
        "license_summary": license_summary,
    }

    return credits


def check_credits() -> bool:
    """Check if credits are up-to-date."""
    root = get_project_root()
    credits_path = root / "wiki" / "credits.json"

    if not credits_path.exists():
        print("❌ wiki/credits.json not found")
        return False

    try:
        with open(credits_path, "r") as f:
            current = json.load(f)
    except (json.JSONDecodeError, IOError):
        print("❌ Could not read wiki/credits.json")
        return False

    # Get current libraries
    current_libs = set()
    for category in current.get("libraries", {}).values():
        for lib in category:
            current_libs.add(lib["id"])
    for lib in current.get("wizard_library", []):
        current_libs.add(lib["id"])

    # Scan for actual libraries
    scanned = sync_credits()
    scanned_libs = set()
    for category in scanned.get("libraries", {}).values():
        for lib in category:
            scanned_libs.add(lib["id"])
    for lib in scanned.get("wizard_library", []):
        scanned_libs.add(lib["id"])

    # Check differences
    missing = scanned_libs - current_libs
    extra = current_libs - scanned_libs

    if missing:
        print(f"⚠️  Libraries not in credits: {', '.join(missing)}")
    if extra:
        print(f"⚠️  Credits for removed libraries: {', '.join(extra)}")

    if not missing and not extra:
        print(f"✅ Credits up-to-date ({len(scanned_libs)} libraries)")
        return True

    print(f"\nRun 'python -m core.services.credits_sync' to update")
    return False


def generate_markdown(credits: Dict[str, Any]) -> str:
    """Generate CREDITS.md from credits JSON."""
    lines = [
        "# uDOS Credits & Acknowledgments",
        "",
        f"**Version:** Alpha v1.0.0.68",
        f"**Last Updated:** {credits['meta']['last_updated']}",
        f"**Auto-Generated:** Yes (by `python -m core.services.credits_sync`)",
        "",
        "This document acknowledges the open-source libraries, fonts, and projects that make uDOS possible.",
        "",
        "---",
        "",
        "## 📚 Library Credits",
        "",
    ]

    category_names = {
        "ai_ml": "AI & Machine Learning",
        "voice_audio": "Voice & Audio",
        "markdown_docs": "Markdown & Documentation",
        "networking": "Networking & Transport",
        "editors": "Text Editors",
        "games": "Games & Entertainment",
        "forms": "Form Tools",
        "other": "Other Libraries",
    }

    for category, libs in credits.get("libraries", {}).items():
        if not libs:
            continue

        cat_name = category_names.get(category, category.replace("_", " ").title())
        lines.append(f"### {cat_name}")
        lines.append("")
        lines.append("| Library | Author | License | Repository | Description |")
        lines.append("|---------|--------|---------|------------|-------------|")

        for lib in libs:
            repo_link = (
                f"[{lib['repository'].split('github.com/')[-1]}]({lib['repository']})"
                if lib["repository"]
                else "-"
            )
            lines.append(
                f"| **{lib['name']}** | {lib['author']} | {lib['license']} | {repo_link} | {lib['description']} |"
            )

        lines.append("")

    # Wizard library
    if credits.get("wizard_library"):
        lines.append("---")
        lines.append("")
        lines.append("## 🧙 Wizard Library Credits")
        lines.append("")
        lines.append("| Library | Author | License | Repository | Description |")
        lines.append("|---------|--------|---------|------------|-------------|")

        for lib in credits["wizard_library"]:
            repo_link = (
                f"[{lib['repository'].split('github.com/')[-1]}]({lib['repository']})"
                if lib["repository"]
                else "-"
            )
            lines.append(
                f"| **{lib['name']}** | {lib['author']} | {lib['license']} | {repo_link} | {lib['description']} |"
            )

        lines.append("")

    # Fonts
    lines.extend(
        [
            "---",
            "",
            "## 📱 Typography & Fonts",
            "",
            "| Font Stack | Purpose | License |",
            "|------------|---------|---------|",
        ]
    )

    for font in credits.get("fonts", {}).get("system_fonts", []):
        fallbacks = ", ".join(font.get("fallbacks", []))
        lines.append(
            f"| **{font['name']}**, {fallbacks} | {font['purpose']} | {font['license']} |"
        )

    lines.append("")

    # Groovebox credits
    if credits.get("groovebox"):
        gb = credits["groovebox"]
        lines.extend(
            [
                "---",
                "",
                "## 🎵 Groovebox Audio Credits",
                "",
                f"{gb.get('description', '')}",
                "",
                "### Sound Design",
                "",
            ]
        )

        if gb.get("sound_design"):
            for key, sound in gb["sound_design"].items():
                lines.append(f"**{sound['name']}**")
                lines.append(f"- Author: {sound['author']}")
                lines.append(f"- License: {sound['license']}")
                lines.append(f"- {sound['description']}")
                if sound.get("influences"):
                    lines.append(f"- Influences: {', '.join(sound['influences'])}")
                lines.append("")

        if gb.get("mml_standard"):
            mml = gb["mml_standard"]
            lines.extend(
                [
                    "### MML Standard",
                    "",
                    f"**{mml['name']}** ({mml['license']})",
                    "",
                    f"{mml['description']}",
                    "",
                    "Historical implementations:",
                ]
            )
            for impl in mml.get("historical_implementations", []):
                lines.append(f"- {impl}")
            lines.append("")

        if gb.get("scale_data"):
            scale = gb["scale_data"]
            lines.extend(
                [
                    "### Musical Standards",
                    "",
                    f"**{scale['name']}** ({scale['license']})",
                    "",
                    f"{scale['description']} ({scale.get('source', '')})",
                    "",
                ]
            )

    # Retro influences
    lines.extend(
        [
            "---",
            "",
            "## 🎨 Retro Style Influences",
            "",
            "| System | Era | Influence on uDOS |",
            "|--------|-----|-------------------|",
        ]
    )

    for influence in credits.get("retro_influences", []):
        lines.append(
            f"| **{influence['name']}** | {influence['era']} | {influence['influence']} |"
        )

    lines.append("")

    # License summary
    lines.extend(
        [
            "---",
            "",
            "## 📜 License Summary",
            "",
            "| License | Libraries |",
            "|---------|-----------|",
        ]
    )

    for license_type, libs in credits.get("license_summary", {}).items():
        lines.append(f"| **{license_type}** | {', '.join(libs)} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 🔄 Maintaining Credits",
            "",
            "Credits are auto-generated from container manifests. To update:",
            "",
            "```bash",
            "# Check credits status",
            "python -m core.services.credits_sync --check",
            "",
            "# Sync credits from containers",
            "python -m core.services.credits_sync",
            "",
            "# Regenerate CREDITS.md",
            "python -m core.services.credits_sync --generate-md",
            "```",
            "",
            "---",
            "",
            "*Part of the [uDOS Wiki](README.md)*",
        ]
    )

    return "\n".join(lines)


def save_credits(credits: Dict[str, Any]) -> bool:
    """Save credits to wiki/credits.json."""
    root = get_project_root()
    credits_path = root / "wiki" / "credits.json"

    try:
        with open(credits_path, "w") as f:
            json.dump(credits, f, indent=2)
        print(f"✅ Saved wiki/credits.json")
        return True
    except IOError as e:
        print(f"❌ Failed to save credits: {e}")
        return False


def save_markdown(markdown: str) -> bool:
    """Save markdown to wiki/CREDITS.md."""
    root = get_project_root()
    md_path = root / "wiki" / "CREDITS.md"

    try:
        with open(md_path, "w") as f:
            f.write(markdown)
        print(f"✅ Saved wiki/CREDITS.md")
        return True
    except IOError as e:
        print(f"❌ Failed to save CREDITS.md: {e}")
        return False


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--check" in args:
        sys.exit(0 if check_credits() else 1)
    elif "--generate-md" in args:
        credits = sync_credits()
        markdown = generate_markdown(credits)
        save_markdown(markdown)
    else:
        # Full sync
        print("🔄 Syncing credits from container manifests...")
        credits = sync_credits()

        lib_count = sum(len(libs) for libs in credits.get("libraries", {}).values())
        wiz_count = len(credits.get("wizard_library", []))

        print(f"   Found {lib_count} library containers")
        print(f"   Found {wiz_count} wizard library containers")

        save_credits(credits)

        markdown = generate_markdown(credits)
        save_markdown(markdown)

        print(f"\n✅ Credits synced successfully")
