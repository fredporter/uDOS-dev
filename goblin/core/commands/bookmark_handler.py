"""
uDOS v1.2.28 - Bookmark Handler

Handles file bookmark operations:
- List bookmarks with status indicators
- Add bookmarks with optional names and tags
- Remove bookmarks interactively or by name
- Bookmark persistence and validation

Extracted from file_handler.py (v1.2.28 refactor)
"""

from .base_handler import BaseCommandHandler


class BookmarkHandler(BaseCommandHandler):
    """Handles file bookmark operations."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._workspace_manager = None
        self._file_picker = None

    @property
    def workspace_manager(self):
        """Lazy load workspace manager."""
        if self._workspace_manager is None:
            from dev.goblin.core.utils.files import WorkspaceManager
            self._workspace_manager = WorkspaceManager()
        return self._workspace_manager

    @property
    def file_picker(self):
        """Lazy load file picker."""
        if self._file_picker is None:
            from dev.goblin.core.ui.file_picker import FilePicker
            self._file_picker = FilePicker()
        return self._file_picker

    def handle_bookmarks(self, params):
        """
        Manage file bookmarks.
        
        Usage:
            FILE BOOKMARKS              - List all bookmarks
            FILE BOOKMARKS ADD <file>   - Add bookmark
            FILE BOOKMARKS REMOVE <file> - Remove bookmark
        
        Args:
            params: Command parameters (empty for list, ADD/REMOVE + filename)
        
        Returns:
            Status message string
        """
        from dev.goblin.core.input.interactive import InteractivePrompt
        prompt = InteractivePrompt()

        if not params:
            # List bookmarks
            return self._list_bookmarks()

        action = params[0].upper()

        if action == "ADD":
            return self._add_bookmark(params[1:], prompt)
        elif action == "REMOVE":
            return self._remove_bookmark(params[1:], prompt)
        else:
            return f"❌ Unknown bookmark action: {action}\nUse: ADD or REMOVE"

    def _list_bookmarks(self):
        """List all bookmarks with status indicators."""
        bookmarks = self.file_picker.get_bookmarks()

        if not bookmarks:
            return "📚 No bookmarks found\n💡 Use: FILE BOOKMARKS ADD <filename> to add"

        output = "📚 File Bookmarks\n\n"
        for i, bookmark in enumerate(bookmarks, 1):
            exists_icon = "✅" if bookmark['exists'] else "❌"
            name = bookmark['bookmark_name'] or bookmark['file_path']
            tags = f" 🏷️ {', '.join(bookmark['tags'])}" if bookmark['tags'] else ""

            output += (f"{i:2d}. {exists_icon} {name}\n"
                      f"     📁 {bookmark['workspace']}/{bookmark['file_path']}{tags}\n\n")

        output += "💡 Use: FILE BOOKMARKS ADD/REMOVE <filename>"
        return output

    def _add_bookmark(self, params, prompt):
        """Add a file bookmark with optional name and tags."""
        if len(params) < 1:
            # Show file picker
            files = self.workspace_manager.list_files()
            if not files:
                return "❌ No files to bookmark"

            file_choice = prompt.ask_choice(
                "📄 File to bookmark",
                choices=files,
                default=files[0]
            )

            if not file_choice:
                return "❌ Bookmark cancelled"

            filename = file_choice
        else:
            filename = params[0]

        # Ask for bookmark name and tags
        bookmark_name = prompt.ask_text(
            "📝 Bookmark name (optional)",
            default=filename
        )

        tags_input = prompt.ask_text(
            "🏷️ Tags (comma-separated, optional)",
            default=""
        )

        tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]

        success = self.file_picker.add_bookmark(
            filename,
            self.workspace_manager.current_workspace,
            bookmark_name,
            tags
        )

        if success:
            return f"✅ Bookmarked: {filename}"
        else:
            return f"❌ Failed to bookmark: {filename}"

    def _remove_bookmark(self, params, prompt):
        """Remove a file bookmark interactively or by name."""
        if len(params) < 1:
            # Show bookmarks to remove
            bookmarks = self.file_picker.get_bookmarks()
            if not bookmarks:
                return "❌ No bookmarks to remove"

            bookmark_choices = [
                f"{b['bookmark_name'] or b['file_path']} ({b['workspace']})"
                for b in bookmarks
            ]

            choice = prompt.ask_choice(
                "📚 Bookmark to remove",
                choices=bookmark_choices,
                default=bookmark_choices[0]
            )

            if not choice:
                return "❌ Remove cancelled"

            # Extract bookmark info
            selected_index = bookmark_choices.index(choice)
            selected_bookmark = bookmarks[selected_index]
            filename = selected_bookmark['file_path']
            workspace = selected_bookmark['workspace']
        else:
            filename = params[0]
            workspace = self.workspace_manager.current_workspace

        success = self.file_picker.remove_bookmark(filename, workspace)

        if success:
            return f"✅ Removed bookmark: {filename}"
        else:
            return f"❌ Bookmark not found: {filename}"
