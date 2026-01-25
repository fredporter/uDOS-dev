"""
uDOS Editor Manager
Handles CLI and web-based editor detection, installation, and configuration.
"""

import os
import sys
import json
import shutil
import subprocess
import platform
import urllib.request
import tarfile
import zipfile
from pathlib import Path


class EditorManager:
    """Manages text editors for uDOS CLI and web modes."""

    def __init__(self, user_data_path=None):
        from dev.goblin.core.utils.paths import PATHS

        if user_data_path is None:
            user_data_path = PATHS.MEMORY_BANK / "user/user.json"
        self.user_data_path = user_data_path
        self.library_dir = PATHS.ROOT / "library"
        self.extensions_dir = Path("extensions")
        self.native_dir = self.extensions_dir / "native"
        self.web_dir = self.extensions_dir / "web"

        # Ensure directories exist
        self.native_dir.mkdir(parents=True, exist_ok=True)
        self.web_dir.mkdir(parents=True, exist_ok=True)

    def detect_available_editors(self):
        """
        Detect all available text editors on the system.

        Returns:
            dict: Available editors by category
        """
        available = {"CLI": [], "WEB": []}

        # Check for CLI editors
        cloned_dir = self.extensions_dir / "cloned"
        library_micro = [
            self.library_dir / "micro" / "micro",
            self.library_dir / "micro" / "bin" / "micro",
        ]
        cli_editors = [
            ("micro", library_micro[0]),  # Preferred: /library/micro
            ("micro-alt", library_micro[1]),
            ("micro-clone", cloned_dir / "micro" / "micro"),  # Legacy clone
            ("nano", "nano"),  # System (always available)
        ]

        for name, path in cli_editors:
            if self._is_available(path):
                if name == "micro" or name == "micro-alt" or name == "micro-clone":
                    if "micro" not in available["CLI"]:
                        available["CLI"].append("micro")
                else:
                    available["CLI"].append(name)

        # Check for web editors
        web_editors = [
            ("typo", self.web_dir / "typo" / "package.json"),
        ]

        for name, indicator_file in web_editors:
            if Path(indicator_file).exists():
                available["WEB"].append(name)

        return available

    def _is_available(self, path):
        """Check if editor is available."""
        if isinstance(path, Path):
            # Custom installation path
            return path.exists() and os.access(path, os.X_OK)
        else:
            # System command
            return shutil.which(path) is not None

    def get_preferred_editor(self, mode="CLI"):
        """
        Get user's preferred editor for specified mode.
        Checks both .env file and user.json preferences.

        Args:
            mode (str): 'CLI' or 'WEB'

        Returns:
            str: Editor name or None
        """
        # First check .env file (new method)
        if mode == "CLI":
            env_editor = os.environ.get("CLI_EDITOR")
            if env_editor:
                return env_editor.lower()
        elif mode == "WEB":
            env_editor = os.environ.get("WEB_EDITOR")
            if env_editor:
                return env_editor.lower()

        # Fallback to user.json (legacy method)
        try:
            with open(self.user_data_path, "r") as f:
                user_data = json.load(f)

            prefs = user_data.get("EDITOR_PREFERENCES", {})

            if mode == "CLI":
                return prefs.get("CLI_EDITOR")
            elif mode == "WEB":
                return prefs.get("WEB_EDITOR")
            else:
                return prefs.get("DEFAULT_MODE", "CLI")

        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None

    def set_preferred_editor(self, editor_name, mode="CLI"):
        """
        Set user's preferred editor.

        Args:
            editor_name (str): Name of the editor
            mode (str): 'CLI' or 'WEB'
        """
        try:
            with open(self.user_data_path, "r") as f:
                user_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            user_data = {}

        if "EDITOR_PREFERENCES" not in user_data:
            user_data["EDITOR_PREFERENCES"] = {
                "DEFAULT_MODE": "CLI",
                "CLI_EDITOR": None,
                "WEB_EDITOR": None,
                "AUTO_INSTALL": True,
            }

        if mode == "CLI":
            user_data["EDITOR_PREFERENCES"]["CLI_EDITOR"] = editor_name
        elif mode == "WEB":
            user_data["EDITOR_PREFERENCES"]["WEB_EDITOR"] = editor_name

        with open(self.user_data_path, "w") as f:
            json.dump(user_data, f, indent=2)

    def get_best_editor(self, mode="CLI"):
        """
        Get the best available editor based on preferences and availability.

        Args:
            mode (str): 'CLI' or 'WEB'

        Returns:
            tuple: (editor_name, editor_path)
        """
        available = self.detect_available_editors()
        preferred = self.get_preferred_editor(mode)

        if mode == "CLI":
            # Check if preferred editor is available
            if preferred and preferred in available["CLI"]:
                return (preferred, self._get_editor_path(preferred))

            # Fallback priority: micro > nano
            # micro is preferred - advanced features, nano is reliable fallback
            priority = ["micro", "nano"]
            for editor in priority:
                if editor in available["CLI"]:
                    return (editor, self._get_editor_path(editor))

            # Last resort - use EDITOR env var or vi
            env_editor = os.environ.get("EDITOR", "vi")
            return (env_editor, env_editor)

        elif mode == "WEB":
            if preferred and preferred in available["WEB"]:
                return (preferred, None)  # Web editors don't have simple paths

            if "typo" in available["WEB"]:
                return ("typo", None)

            return (None, None)

    def _get_editor_path(self, editor_name):
        """Get the full path to an editor."""
        if editor_name == "micro":
            library_paths = [
                self.library_dir / "micro" / "micro",
                self.library_dir / "micro" / "bin" / "micro",
            ]
            for path in library_paths:
                if path.exists():
                    return str(path.absolute())

        # Check cloned micro first
        cloned_dir = self.extensions_dir / "cloned"
        cloned_path = cloned_dir / editor_name / editor_name
        if cloned_path.exists():
            return str(cloned_path.absolute())  # Return absolute path

        # Check custom installation in native
        custom_path = self.native_dir / editor_name / editor_name
        if custom_path.exists():
            return str(custom_path.absolute())  # Return absolute path

        # Check system
        return shutil.which(editor_name) or editor_name

    def install_micro(self, force=False):
        """
        Install micro editor from cloned repository.

        Args:
            force (bool): Force reinstallation

        Returns:
            bool: Success status
        """
        cloned_dir = self.extensions_dir / "cloned"
        micro_dir = cloned_dir / "micro"
        micro_bin = micro_dir / "micro"

        # Check if already built
        if micro_bin.exists() and not force:
            print("✅ micro is already installed")
            return True

        # Check if cloned directory exists
        if not micro_dir.exists():
            print("❌ Micro source not found in extensions/cloned/micro")
            print(
                "💡 Clone it with: git clone https://github.com/zyedidia/micro extensions/cloned/micro"
            )
            return False

        print("🔨 Building micro editor from source...")

        try:
            # Use make to build micro
            build_result = subprocess.run(
                ["make", "build"],
                cwd=str(micro_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )

            urllib.request.urlretrieve(url, download_path)
            print("✅ Download complete")

            # Extract
            print("📂 Extracting...")
            micro_dir.mkdir(parents=True, exist_ok=True)

            if filename.endswith(".tar.gz"):
                with tarfile.open(download_path, "r:gz") as tar:
                    tar.extractall(self.native_dir)

                # Move from extracted directory to micro/
                extracted_dir = self.native_dir / f"micro-{version}"
                if extracted_dir.exists():
                    # Move micro binary
                    src_bin = extracted_dir / "micro"
                    if src_bin.exists():
                        shutil.move(str(src_bin), str(micro_bin))
                        os.chmod(micro_bin, 0o755)

                    # Clean up
                    shutil.rmtree(extracted_dir)

            if build_result.returncode == 0:
                print("✅ Micro built successfully!")
                print(f"📍 Location: {micro_bin}")

                # Verify binary exists
                if micro_bin.exists():
                    # Make executable
                    os.chmod(micro_bin, 0o755)

                    # Set as preferred editor
                    self.set_preferred_editor("micro", "CLI")
                    return True
                else:
                    print("❌ Build succeeded but binary not found")
                    return False
            else:
                print(f"❌ Build failed: {build_result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Build timed out after 120 seconds")
            return False
        except FileNotFoundError:
            print("❌ 'make' command not found. Install build tools first.")
            return False
        except Exception as e:
            print(f"❌ Build failed: {e}")
            return False

    def open_file(self, filepath, mode=None, editor=None, typo_port=5173):
        """
        Open a file with the appropriate editor.

        Args:
            filepath (str): Path to file to edit
            mode (str): 'CLI' or 'WEB' (None = auto-detect from preferences)
            editor (str): Specific editor to use (overrides detection)
            typo_port (int): Legacy parameter, ignored (external app used instead)

        Returns:
            int: Return code from editor
        """
        # Determine mode
        if mode is None:
            try:
                with open(self.user_data_path, "r") as f:
                    user_data = json.load(f)
                mode = user_data.get("EDITOR_PREFERENCES", {}).get(
                    "DEFAULT_MODE", "CLI"
                )
            except:
                mode = "CLI"

        # Get editor
        if editor:
            editor_path = self._get_editor_path(editor)
        else:
            editor_name, editor_path = self.get_best_editor(mode)

            if mode == "CLI" and editor_path is None:
                print("❌ No CLI editor available")
                return 1

        # Open file
        if mode == "CLI":
            try:
                return subprocess.run([editor_path, filepath]).returncode
            except Exception as e:
                print(f"❌ Failed to open editor: {e}")
                return 1

        elif mode == "WEB":
            # Use external Typo Tauri app (v1.2.31+)
            return self._open_in_typo_app(filepath)

    def _open_in_typo_app(self, filepath):
        """
        Open file in external Typo Tauri application.

        Args:
            filepath (str): Path to file to edit

        Returns:
            int: 0 on success, 1 on failure
        """
        # Check for Typo app installation
        typo_app_path = Path(
            "extensions/typo-tauri/src-tauri/target/universal-apple-darwin/release/bundle/macos/Typo.app"
        )

        if not typo_app_path.exists():
            # Try release build location
            typo_app_path = Path(
                "extensions/typo-tauri/src-tauri/target/release/bundle/macos/Typo.app"
            )

        if not typo_app_path.exists():
            print("❌ Typo app not found. Build it with:")
            print("   cd extensions/typo-tauri && npx tauri build")
            print("\n📝 Falling back to CLI editor...")
            editor_name, editor_path = self.get_best_editor("CLI")
            if editor_path:
                return subprocess.run([editor_path, filepath]).returncode
            return 1

        # Convert to absolute path
        abs_filepath = Path(filepath).absolute()

        try:
            # Launch Typo app with file argument
            # macOS: Use 'open' command with --args to pass file path
            result = subprocess.run(
                ["open", "-n", str(typo_app_path), "--args", str(abs_filepath)],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print(f"✅ Opened in Typo: {abs_filepath}")
                return 0
            else:
                print(f"❌ Failed to launch Typo: {result.stderr}")
                return 1

        except Exception as e:
            print(f"❌ Error launching Typo: {e}")
            return 1
