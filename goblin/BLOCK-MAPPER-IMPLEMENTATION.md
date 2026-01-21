# BlockMapping Implementation Plan

_This specification ensures TypeScript and Python runtimes are compatible, enabling code reuse across platforms._---- ADR-0002: `/docs/decisions/ADR-0002-typescript-runtime-for-mobile.md`- Notion compatibility: `/docs/specs/notion-compatible-blocks.md`- TypeScript brief: `/dev/roadmap/typescript.md`- SQLite schema: `/dev/roadmap/example-sqlite.db.md`- Example scripts: `/dev/roadmap/example-script.md`, `/dev/roadmap/movement-demo-script.md`## References---| `core/docs/MIGRATION.md` | From Python runtime → TS || `core/docs/TESTING.md` | Unit + integration tests || `core/docs/EXAMPLES.md` | Example scripts + patterns || `core/docs/DATABASE-BINDING.md` | DB connection + queries || `core/docs/STATE-MODEL.md` | Variables + data types || `core/docs/BLOCKS.md` | Block types + syntax || `core/docs/TYPESCRIPT-RUNTIME.md` | Main runtime spec || --- | --- || Document | Purpose |When TypeScript runtime is implemented in v1.0.3.0, create:## Standards for `/core/docs/`---4. **Complex State** — Objects + arrays (game-state.md)3. **Data-Driven NPC** — DB-backed narrative (merchant-db-lookup.md)2. **Movement Demo** — Sprites + map blocks (movement-demo-script.md)1. **Simple Story** — Text + conditionals (garden.md)### Example Workflows`- test_state_persistence- test_db_variables_available- test_conditional_blocks_hide_show- test_form_submission_triggers_set- test_full_document_load_and_render# test_document_execution.py`python### Integration Tests`- test_db_binding_resolution- test_interpolation_text- test_nav_button_gate_evaluation- test_if_condition_evaluation- test_form_parse_fields- test_set_commands_mutations- test_state_parse_objects_arrays- test_state_parse_simple_variables# test_runtime_blocks.py`python### Unit Tests## Testing Strategy---- **Persistent state** — Auto-save to device SQLite- **Web API binding** — Read-only REST endpoints- **More DB providers** — MySQL, PostgreSQL, Notion API- **Operators** — Math (`+`, `-`, `*`, `/`), String concat- **Computed properties** — `$player.total_items = len($inventory)`- **Array iteration** — `for $item in $array`## Future Extensions (v1.0.4.0+)---- Tile adjacency lookup- Sprite movement with MAP blocks- Forms, conditionals, navigation- External DB binding- State initializationSee `/dev/roadmap/example-script.md` for full example with:## Example: Complete Interactive Story---`5. Navigate to next section (if nav)4. Persist state (to SQLite if available)3. Re-render affected sections2. Execute SET block (if associated)1. User fills form or clicks nav button`### User Action (Mobile)`5. Show interactive elements (form, nav)   - Render graphics (panel, map)   - Hide unavailable options (nav when gates)   - Evaluate conditionals (if/else)   - Interpolate variables in text4. Render document:3. Execute all STATE blocks (top to bottom)2. Load DB bindings (if configured)1. Parse frontmatter (title, db config, state defaults)`### Document Load## Execution Flow---`inc $coins $db.fact.starting_goldset $name $db.npc.merchant.name`set`markdownVariables work in runtime blocks:### Code Block Interpolation`} }); return String(value); if (typeof value === 'object') return JSON.stringify(value); if (value === null) return match; const value = resolveVariable(state, db, path); return text.replace(/\$([a-zA-Z_]a-zA-Z0-9*.[\]]*)/g, (match, path) => {function interpolateText(text: string, state: RuntimeState, db: DBConnection[]): string {`typescript**Implementation:**`Merchant: $db.npc.merchant.nameWeather: $db.fact.weatherFrom the database:HP: $player.hp / 100You have $coins coins.# Hello, $name!```markdownVariables can appear in normal Markdown:### Text Interpolation## Interpolation Rules---```]  { id: "poi_garden", ch: "🌿", z: 1, pos: { tile: "AA340-101", layer: 300 } }  { id: "npc_1", ch: "G", z: 5, pos: { tile: "AA339-100", layer: 300 } },  { id: "player", ch: "@", z: 10, pos: { tile: "AA340-100", layer: 300 } },$sprites = [`` javascript**Expected Sprite Format:**- `sprites` — Variable containing sprite array- `show` — What to render- `style` — 'teletext' | 'ascii' | 'unicode'- `viewport` — Size (columns x rows)- `layer` — Which layer to render- `center` — Tile to center on**Configuration:** ``sprites: $sprites  labels: false  sprites: true  terrain: trueshow:style: teletextviewport: "20x10"layer: $player.pos.layercenter: $player.pos.tile```map```markdown### 7. MAP — Render Viewport with Sprites- Static (no interaction)- Multi-column layout- ASCII box drawing (Unicode)- Variable interpolation inside block**Features:**```Panel divider (row split)█████████ @    █████████**[MAP]**---Key: $has_keyCoins: $coinsHP: $player.hp / 100**[STATS]**```panel cols=2```markdown### 6. PANEL — ASCII/Teletext Graphics- Mobile: Full-width button column- Desktop: Button list**Rendering:**- `when` (optional) — Condition to show button- `to` — Target anchor (section ID)- `label` — Display text**Properties:**```  when: "$coins >= 10 and $has_key == true"  to: "#market"- label: "Enter Market District"    when: "$db.npc.merchant.name != null" to: "#merchant"- label: "Talk to the Merchant" to: "#garden"- label: "Visit the Garden (find items)"`nav`markdown### 5. NAV — Navigation Choices`}  execute(ifContent: string, elseContent?: string, state: RuntimeState): string  evaluate(condition: ASTNode, state: RuntimeState): boolean  parseCondition(expr: string): ASTNodeinterface IfBlockExecutor {`typescript**Implementation:**- Renders only matching block (not both)- Conditions: `==`, `!=`, `<`, `>`, `<=`, `>=`, `and`, `or`- `else` must immediately follow `if`**Rules:**`The gate is locked. You need a key and 10 coins.`else`markdownelse (optional)`...content...## You enter the Market DistrictYou have enough coins and a key. The gate opens.`if $coins >= 10 and $has_key == true`markdown### 4. IF/ELSE — Conditionals- Android: Jetpack Compose- iOS: SwiftUI Forms- Desktop: HTML form**Mobile Rendering:**| `checkbox` | Multi-select | `string[]` || `choice` | Radio/dropdown | `string` (one of options) || `toggle` | Checkbox | `boolean` || `number` | Number slider/input | `number` || `text` | String input | `string` || --- | --- | --- || Type | Input | Output |**Types:**`  options: ["work", "personal", "hobby"]  label: "Category"  type: choice- var: $category  label: "Do you have the key?"  type: toggle- var: $has_key  max: 1000  min: 0  label: "Starting coins"  type: number- var: $coins  placeholder: "Traveller"  required: true  label: "Your name"  type: text- var: $name`form`markdown### 3. FORM — Collect Input`} validateCommand(cmd: string): boolean execute(commands: string[], state: RuntimeState): RuntimeStateinterface SetBlockExecutor {`` typescript**Implementation:**| `pop $var` | Array pop | `pop $inventory` || `push $var value` | Array append | `push $inventory apple` || `toggle $var` | true ↔ false | `toggle $has_key` || `dec $var n` | Subtract n | `dec $hp 10` || `inc $var n` | Add n | `inc $coins 5` || `set $var value` | Assign literal | `set $coins 100` || --- | --- | --- || Command | Behavior | Example |**Commands:** ``toggle $has_keydec $hp 5inc $hp 10set $coins 100```set```markdown### 2. SET — Controlled Mutations```}  merge(existing: RuntimeState, defaults: RuntimeState, mode: 'preserve' | 'overwrite'): RuntimeState  parse(content: string): RuntimeStateinterface StateBlockExecutor {```typescript**Implementation:**- Cannot reference other variables (yet)- Complex values (objects, arrays) supported- Respects `stateDefaults: preserve | overwrite` frontmatter- Evaluated top-to-bottom at document start**Rules:**```}  sprite: { ch: "@", z: 10 }  pos: { tile: "AA340-100", layer: 300 },  id: "player_1",$player = {$inventory = []$coins = 0$hp = 100$name = "Traveller"`state`markdown### 1. STATE — Initialize Variables## Runtime Blocks (v0)---```} return null; } } return await db.resolve(varPath); if (varPath.startsWith(db.namespace)) { for (const db of dbConnections) { // Check DB bindings ($db.*, $notion.*, etc)    }    return state[varPath.slice(1)];  if (varPath.startsWith('$') && !varPath.includes('.')) { // Try local state first): Promise<RuntimeValue> { varPath: string dbConnections: DBConnection[], state: RuntimeState,async function resolveVariable(// In state resolution:} resolve(path: string): Promise<RuntimeValue | null> // Resolve a variable path async load(): Promise<void> // Load initial bindings cache: Map<string, RuntimeValue> namespace: string provider: 'sqlite' | 'notion'interface DBConnection {`typescript### Runtime DB Access` - var: "$notion.tasks"      # Filtered view      - var: "$notion.npc" # All rows from DB bind: namespace: "$notion"    database_id: "..." # Notion database UUID    page_id: "..." # Notion page UUID    provider: notion  db:data:```yaml#### 2. Notion (Future, v1.0.4.0+)```// $db.poi.where("kind = 'garden'")[0].note// $db.npc.where("tile = 'AA340-100'")// With WHERE (future):$db.npc // → SELECT * FROM npc → [{id, name, bio, tile, layer}, ...]// Full table:$db.npc[*].name // → SELECT name FROM npc → [...]// All NPC names:$db.fact.weather  // → SELECT value FROM facts WHERE key='weather'// Single fact:```typescript**Binding Examples**:```);  PRIMARY KEY (layer, from_tile, dir)  to_tile TEXT,  dir TEXT,       -- 'N', 'S', 'E', 'W'  from_tile TEXT,  layer INTEGER,CREATE TABLE tile_edges (-- Tile adjacency (movement support));  note TEXT  layer INTEGER,  tile TEXT,  kind TEXT,      -- 'garden', 'market', 'landmark'  name TEXT,  id TEXT PRIMARY KEY,CREATE TABLE poi (-- Points of Interest);  layer INTEGER  tile TEXT,  bio TEXT,  name TEXT NOT NULL,  id TEXT PRIMARY KEY,CREATE TABLE npc (-- NPCs (structured data));  value TEXT NOT NULL  key TEXT PRIMARY KEY,CREATE TABLE facts (-- Facts (key/value)```sql**Schema Example** (example.sqlite.db):```      - var: "$db.npc" # Full table - var: "$db.npc[*].name"        # All rows, name field      - var: "$db.fact.weather" # Single row bind: namespace: "$db"    path: "./data/example.sqlite.db"    provider: sqlite  db:data:```yaml#### 1. SQLite (Local, read-only v0)### Supported Providers```---      - var: "$db.poi[*]" - var: "$db.npc[*].name"      - var: "$db.fact.weather" bind: namespace: "$db"    path: "./data/world.sqlite.db"    provider: sqlite  db:data:stateDefaults: "preserve"  # or 'overwrite'mode: "presentation"  # or 'interactive'runtime: "udos-ts-runtime"version: "1.0"id: "story-123"title: "Interactive Story"---```markdownDocuments can declare external data sources:### Configuration (YAML Frontmatter)## Database Binding---```}  return value;  }    }      return null;    } else {      value = value[part];    if (typeof value === 'object' && value !== null) {  for (const part of parts) {  let value: RuntimeValue = state;  const parts = path.split(/\.|\[|\]/).filter(p => p);function resolvePath(state: RuntimeState, path: string): RuntimeValue {// Runtime implementation:$db.npc.merchant.name // DB binding (read-only)$player.inventory[0].qty // Nested$inventory[0] // Array index$player.hp               // Object property// Valid paths:```typescript### Path Access (Dot + Bracket Notation)```  $db.npc.merchant.name  $db.fact.weather  $player.inventory[0].name  $player.hp  $player  $nameExamples:$[a-zA-Z*][a-zA-Z0-9_]\*`### Variable Naming`} [varName: string]: RuntimeValueinterface RuntimeState { | RuntimeValue[] // array | { [key: string]: RuntimeValue } // object | null | boolean | number | stringtype RuntimeValue = ```typescript### Variable Types## State Model---5. **Deterministic Execution** — Same input → same output (no loops, no functions)4. **Variable Interpolation** — `$var` in text and code blocks3. **Runtime Blocks** — Executable: `state`, `set`, `form`, `if/else`, `nav`, `panel`, `map`2. **Database Binding** — Read-only external SQLite (or Notion) data1. **State Management** — `$variables`(strings, numbers, booleans, objects, arrays)The TypeScript runtime executes Markdown documents with:## Overview---**Status:** Specification (for implementation in v1.0.3.0)**Reference:** Example scripts in`/dev/roadmap/`+ Notion integration (Move 1)  **Scope:** Mobile/iPad (iOS/iPadOS) + future desktop TypeScript support  **Purpose:** Define how TypeScript runtime (v1.0.3.0+) handles state, variables, and external database binding  **File:**`dev/goblin/services/block_mapper.py`  
**Purpose:** Parse markdown → Block objects → Notion API format  
**Status:** Scaffold created, implementation pending  
**Complexity:** Medium (300-400 lines)

