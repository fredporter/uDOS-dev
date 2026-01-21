"""
API Keys Configuration Section

Manages API keys and credentials (Gemini, GitHub, etc.)
"""

from .base_section import BaseConfigSection
from dev.goblin.core.uDOS_main import get_config


class APIKeysSection(BaseConfigSection):
    """Manages API keys and credentials."""
    
    def handle(self):
        """Interactive API key management (v1.5.0: Uses ConfigManager)."""
        self.clear_screen()
        try:
            # Get ConfigManager instance
            config = get_config()

            # Get current API keys from ConfigManager
            gemini_key = config.get_env('GEMINI_API_KEY', '')
            github_token = config.get_env('GITHUB_TOKEN', '')

            # Show current status
            output = []
            output.append(self.output_formatter.format_panel(
                "API Keys & Credentials",
                f"Gemini API Key: {'✅ Set' if gemini_key else '❌ Not set'}\n"
                f"GitHub Token: {'✅ Set' if github_token else '❌ Not set'}"
            ))

            # Ask what to do
            action = self.input_manager.prompt_choice(
                message="Choose an action:",
                choices=[
                    "Set Gemini API Key",
                    "Set GitHub Token",
                    "View Current Keys (masked)",
                    "Clear API Keys",
                    "Back to Main Menu"
                ],
                default="Back to Main Menu"
            )

            # Handle back to main menu
            if action == "Back to Main Menu":
                return None  # Signal to return to main CONFIG menu

            if action == "Set Gemini API Key":
                new_key = self.input_manager.prompt_user(
                    message="Enter Gemini API Key (or leave blank to skip):",
                    default=gemini_key,
                    required=False
                )
                if new_key:
                    config.set_env('GEMINI_API_KEY', new_key)
                    output.append("\n✅ Gemini API Key updated")
                    output.append("📝 Changes saved to .env")
                else:
                    output.append("\n⚠️ Gemini API Key unchanged")

            elif action == "Set GitHub Token":
                new_token = self.input_manager.prompt_user(
                    message="Enter GitHub Personal Access Token:",
                    default=github_token,
                    required=False
                )
                if new_token:
                    config.set_env('GITHUB_TOKEN', new_token)
                    output.append("\n✅ GitHub Token updated")
                    output.append("📝 Changes saved to .env")
                else:
                    output.append("\n⚠️ GitHub Token unchanged")

            elif action == "View Current Keys (masked)":
                masked_gemini = f"{gemini_key[:8]}...{gemini_key[-4:]}" if len(gemini_key) > 12 else "Not set"
                masked_github = f"{github_token[:8]}...{github_token[-4:]}" if len(github_token) > 12 else "Not set"
                output.append(f"\nGemini API Key: {masked_gemini}")
                output.append(f"GitHub Token: {masked_github}")

            elif action == "Clear API Keys":
                confirm = self.input_manager.prompt_confirm(
                    message="Are you sure you want to clear all API keys?",
                    default=False
                )
                if confirm:
                    config.set_env('GEMINI_API_KEY', '')
                    config.set_env('GITHUB_TOKEN', '')
                    output.append("\n✅ API Keys cleared")
                    output.append("📝 Changes saved to .env")
                else:
                    output.append("\n⚠️ Operation cancelled")

            return "\n".join(output)

        except Exception as e:
            return self.format_error("API key management failed", e)
