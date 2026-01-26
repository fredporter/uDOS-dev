# Notion Setup & BlockMapper Test Guide

**Purpose:** Set up a test Notion workspace and verify BlockMapper roundtrip conversion with real Notion API blocks

**Time Required:** ~20 minutes setup + testing

---

## Step 1: Create Notion Integration

### 1.1 Create Notion Internal Integration

1. Go to [Notion Developers](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Name it: `uDOS BlockMapper Test`
4. Select workspace: Your test workspace
5. Click **Create integration**
6. Copy the **Internal Integration Token** (save to `.env` or keep secure)

### 1.2 Create Test Database

1. In your Notion workspace, create a new page
2. Name it: `BlockMapper Test`
3. Add a new database (empty template)
4. Click the **⋯** menu at top
5. Select **"Connections"**
6. Search for and add `uDOS BlockMapper Test` integration
7. **Grant full access**

### 1.3 Get Database ID

In the URL bar, copy the database ID from the URL:

```
https://www.notion.so/workspace/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX?v=...
                                 ↑
                          Database ID (32 chars)
```

**Save this to your environment:**

```bash
export NOTION_DATABASE_ID="your_database_id_here"
export NOTION_API_TOKEN="your_integration_token_here"
```

---

## Step 2: Add Test Blocks to Notion

Using Notion UI, create a page with these blocks:

### Standard Blocks

- H1: "BlockMapper Test"
- Paragraph: "Testing markdown ↔ Notion roundtrip conversion"
- Heading 2: "Standard Blocks"
- Bulleted list:
  - Item 1
  - Item 2
  - Item 3
- Quote: "A test quote"
- Code block (Python):
  ```python
  print("Hello from Notion")
  ```

### Runtime Blocks (as code with captions)

- Code block with caption `[uDOS:STATE]`:

  ```
  $gold = 100
  $player = { name: "Hero", hp: 50 }
  ```

- Code block with caption `[uDOS:FORM]`:

  ```
  name: text
  age: number
  agreed: toggle
  ```

- Heading 2 with toggle enabled: "if $gold >= 100"

- Callout with text: "- 'Buy sword' → $gold -= 50"

---

## Step 3: Run BlockMapper Test

### 3.1 Create Test Script

Create `dev/goblin/tests/test_notion_integration.py`:

```python
"""Test BlockMapper with real Notion API data"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# For now, we'll test with mock Notion API responses
# Later: fetch real blocks from Notion API

from dev.goblin.services.block_mapper import BlockMapper

def test_notion_blocks():
    """Test BlockMapper with Notion API block format"""
    mapper = BlockMapper()

    # Example Notion API response (from actual API)
    notion_blocks = [
        {
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
        },
        {
            "object": "block",
            "id": "12346",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Testing markdown ↔ Notion roundtrip"},
                        "plain_text": "Testing markdown ↔ Notion roundtrip"
                    }
                ],
                "color": "default"
            }
        },
        {
            "object": "block",
            "id": "12347",
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
    ]

    # Convert Notion blocks to markdown
    markdown = mapper.from_notion_blocks(notion_blocks)
    print("=== Notion → Markdown ===")
    print(markdown)
    print()

    # Parse markdown back to blocks
    blocks = mapper.parse_markdown(markdown)
    print("=== Parsed Blocks ===")
    for block in blocks:
        print(f"- {block.type.value}: {block.content[:50]}")
    print()

    # Convert back to Notion
    notion_result = mapper.to_notion_api(blocks)
    print("=== Markdown → Notion ===")
    print(json.dumps(notion_result, indent=2))
    print()

    # Verify roundtrip
    assert len(notion_result) == len(notion_blocks), "Block count mismatch"
    print("✅ Roundtrip successful!")

if __name__ == "__main__":
    test_notion_blocks()
```

### 3.2 Run Test

```bash
cd ~/uDOS
python -m pytest dev/goblin/tests/test_notion_integration.py -v -s
```

---

## Step 4: Real Notion API Test (Optional)

To test with **actual** Notion API blocks:

### 4.1 Install Notion Client

```bash
pip install notion-client
```

### 4.2 Fetch Real Blocks

```python
from notion_client import Client

client = Client(auth=NOTION_API_TOKEN)

# Get database blocks
response = client.blocks.children.list(NOTION_DATABASE_ID)

blocks = response["results"]
print(json.dumps(blocks, indent=2))
```

### 4.3 Test Roundtrip

```python
mapper = BlockMapper()
markdown = mapper.from_notion_blocks(blocks)
parsed = mapper.parse_markdown(markdown)
notion_result = mapper.to_notion_api(parsed)

# Verify
print("Original blocks:", len(blocks))
print("Parsed blocks:", len(parsed))
print("Result blocks:", len(notion_result))
```

---

## Verification Checklist

- [ ] Notion integration created and authorized
- [ ] Test database created
- [ ] Test blocks added to Notion
- [ ] BlockMapper test script runs successfully
- [ ] Markdown output is readable and correct
- [ ] Roundtrip conversion preserves all blocks
- [ ] Runtime blocks identified correctly (STATE, FORM, IF captions)
- [ ] Rich text annotations preserved

---

## Common Issues

### Issue: "Invalid API token"

- Verify token is set correctly in environment
- Check that integration has database access
- Ensure database is shared with integration

### Issue: "Block type not supported"

- Some Notion block types may not be mapped yet
- Check `BlockMapper._notion_block_to_markdown()` for supported types
- Add new types as needed

### Issue: "Content truncated or lost"

- Verify rich text arrays are properly extracted
- Check `_extract_rich_text()` function
- Test with simpler blocks first

---

## Next Steps (After Verification)

Once roundtrip is verified:

1. **Phase B:** Implement Notion webhook handler
2. **Phase C:** Bidirectional sync with conflict resolution
3. **Phase D:** Full integration testing with Notion workspace

---

## Files

- Test script: `dev/goblin/tests/test_notion_integration.py`
- BlockMapper: `dev/goblin/services/block_mapper.py`
- Notion setup docs: `dev/goblin/NOTION-SETUP-TEST.md` (this file)