---

## Data Classes

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class BlockType(str, Enum):
    """Standard + Runtime block types"""
    # Standard Markdown
    HEADING_1 = "heading_1"
    HEADING_2 = "heading_2"
    HEADING_3 = "heading_3"
    PARAGRAPH = "paragraph"
    QUOTE = "quote"
    BULLETED_LIST = "bulleted_list_item"
    NUMBERED_LIST = "numbered_list_item"
    TODO = "to_do"
    CODE = "code"
    IMAGE = "image"
    DIVIDER = "divider"
    CALLOUT = "callout"

    # Runtime Blocks
    STATE = "state"        # Code fence with metadata
    SET = "set"            # Code fence with metadata
    FORM = "form"          # Code fence with form fields
    IF = "if"              # Toggle with condition
    NAV = "nav"            # Callout with links
    PANEL = "panel"        # Column list
    MAP = "map"            # Table

@dataclass
class RichText:
    """Rich text with annotations"""
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    link: Optional[str] = None

    def to_notion(self) -> Dict[str, Any]:
        """Convert to Notion rich_text format"""
        return {
            "type": "text",
            "text": {"content": self.text, "link": {"url": self.link} if self.link else None},
            "annotations": {
                "bold": self.bold,
                "italic": self.italic,
                "code": self.code,
                "strikethrough": False,
                "underline": False,
                "color": "default"
            },
            "plain_text": self.text,
            "href": self.link
        }

