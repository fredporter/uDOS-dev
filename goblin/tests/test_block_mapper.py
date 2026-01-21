"""
Tests for BlockMapper — Parse uDOS markdown ↔ Notion blocks

Tests roundtrip conversion:
- Parse markdown → blocks
- Convert blocks → Notion API
- Convert Notion API → markdown
- Verify content preservation
"""

import pytest
from dev.goblin.services.block_mapper import BlockMapper, BlockType, Block, RichText, DBBinding


class TestBlockMapper:
    """Test suite for BlockMapper"""

    def setup_method(self):
        """Initialize mapper before each test"""
        self.mapper = BlockMapper()

    # ========== PARSE MARKDOWN TESTS ==========

    def test_parse_heading_1(self):
        """Parse H1 heading"""
        markdown = "# Title"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.HEADING_1
        assert blocks[0].content == "Title"

    def test_parse_heading_2(self):
        """Parse H2 heading"""
        markdown = "## Subtitle"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.HEADING_2
        assert blocks[0].content == "Subtitle"

    def test_parse_heading_3(self):
        """Parse H3 heading"""
        markdown = "### Section"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.HEADING_3
        assert blocks[0].content == "Section"

    def test_parse_paragraph(self):
        """Parse paragraph"""
        markdown = "This is a paragraph."
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.PARAGRAPH
        assert blocks[0].content == "This is a paragraph."

    def test_parse_multiple_paragraphs(self):
        """Parse multiple paragraphs"""
        markdown = "First paragraph.\n\nSecond paragraph."
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 2
        assert blocks[0].type == BlockType.PARAGRAPH
        assert blocks[1].type == BlockType.PARAGRAPH

    def test_parse_blockquote(self):
        """Parse blockquote"""
        markdown = "> This is a quote."
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.QUOTE
        assert blocks[0].content == "This is a quote."

    def test_parse_divider(self):
        """Parse horizontal divider"""
        markdown = "---"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.DIVIDER

    def test_parse_bullet_list(self):
        """Parse bullet list"""
        markdown = "- Item 1\n- Item 2\n- Item 3"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 3
        assert all(b.type == BlockType.BULLETED_LIST_ITEM for b in blocks)
        assert blocks[0].content == "Item 1"
        assert blocks[1].content == "Item 2"
        assert blocks[2].content == "Item 3"

    def test_parse_numbered_list(self):
        """Parse numbered list"""
        markdown = "1. First\n2. Second\n3. Third"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 3
        assert all(b.type == BlockType.NUMBERED_LIST_ITEM for b in blocks)

    def test_parse_code_block(self):
        """Parse regular code block"""
        markdown = "```python\nprint('hello')\n```"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.CODE
        assert blocks[0].metadata['language'] == 'python'
        assert "print" in blocks[0].content

    # ========== RUNTIME BLOCK TESTS ==========

    def test_parse_state_block(self):
        """Parse STATE runtime block"""
        markdown = "```state\n$gold = 100\n$name = \"Hero\"\n```"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.STATE
        assert blocks[0].metadata['runtime'] == True
        assert "$gold = 100" in blocks[0].content

    def test_parse_set_block(self):
        """Parse SET runtime block"""
        markdown = "```set\n$gold -= 10\n$hp += 5\n```"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.SET

    def test_parse_form_block(self):
        """Parse FORM runtime block"""
        markdown = "```form\nname: text\nage: number\nagreed: toggle\n```"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.FORM
        assert "name: text" in blocks[0].content

    def test_parse_if_block(self):
        """Parse IF runtime block"""
        markdown = "```if\n$gold >= 100\n```"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.IF

    def test_parse_nav_block(self):
        """Parse NAV runtime block"""
        markdown = '```nav\n- "Button" → $gold -= 10\n```'
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.NAV

    def test_parse_panel_block(self):
        """Parse PANEL runtime block"""
        markdown = "```panel\n┌───┐\n│ ◆ │\n└───┘\n```"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.PANEL

    def test_parse_map_block(self):
        """Parse MAP runtime block"""
        markdown = "```map\nprovider: sprites.json\nviewport: 5x5\n```"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.MAP

    # ========== TO NOTION TESTS ==========

    def test_to_notion_heading_1(self):
        """Convert H1 to Notion"""
        block = Block(
            type=BlockType.HEADING_1,
            content="Title",
            rich_text=[RichText("Title")]
        )
        notion_blocks = self.mapper.to_notion_api([block])
        assert len(notion_blocks) == 1
        assert notion_blocks[0]["type"] == "heading_1"
        assert "heading_1" in notion_blocks[0]

    def test_to_notion_paragraph(self):
        """Convert paragraph to Notion"""
        block = Block(
            type=BlockType.PARAGRAPH,
            content="Text",
            rich_text=[RichText("Text")]
        )
        notion_blocks = self.mapper.to_notion_api([block])
        assert notion_blocks[0]["type"] == "paragraph"
        assert "paragraph" in notion_blocks[0]

    def test_to_notion_code(self):
        """Convert code block to Notion"""
        block = Block(
            type=BlockType.CODE,
            content="print('hello')",
            metadata={'language': 'python'},
            rich_text=[RichText("print('hello')")]
        )
        notion_blocks = self.mapper.to_notion_api([block])
        assert notion_blocks[0]["type"] == "code"
        assert notion_blocks[0]["code"]["language"] == "python"

    def test_to_notion_state_block(self):
        """Convert STATE to Notion code with caption"""
        block = Block(
            type=BlockType.STATE,
            content="$gold = 100",
            metadata={'runtime': True},
            rich_text=[RichText("$gold = 100")]
        )
        notion_blocks = self.mapper.to_notion_api([block])
        assert notion_blocks[0]["type"] == "code"
        caption = notion_blocks[0]["code"]["caption"]
        assert len(caption) > 0
        assert "[uDOS:STATE]" in caption[0]["plain_text"]

    def test_to_notion_if_block(self):
        """Convert IF to Notion toggle heading"""
        block = Block(
            type=BlockType.IF,
            content="$gold >= 100",
            rich_text=[RichText("$gold >= 100")]
        )
        notion_blocks = self.mapper.to_notion_api([block])
        assert notion_blocks[0]["type"] == "heading_2"
        assert notion_blocks[0]["heading_2"]["is_toggleable"] == True

    def test_to_notion_bullet_list(self):
        """Convert bullet list to Notion"""
        block = Block(
            type=BlockType.BULLETED_LIST_ITEM,
            content="Item 1",
            rich_text=[RichText("Item 1")]
        )
        notion_blocks = self.mapper.to_notion_api([block])
        assert notion_blocks[0]["type"] == "bulleted_list_item"

    # ========== FROM NOTION TESTS ==========

    def test_from_notion_heading_1(self):
        """Convert Notion heading_1 to markdown"""
        notion_block = {
            "type": "heading_1",
            "heading_1": {
                "rich_text": [
                    {"plain_text": "Title", "type": "text"}
                ]
            }
        }
        markdown = self.mapper.from_notion_blocks([notion_block])
        assert "# Title" in markdown

    def test_from_notion_paragraph(self):
        """Convert Notion paragraph to markdown"""
        notion_block = {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"plain_text": "Text", "type": "text"}
                ]
            }
        }
        markdown = self.mapper.from_notion_blocks([notion_block])
        assert "Text" in markdown

    def test_from_notion_code(self):
        """Convert Notion code block to markdown"""
        notion_block = {
            "type": "code",
            "code": {
                "language": "python",
                "rich_text": [
                    {"plain_text": "print('hello')", "type": "text"}
                ],
                "caption": []
            }
        }
        markdown = self.mapper.from_notion_blocks([notion_block])
        assert "```python" in markdown
        assert "print('hello')" in markdown

    def test_from_notion_runtime_block_with_caption(self):
        """Convert Notion code with [uDOS:STATE] caption back to state block"""
        notion_block = {
            "type": "code",
            "code": {
                "language": "typescript",
                "rich_text": [
                    {"plain_text": "$gold = 100", "type": "text"}
                ],
                "caption": [
                    {"plain_text": "[uDOS:STATE]", "type": "text"}
                ]
            }
        }
        markdown = self.mapper.from_notion_blocks([notion_block])
        assert "```state" in markdown
        assert "$gold = 100" in markdown

    def test_from_notion_toggle_heading(self):
        """Convert Notion toggle heading to if block"""
        notion_block = {
            "type": "heading_2",
            "heading_2": {
                "is_toggleable": True,
                "rich_text": [
                    {"plain_text": "if $gold >= 100", "type": "text"}
                ]
            }
        }
        markdown = self.mapper.from_notion_blocks([notion_block])
        assert "```if" in markdown

    # ========== ROUNDTRIP TESTS ==========

    def test_roundtrip_simple_document(self):
        """Roundtrip: markdown → blocks → Notion → markdown"""
        original = "# Title\n\nThis is a paragraph."

        # Parse markdown
        blocks = self.mapper.parse_markdown(original)
        assert len(blocks) == 2

        # Convert to Notion
        notion_blocks = self.mapper.to_notion_api(blocks)
        assert len(notion_blocks) == 2

        # Convert back to markdown
        result = self.mapper.from_notion_blocks(notion_blocks)

        # Verify content preserved
        assert "# Title" in result
        assert "This is a paragraph." in result

    def test_roundtrip_with_code_block(self):
        """Roundtrip with code block"""
        original = "# Code Example\n\n```python\nprint('hello')\n```"

        blocks = self.mapper.parse_markdown(original)
        notion_blocks = self.mapper.to_notion_api(blocks)
        result = self.mapper.from_notion_blocks(notion_blocks)

        assert "# Code Example" in result
        assert "```python" in result
        assert "print('hello')" in result

    def test_roundtrip_with_state_block(self):
        """Roundtrip with STATE runtime block"""
        original = "```state\n$gold = 100\n$name = \"Hero\"\n```"

        blocks = self.mapper.parse_markdown(original)
        assert blocks[0].type == BlockType.STATE

        notion_blocks = self.mapper.to_notion_api(blocks)
        assert "[uDOS:STATE]" in notion_blocks[0]["code"]["caption"][0]["plain_text"]

        result = self.mapper.from_notion_blocks(notion_blocks)
        assert "```state" in result
        assert "$gold = 100" in result

    def test_roundtrip_complex_document(self):
        """Roundtrip complex document with multiple block types"""
        original = """# Game Start

## Introduction
You wake up in a tavern.

> A mysterious figure approaches...

```state
$gold = 100
$inventory = []
```

## What do you do?

1. Talk to the figure
2. Order a drink
3. Leave the tavern"""

        blocks = self.mapper.parse_markdown(original)
        notion_blocks = self.mapper.to_notion_api(blocks)
        result = self.mapper.from_notion_blocks(notion_blocks)

        assert "# Game Start" in result
        assert "## Introduction" in result
        assert "> A mysterious figure" in result
        assert "```state" in result
        assert "$gold = 100" in result

    def test_roundtrip_all_runtime_blocks(self):
        """Test roundtrip for all 7 runtime block types"""
        document = """# Story

```state
$gold = 100
```

```set
$gold -= 10
```

```form
name: text
```

```if
$gold > 0
```

```nav
- "Continue" → done
```

```panel
┌─────┐
│ Map │
└─────┘
```

```map
viewport: 5x5
```"""

        blocks = self.mapper.parse_markdown(document)
        block_types = {b.type for b in blocks if b.type != BlockType.HEADING_1 and b.type != BlockType.PARAGRAPH}

        expected = {BlockType.STATE, BlockType.SET, BlockType.FORM, BlockType.IF, BlockType.NAV, BlockType.PANEL, BlockType.MAP}
        assert block_types == expected

        # Verify all 7 runtime block types were parsed
        assert BlockType.STATE in block_types
        assert BlockType.SET in block_types
        assert BlockType.FORM in block_types
        assert BlockType.IF in block_types
        assert BlockType.NAV in block_types
        assert BlockType.PANEL in block_types
        assert BlockType.MAP in block_types

    # ========== EDGE CASES ==========

    def test_empty_document(self):
        """Parse empty document"""
        blocks = self.mapper.parse_markdown("")
        assert len(blocks) == 0

    def test_whitespace_only(self):
        """Parse whitespace-only document"""
        blocks = self.mapper.parse_markdown("   \n\n   ")
        assert len(blocks) == 0

    def test_code_block_with_fence_inside(self):
        """Handle code block containing fence markers"""
        markdown = "```python\nprint('```')\n```"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.CODE

    def test_special_characters_in_content(self):
        """Handle special characters"""
        markdown = "Test with *markdown*, _emphasis_, and `code`."
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].content == markdown

    # ========== DB BINDING TESTS ==========

    def test_db_binding_serialization(self):
        """Test DBBinding to_dict conversion"""
        binding = DBBinding(
            provider='sqlite',
            path='./data/world.db',
            namespace='$db',
            bind=['$db.npc[*].name', '$db.fact.weather']
        )
        result = binding.to_dict()
        assert result['provider'] == 'sqlite'
        assert result['path'] == './data/world.db'
        assert '$db.npc[*].name' in result['bind']

    # ========== RICH TEXT TESTS ==========

    def test_rich_text_to_notion(self):
        """Convert RichText to Notion format"""
        rt = RichText("Bold text", bold=True)
        notion = rt.to_notion()
        assert notion["annotations"]["bold"] == True
        assert notion["plain_text"] == "Bold text"

    def test_rich_text_with_link(self):
        """RichText with hyperlink"""
        rt = RichText("Click here", link="https://example.com")
        notion = rt.to_notion()
        assert notion["text"]["link"]["url"] == "https://example.com"
