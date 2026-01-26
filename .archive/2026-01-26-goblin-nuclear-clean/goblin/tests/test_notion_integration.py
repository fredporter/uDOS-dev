"""
Test BlockMapper with mock Notion API responses

This allows testing roundtrip conversion without requiring a live Notion account.
After verifying with mocks, can test with real Notion API.
"""

import json
import pytest
from dev.goblin.services.block_mapper import BlockMapper, BlockType


class TestNotionIntegration:
    """Test BlockMapper with Notion API block format"""

    def setup_method(self):
        self.mapper = BlockMapper()

    def test_notion_heading_to_markdown_to_notion(self):
        """Test: Notion heading → markdown → Notion"""
        # Notion API response
        notion_block = {
            "object": "block",
            "id": "12345",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "BlockMapper Test"},
                        "plain_text": "BlockMapper Test"
                    }
                ],
                "color": "default",
                "is_toggleable": False
            }
        }

        # Convert to markdown
        markdown = self.mapper.from_notion_blocks([notion_block])
        assert "# BlockMapper Test" in markdown

        # Parse markdown
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.HEADING_1

        # Convert back to Notion
        notion_result = self.mapper.to_notion_api(blocks)
        assert notion_result[0]["type"] == "heading_1"

    def test_notion_state_block_roundtrip(self):
        """Test: Notion STATE block (code with caption) roundtrip"""
        # Notion API response for STATE block
        notion_block = {
            "object": "block",
            "id": "67890",
            "type": "code",
            "code": {
                "language": "typescript",
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "$gold = 100\n$player = { name: 'Hero' }"},
                        "plain_text": "$gold = 100\n$player = { name: 'Hero' }"
                    }
                ],
                "caption": [
                    {
                        "type": "text",
                        "text": {"content": "[uDOS:STATE]"},
                        "plain_text": "[uDOS:STATE]"
                    }
                ]
            }
        }

        # Convert to markdown
        markdown = self.mapper.from_notion_blocks([notion_block])
        assert "```state" in markdown
        assert "$gold = 100" in markdown

        # Parse markdown
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.STATE

        # Convert back to Notion
        notion_result = self.mapper.to_notion_api(blocks)
        assert notion_result[0]["type"] == "code"
        assert "[uDOS:STATE]" in notion_result[0]["code"]["caption"][0]["plain_text"]

    def test_notion_form_block_roundtrip(self):
        """Test: Notion FORM block roundtrip"""
        notion_block = {
            "object": "block",
            "id": "form123",
            "type": "code",
            "code": {
                "language": "typescript",
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "name: text\nage: number\nagreed: toggle"},
                        "plain_text": "name: text\nage: number\nagreed: toggle"
                    }
                ],
                "caption": [
                    {
                        "type": "text",
                        "text": {"content": "[uDOS:FORM]"},
                        "plain_text": "[uDOS:FORM]"
                    }
                ]
            }
        }

        markdown = self.mapper.from_notion_blocks([notion_block])
        assert "```form" in markdown

        blocks = self.mapper.parse_markdown(markdown)
        assert blocks[0].type == BlockType.FORM

    def test_notion_if_block_roundtrip(self):
        """Test: Notion IF block (toggle heading) roundtrip"""
        notion_block = {
            "object": "block",
            "id": "if456",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "if $gold >= 100"},
                        "plain_text": "if $gold >= 100"
                    }
                ],
                "color": "default",
                "is_toggleable": True
            }
        }

        markdown = self.mapper.from_notion_blocks([notion_block])
        assert "```if" in markdown

        blocks = self.mapper.parse_markdown(markdown)
        assert blocks[0].type == BlockType.IF

    def test_complex_notion_document_roundtrip(self):
        """Test: Complex document with multiple block types"""
        notion_blocks = [
            # H1
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": "Game Title"}, "plain_text": "Game Title"}],
                    "color": "default",
                    "is_toggleable": False
                }
            },
            # Paragraph
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "Introduction text"}, "plain_text": "Introduction text"}],
                    "color": "default"
                }
            },
            # H2
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Setup"}, "plain_text": "Setup"}],
                    "color": "default",
                    "is_toggleable": False
                }
            },
            # STATE code block
            {
                "object": "block",
                "type": "code",
                "code": {
                    "language": "typescript",
                    "rich_text": [{"type": "text", "text": {"content": "$gold = 100"}, "plain_text": "$gold = 100"}],
                    "caption": [{"type": "text", "text": {"content": "[uDOS:STATE]"}, "plain_text": "[uDOS:STATE]"}]
                }
            },
            # Quote
            {
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": [{"type": "text", "text": {"content": "A wise quote"}, "plain_text": "A wise quote"}],
                    "color": "default"
                }
            },
            # Bullet list item
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "Item 1"}, "plain_text": "Item 1"}],
                    "color": "default"
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "Item 2"}, "plain_text": "Item 2"}],
                    "color": "default"
                }
            }
        ]

        # Convert to markdown
        markdown = self.mapper.from_notion_blocks(notion_blocks)

        # Verify key elements
        assert "# Game Title" in markdown
        assert "## Setup" in markdown
        assert "```state" in markdown
        assert "$gold = 100" in markdown
        assert "> A wise quote" in markdown
        assert "- Item 1" in markdown
        assert "- Item 2" in markdown

        # Parse back
        blocks = self.mapper.parse_markdown(markdown)

        # Verify block types
        types = [b.type for b in blocks if b.type != BlockType.PARAGRAPH]
        assert BlockType.HEADING_1 in types
        assert BlockType.HEADING_2 in types
        assert BlockType.STATE in types
        assert BlockType.QUOTE in types
        assert BlockType.BULLETED_LIST_ITEM in types

        # Convert back to Notion
        notion_result = self.mapper.to_notion_api(blocks)
        assert len(notion_result) >= 7  # At least 7 blocks

    def test_all_standard_blocks_notion_roundtrip(self):
        """Test: All standard Notion block types"""
        notion_blocks = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"plain_text": "H1"}], "color": "default", "is_toggleable": False}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"plain_text": "H2"}], "color": "default", "is_toggleable": False}
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"plain_text": "H3"}], "color": "default", "is_toggleable": False}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"plain_text": "Text"}], "color": "default"}
            },
            {
                "object": "block",
                "type": "quote",
                "quote": {"rich_text": [{"plain_text": "Quote"}], "color": "default"}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"plain_text": "Bullet"}], "color": "default"}
            },
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": [{"plain_text": "Number"}], "color": "default"}
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "code",
                "code": {"language": "python", "rich_text": [{"plain_text": "code"}], "caption": []}
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {"rich_text": [{"plain_text": "Note"}], "icon": {"emoji": "📝"}, "color": "default"}
            }
        ]

        markdown = self.mapper.from_notion_blocks(notion_blocks)
        assert "# H1" in markdown
        assert "## H2" in markdown
        assert "### H3" in markdown
        assert "> Quote" in markdown
        assert "- Bullet" in markdown
        assert "1. Number" in markdown
        assert "---" in markdown
        assert "```python" in markdown

        blocks = self.mapper.parse_markdown(markdown)
        notion_result = self.mapper.to_notion_api(blocks)

        assert len(notion_result) >= 9

    def test_runtime_blocks_all_types(self):
        """Test: All 7 runtime block types"""
        runtime_blocks = [
            {
                "object": "block",
                "type": "code",
                "code": {
                    "language": "typescript",
                    "rich_text": [{"plain_text": "$x = 1"}],
                    "caption": [{"plain_text": "[uDOS:STATE]"}]
                }
            },
            {
                "object": "block",
                "type": "code",
                "code": {
                    "language": "typescript",
                    "rich_text": [{"plain_text": "$x += 1"}],
                    "caption": [{"plain_text": "[uDOS:SET]"}]
                }
            },
            {
                "object": "block",
                "type": "code",
                "code": {
                    "language": "typescript",
                    "rich_text": [{"plain_text": "name: text"}],
                    "caption": [{"plain_text": "[uDOS:FORM]"}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"plain_text": "if $x > 0"}],
                    "color": "default",
                    "is_toggleable": True
                }
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"plain_text": "- 'Choice' → action"}],
                    "icon": {"emoji": "🧭"},
                    "color": "blue_background"
                }
            }
        ]

        markdown = self.mapper.from_notion_blocks(runtime_blocks)

        # Verify all runtime types identified
        assert "```state" in markdown
        assert "```set" in markdown
        assert "```form" in markdown
        assert "```if" in markdown

        blocks = self.mapper.parse_markdown(markdown)
        block_types = {b.type for b in blocks}

        assert BlockType.STATE in block_types
        assert BlockType.SET in block_types
        assert BlockType.FORM in block_types
        assert BlockType.IF in block_types


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