@dataclass
class DBBinding:
    """External database binding configuration"""
    provider: str  # 'sqlite' | 'mysql' | 'notion'
    path: str      # './data/example.sqlite.db'
    namespace: str # '$db'
    bind: List[str]  # ['$db.fact.weather', '$db.npc[*].name']

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to YAML-compatible dict"""
        return {
            'provider': self.provider,
            'path': self.path,
            'namespace': self.namespace,
            'bind': self.bind
        }

@dataclass
class Block:
    """Internal block representation"""
    type: BlockType
    content: str  # Raw content
    children: List['Block'] = None
    metadata: Dict[str, Any] = None  # Type-specific metadata

    # For rich text blocks
    rich_text: List[RichText] = None

    # For runtime blocks (state, set, form, etc)
    db_binding: Optional[DBBinding] = None

    def to_notion(self) -> Dict[str, Any]:
        """Convert to Notion API block format"""
        pass  # Implemented in BlockMapper
```

---

## BlockMapper Class

````python
import re
from markdown_it import MarkdownIt

class BlockMapper:
    """Maps uDOS markdown ↔ Notion blocks"""

    def __init__(self):
        self.md = MarkdownIt()
        self.runtime_block_types = {'state', 'set', 'form', 'if', 'nav', 'panel', 'map'}

    # ============ PARSE MARKDOWN ============

    def parse_markdown(self, content: str) -> List[Block]:
        """Parse markdown string → Block objects"""
        blocks = []
        tokens = self.md.parse(content)

        i = 0
        while i < len(tokens):
            token = tokens[i]
            block, next_i = self._parse_token(tokens, i)
            if block:
                blocks.append(block)
            i = next_i

        return blocks

    def _parse_token(self, tokens: List, index: int) -> tuple[Optional[Block], int]:
        """Parse single token → Block"""
        token = tokens[index]

        # Headings
        if token.type == "heading_open":
            level = int(token.tag[1])
            content_token = tokens[index + 1]
            text = content_token.content
            block_type = BlockType(f"heading_{level}")
            return Block(
                type=block_type,
                content=text,
                rich_text=[RichText(text)]
            ), index + 3

        # Paragraphs (including code fences)
        if token.type == "paragraph_open":
            # Check if paragraph contains code fence
            if index + 1 < len(tokens) and tokens[index + 1].type == "inline":
                inline_token = tokens[index + 1]
                content = inline_token.content

                # Check if it's a runtime block (state, set, form, etc)
                if self._is_code_block(content):
                    return self._parse_code_block(content), index + 3

                # Regular paragraph
                return Block(
                    type=BlockType.PARAGRAPH,
                    content=content,
                    rich_text=[RichText(content)]
                ), index + 3

        # Code blocks (```language ... ```)
        if token.type == "fence":
            lang = token.info or ""
            code = token.content

            # Check if it's a runtime block
            if lang in self.runtime_block_types:
                return self._parse_runtime_block(lang, code), index + 1

            # Regular code block
            return Block(
                type=BlockType.CODE,
                content=code,
                metadata={"language": lang},
                rich_text=[RichText(code)]
            ), index + 1

        # Lists
        if token.type == "bullet_list_open":
            items = []
            i = index + 1
            while i < len(tokens) and tokens[i].type != "bullet_list_close":
                if tokens[i].type == "list_item_open":
                    # Extract item content
                    content_token = tokens[i + 2]
                    items.append(content_token.content)
                    i += 4
                else:
                    i += 1

            return Block(
                type=BlockType.BULLETED_LIST,
                content="\n".join(items),
                children=[Block(type=BlockType.PARAGRAPH, content=item, rich_text=[RichText(item)])
                         for item in items]
            ), i + 1

        # Blockquotes
        if token.type == "blockquote_open":
            # Extract quote content
            content_token = None
            i = index + 1
            while i < len(tokens) and tokens[i].type != "blockquote_close":
                if tokens[i].type == "paragraph_open" and i + 1 < len(tokens):
                    if tokens[i + 1].type == "inline":
                        content_token = tokens[i + 1]
                i += 1

            text = content_token.content if content_token else ""
            return Block(
                type=BlockType.QUOTE,
                content=text,
                rich_text=[RichText(text)]
            ), i + 1

        # Skip other token types
        return None, index + 1

    def _is_code_block(self, content: str) -> bool:
        """Check if content is inline code block"""
        return content.strip().startswith("```") and content.strip().endswith("```")

    def _parse_code_block(self, content: str) -> Block:
        """Parse code fence (could be runtime block or regular code)"""
        # Extract language and code
        match = re.match(r'```(\w+)?\n(.*)\n```', content, re.DOTALL)
        if match:
            lang = match.group(1) or "text"
            code = match.group(2)

            if lang in self.runtime_block_types:
                return self._parse_runtime_block(lang, code)

            return Block(
                type=BlockType.CODE,
                content=code,
                metadata={"language": lang},
                rich_text=[RichText(code)]
            )

        return Block(type=BlockType.CODE, content=content, rich_text=[RichText(content)])

    def _parse_runtime_block(self, block_type: str, content: str) -> Block:
        """Parse runtime block (state, set, form, if, etc)"""
        return Block(
            type=BlockType(block_type),
            content=content,
            metadata={"runtime": True, "language": "typescript"},
            rich_text=[RichText(content)]
        )

    # ============ CONVERT TO NOTION ============

    def to_notion_api(self, blocks: List[Block]) -> List[Dict[str, Any]]:
        """Convert Block objects → Notion API format"""
        return [self._block_to_notion(block) for block in blocks]

    def _block_to_notion(self, block: Block) -> Dict[str, Any]:
        """Convert single Block → Notion API block"""
        notion_block = {
            "object": "block",
            "type": block.type.value,
        }

        # Standard mapping
        if block.type == BlockType.HEADING_1:
            notion_block["heading_1"] = {
                "rich_text": [rt.to_notion() for rt in block.rich_text],
                "color": "default",
                "is_toggleable": False
            }

        elif block.type == BlockType.HEADING_2:
            notion_block["heading_2"] = {
                "rich_text": [rt.to_notion() for rt in block.rich_text],
                "color": "default",
                "is_toggleable": False
            }

        elif block.type == BlockType.HEADING_3:
            notion_block["heading_3"] = {
                "rich_text": [rt.to_notion() for rt in block.rich_text],
                "color": "default",
                "is_toggleable": False
            }

        elif block.type == BlockType.PARAGRAPH:
            notion_block["paragraph"] = {
                "rich_text": [rt.to_notion() for rt in block.rich_text],
                "color": "default"
            }

        elif block.type == BlockType.CODE:
            notion_block["code"] = {
                "rich_text": [rt.to_notion() for rt in block.rich_text],
                "language": block.metadata.get("language", "text"),
                "caption": [RichText("[uDOS:CODE]").to_notion()]
            }

        elif block.type == BlockType.QUOTE:
            notion_block["quote"] = {
                "rich_text": [rt.to_notion() for rt in block.rich_text],
                "color": "default"
            }

        elif block.type == BlockType.BULLETED_LIST:
            # Create multiple list items
            return [
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [RichText(child.content).to_notion()],
                        "color": "default"
                    }
                }
                for child in (block.children or [])
            ]

        # Runtime blocks → code with metadata
        elif block.type in [BlockType.STATE, BlockType.SET, BlockType.FORM]:
            notion_block["code"] = {
                "rich_text": [rt.to_notion() for rt in block.rich_text],
                "language": "typescript",
                "caption": [RichText(f"[uDOS:{block.type.value.upper()}]").to_notion()]
            }

        elif block.type == BlockType.IF:
            # Map to toggle (collapsible heading)
            notion_block["type"] = "heading_2"
            notion_block["heading_2"] = {
                "rich_text": [RichText(f"if {block.content}").to_notion()],
                "color": "default",
                "is_toggleable": True
            }

        elif block.type == BlockType.NAV:
            notion_block["callout"] = {
                "rich_text": [rt.to_notion() for rt in block.rich_text],
                "icon": {"emoji": "🧭"},
                "color": "default"
            }

        elif block.type == BlockType.PANEL:
            # Map to column_list (special handling needed for children)
            notion_block["column_list"] = {}

        elif block.type == BlockType.MAP:
            # Map to table (special handling needed)
            notion_block["table"] = {
                "table_width": 2,
                "has_column_header": True,
                "has_row_header": False
            }

        return notion_block

    # ============ CONVERT FROM NOTION ============

    def from_notion_blocks(self, notion_blocks: List[Dict[str, Any]]) -> str:
        """Convert Notion blocks → markdown string"""
        markdown_lines = []

        for block in notion_blocks:
            md_block = self._notion_block_to_markdown(block)
            if md_block:
                markdown_lines.append(md_block)

        return "\n\n".join(markdown_lines)

    def _notion_block_to_markdown(self, block: Dict[str, Any]) -> Optional[str]:
        """Convert single Notion block → markdown"""
        block_type = block.get("type")

        if block_type == "heading_1":
            content = self._extract_rich_text(block["heading_1"]["rich_text"])
            return f"# {content}"

        elif block_type == "heading_2":
            content = self._extract_rich_text(block["heading_2"]["rich_text"])
            if block["heading_2"].get("is_toggleable"):
                # Runtime IF block
                return f"```if {content}\n...\n```"
            return f"## {content}"

        elif block_type == "heading_3":
            content = self._extract_rich_text(block["heading_3"]["rich_text"])
            return f"### {content}"

        elif block_type == "paragraph":
            content = self._extract_rich_text(block["paragraph"]["rich_text"])
            return content

        elif block_type == "code":
            content = self._extract_rich_text(block["code"]["rich_text"])
            lang = block["code"].get("language", "text")
            caption = self._extract_rich_text(block["code"].get("caption", []))

            # Check caption for runtime block marker
            if "[uDOS:" in caption:
                return f"```{lang}\n{content}\n```"

            return f"```{lang}\n{content}\n```"

        elif block_type == "quote":
            content = self._extract_rich_text(block["quote"]["rich_text"])
            return f"> {content}"

        elif block_type == "bulleted_list_item":
            content = self._extract_rich_text(block["bulleted_list_item"]["rich_text"])
            return f"- {content}"

        elif block_type == "numbered_list_item":
            content = self._extract_rich_text(block["numbered_list_item"]["rich_text"])
            return f"1. {content}"

        elif block_type == "divider":
            return "---"

        elif block_type == "callout":
            content = self._extract_rich_text(block["callout"]["rich_text"])
            return f"> {content}"

        return None

    def _extract_rich_text(self, rich_text_array: List[Dict]) -> str:
        """Extract plain text from Notion rich_text array"""
        return "".join([rt.get("plain_text", "") for rt in rich_text_array])
````

---

## Tests

````python
# dev/goblin/tests/test_block_mapper.py

import pytest
from dev.goblin.services.block_mapper import BlockMapper, BlockType, Block

class TestBlockMapper:

    def setup_method(self):
        self.mapper = BlockMapper()

    def test_parse_heading(self):
        markdown = "# Title"
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.HEADING_1
        assert blocks[0].content == "Title"

    def test_parse_paragraph(self):
        markdown = "This is a paragraph."
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.PARAGRAPH

    def test_parse_code_block(self):
        markdown = """```typescript
const x = 1;
```"""
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.CODE
        assert blocks[0].metadata["language"] == "typescript"

    def test_parse_state_block(self):
        markdown = """```state
name: string = "Alice"
```"""
        blocks = self.mapper.parse_markdown(markdown)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.STATE

    def test_to_notion_heading(self):
        block = Block(
            type=BlockType.HEADING_1,
            content="Title",
            rich_text=[RichText("Title")]
        )
        notion_blocks = self.mapper.to_notion_api([block])
        assert notion_blocks[0]["type"] == "heading_1"
        assert notion_blocks[0]["heading_1"]["rich_text"][0]["plain_text"] == "Title"

    def test_roundtrip_markdown(self):
        """Parse → Notion → Markdown should preserve content"""
        original = "# Title\n\nThis is a paragraph."

        # Parse markdown
        blocks = self.mapper.parse_markdown(original)

        # Convert to Notion and back
        notion = self.mapper.to_notion_api(blocks)
        result = self.mapper.from_notion_blocks(notion)

        # Clean whitespace and compare
        assert result.strip() == original.strip()
````

---

## Next: NotionSyncService

After `BlockMapper` is tested, implement:

- `NotionSyncService` — Handle Notion API calls + webhooks
- `SyncQueue` — SQLite queue for async syncing
- `ConflictResolver` — Merge strategy for concurrent edits

See [Move 1 Quick Start](./MOVE-1-QUICK-START.md) for full plan.
