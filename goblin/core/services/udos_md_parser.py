"""
uDOS.md Template Parser - Parse and execute udos.md templates

Handles the uDOS.md format with:
- YAML frontmatter extraction
- Shortcode detection and execution
- Code block parsing (@named blocks)
- Variable interpolation
- Slideshow splitting

Part of Alpha v1.0.0.67+ - uDOS.md Template System
Version: 1.0.0
Author: uDOS System
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from ..services.logging_manager import get_logger

    logger = get_logger("udos-md-parser")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("udos-md-parser")


@dataclass
class CodeBlock:
    """Named code block from a udos.md file."""

    name: str  # @SPLASH, @config, etc.
    language: str  # upy, json, python, etc.
    content: str
    params: List[str] = field(default_factory=list)  # For function-style blocks
    line_number: int = 0


@dataclass
class Shortcode:
    """Shortcode call in document content."""

    name: str  # SPLASH, FORM:player_setup, etc.
    params: List[str] = field(default_factory=list)
    raw: str = ""  # Original [SHORTCODE] text
    line_number: int = 0
    inline: bool = False  # True if part of inline text


@dataclass
class ParsedTemplate:
    """Fully parsed udos.md template."""

    # Metadata
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    title: str = ""
    template_type: str = "guide"

    # Variables
    variables: Dict[str, Any] = field(default_factory=dict)

    # Content
    raw_content: str = ""
    slides: List[str] = field(default_factory=list)

    # Code blocks and shortcodes
    code_blocks: Dict[str, CodeBlock] = field(default_factory=dict)
    shortcodes: List[Shortcode] = field(default_factory=list)

    # Source info
    source_path: Optional[str] = None


class UdosMdParser:
    """
    Parser for uDOS.md template files.

    Handles:
    - YAML frontmatter extraction
    - Shortcode detection [NAME] or [NAME:param]
    - Named code blocks ```lang @NAME
    - Variable interpolation $variable
    - Slide separation via ---
    """

    # Regex patterns
    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    SHORTCODE_PATTERN = re.compile(r"\[([A-Z][A-Z0-9_]*(?::[^\]]+)?)\]")
    CODE_BLOCK_PATTERN = re.compile(
        r"```(\w+)\s+@([A-Za-z_][A-Za-z0-9_]*(?:\([^)]*\))?)\s*\n(.*?)```", re.DOTALL
    )
    VARIABLE_PATTERN = re.compile(r"\$([A-Za-z_][A-Za-z0-9_\.]*)")
    SLIDE_SEPARATOR = re.compile(r"\n---\s*\n")

    def __init__(self):
        """Initialize the parser."""
        pass

    def parse_file(self, filepath: str) -> ParsedTemplate:
        """
        Parse a udos.md file.

        Args:
            filepath: Path to .md or .udos.md file

        Returns:
            ParsedTemplate with all extracted data
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {filepath}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        result = self.parse(content)
        result.source_path = str(path)

        return result

    def parse(self, content: str) -> ParsedTemplate:
        """
        Parse udos.md content string.

        Args:
            content: Raw markdown content

        Returns:
            ParsedTemplate with extracted data
        """
        result = ParsedTemplate()
        result.raw_content = content

        # 1. Extract frontmatter
        content_after_frontmatter = self._extract_frontmatter(content, result)

        # 2. Extract code blocks (before splitting slides)
        content_without_blocks = self._extract_code_blocks(
            content_after_frontmatter, result
        )

        # 3. Find shortcodes
        self._find_shortcodes(content_without_blocks, result)

        # 4. Split into slides
        result.slides = self._split_slides(content_without_blocks)

        # 5. Set convenience properties
        result.title = result.frontmatter.get("title", "")
        result.template_type = result.frontmatter.get("template", "guide")

        # 6. Extract variables from frontmatter
        if "variables" in result.frontmatter:
            result.variables = result.frontmatter["variables"]

        logger.info(
            f"[LOCAL] Parsed template: {result.title or 'untitled'}, "
            f"{len(result.code_blocks)} code blocks, "
            f"{len(result.shortcodes)} shortcodes, "
            f"{len(result.slides)} slides"
        )

        return result

    def _extract_frontmatter(self, content: str, result: ParsedTemplate) -> str:
        """Extract YAML frontmatter from content."""
        match = self.FRONTMATTER_PATTERN.match(content)

        if match:
            yaml_content = match.group(1)

            if HAS_YAML:
                try:
                    result.frontmatter = yaml.safe_load(yaml_content) or {}
                except yaml.YAMLError as e:
                    logger.warning(f"[LOCAL] YAML parse error: {e}")
                    result.frontmatter = {}
            else:
                # Simple key: value parsing fallback
                result.frontmatter = self._parse_simple_yaml(yaml_content)

            # Return content after frontmatter
            return content[match.end() :]

        return content

    def _parse_simple_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """Simple YAML-like parsing for when PyYAML is not available."""
        result = {}
        current_key = None

        for line in yaml_content.split("\n"):
            line = line.rstrip()
            if not line or line.startswith("#"):
                continue

            if ":" in line and not line.startswith(" "):
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()

                if value:
                    # Remove quotes
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    result[key] = value
                else:
                    result[key] = {}
                    current_key = key

        return result

    def _extract_code_blocks(self, content: str, result: ParsedTemplate) -> str:
        """Extract named code blocks from content."""

        def replace_block(match):
            language = match.group(1)
            name_part = match.group(2)
            block_content = match.group(3)

            # Parse name and optional params: @FUNC($a, $b)
            if "(" in name_part:
                name = name_part[: name_part.index("(")]
                params_str = name_part[name_part.index("(") + 1 : name_part.rindex(")")]
                params = [p.strip() for p in params_str.split(",") if p.strip()]
            else:
                name = name_part
                params = []

            code_block = CodeBlock(
                name=name,
                language=language,
                content=block_content.strip(),
                params=params,
            )

            result.code_blocks[name] = code_block

            # Remove from content (replaced with empty string)
            return ""

        return self.CODE_BLOCK_PATTERN.sub(replace_block, content)

    def _find_shortcodes(self, content: str, result: ParsedTemplate):
        """Find all shortcode references in content."""
        line_num = 0

        for line_num, line in enumerate(content.split("\n"), 1):
            for match in self.SHORTCODE_PATTERN.finditer(line):
                shortcode_text = match.group(1)

                # Parse shortcode: NAME or NAME:param1:param2
                parts = shortcode_text.split(":")
                name = parts[0]
                params = parts[1:] if len(parts) > 1 else []

                # Check if inline (text before or after on same line)
                is_inline = match.start() > 0 or match.end() < len(line.strip())

                shortcode = Shortcode(
                    name=name,
                    params=params,
                    raw=match.group(0),
                    line_number=line_num,
                    inline=is_inline,
                )

                result.shortcodes.append(shortcode)

    def _split_slides(self, content: str) -> List[str]:
        """Split content into slides by --- separator."""
        # Split by --- on its own line
        slides = self.SLIDE_SEPARATOR.split(content)

        # Clean up each slide
        return [slide.strip() for slide in slides if slide.strip()]

    def interpolate_variables(
        self, content: str, variables: Dict[str, Any], strict: bool = False
    ) -> str:
        """
        Replace $variables in content with values.

        Args:
            content: Content with $variable references
            variables: Variable name -> value mapping (keys with or without $)
            strict: Raise error if variable not found

        Returns:
            Content with variables replaced
        """

        def replace_var(match):
            var_name = match.group(1)

            # Try both with and without $ prefix
            lookup_keys = [var_name, f"${var_name}"]

            # Handle nested access: $obj.key
            if "." in var_name:
                parts = var_name.split(".")
                root = parts[0]
                root_keys = [root, f"${root}"]

                value = None
                for key in root_keys:
                    if key in variables:
                        value = variables[key]
                        break

                if value is None:
                    if strict:
                        raise KeyError(f"Variable not found: ${var_name}")
                    return match.group(0)

                for part in parts[1:]:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        if strict:
                            raise KeyError(f"Variable not found: ${var_name}")
                        return match.group(0)  # Keep original
                return str(value)

            # Simple variable - try both key styles
            for key in lookup_keys:
                if key in variables:
                    return str(variables[key])

            if strict:
                raise KeyError(f"Variable not found: ${var_name}")
            return match.group(0)  # Keep original

        return self.VARIABLE_PATTERN.sub(replace_var, content)

    def get_code_block(
        self, template: ParsedTemplate, name: str
    ) -> Optional[CodeBlock]:
        """Get a named code block from parsed template."""
        return template.code_blocks.get(name)

    def execute_code_block(
        self, block: CodeBlock, variables: Dict[str, Any], params: List[str] = None
    ) -> str:
        """
        Execute a code block and return result.

        Args:
            block: CodeBlock to execute
            variables: Variable context
            params: Parameters passed to block (for function blocks)

        Returns:
            Execution result as string
        """
        # Interpolate variables in content
        content = self.interpolate_variables(block.content, variables)

        if block.language == "json":
            # JSON blocks return parsed data as formatted string
            try:
                data = json.loads(content)
                return json.dumps(data, indent=2)
            except json.JSONDecodeError:
                return f"[JSON Error in @{block.name}]"

        elif block.language == "upy":
            # uPY blocks need runtime execution
            # This would integrate with UPYExecutor
            try:
                from ..runtime.upy_executor import execute_upy_code

                return execute_upy_code(content, variables=variables)
            except ImportError:
                # Return content for display if runtime not available
                return f"[uPY @{block.name}]\n{content}"

        else:
            # Other languages just return content
            return content

    def render_shortcode(
        self, shortcode: Shortcode, template: ParsedTemplate, variables: Dict[str, Any]
    ) -> str:
        """
        Render a shortcode by executing its code block.

        Args:
            shortcode: Shortcode to render
            template: Parsed template with code blocks
            variables: Variable context

        Returns:
            Rendered content
        """
        block = template.code_blocks.get(shortcode.name)

        if not block:
            logger.warning(
                f"[LOCAL] Code block not found for shortcode: {shortcode.name}"
            )
            return f"[{shortcode.name}?]"

        # Merge shortcode params with variables
        merged_vars = variables.copy()

        # Map positional params to block params
        if block.params and shortcode.params:
            for i, param_name in enumerate(block.params):
                if i < len(shortcode.params):
                    merged_vars[param_name.lstrip("$")] = shortcode.params[i]

        return self.execute_code_block(block, merged_vars, shortcode.params)

    def render_template(
        self,
        template: ParsedTemplate,
        variables: Dict[str, Any] = None,
        slide_index: int = None,
    ) -> str:
        """
        Fully render a template with all shortcodes executed.

        Args:
            template: Parsed template
            variables: Override variables
            slide_index: Render only specific slide (0-based)

        Returns:
            Rendered content
        """
        # Merge variables
        merged_vars = template.variables.copy()
        if variables:
            merged_vars.update(variables)

        # Get content to render
        if slide_index is not None and 0 <= slide_index < len(template.slides):
            content = template.slides[slide_index]
        else:
            content = "\n\n---\n\n".join(template.slides)

        # Replace shortcodes
        def replace_shortcode(match):
            shortcode_text = match.group(1)
            parts = shortcode_text.split(":")
            name = parts[0]

            shortcode = Shortcode(name=name, params=parts[1:] if len(parts) > 1 else [])

            return self.render_shortcode(shortcode, template, merged_vars)

        content = self.SHORTCODE_PATTERN.sub(replace_shortcode, content)

        # Interpolate remaining variables
        content = self.interpolate_variables(content, merged_vars)

        return content


# Singleton instance
_parser_instance: Optional[UdosMdParser] = None


def get_udos_md_parser() -> UdosMdParser:
    """Get or create singleton UdosMdParser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = UdosMdParser()
    return _parser_instance


# ========== Test ==========
if __name__ == "__main__":
    print("=" * 60)
    print("UDOS.MD PARSER TEST")
    print("=" * 60)

    # Test content
    test_content = """---
title: "Test Template"
template: guide
variables:
  $user_name: "Hero"
  $city: "Sydney"
---

[SPLASH]

# Welcome to $city

Hello, $user_name!

---

## Next Slide

More content here.

[STATUS]

---

```upy @SPLASH
PRINT(':wave: Welcome!')
PRINT('Loading $city...')
```

```upy @STATUS
PRINT(':check: All systems go')
```

```json @config
{
  "theme": "dark"
}
```
"""

    parser = get_udos_md_parser()
    result = parser.parse(test_content)

    print(f"\nTitle: {result.title}")
    print(f"Template: {result.template_type}")
    print(f"Variables: {result.variables}")
    print(f"\nCode Blocks:")
    for name, block in result.code_blocks.items():
        print(f"  @{name} ({block.language})")
    print(f"\nShortcodes:")
    for sc in result.shortcodes:
        print(f"  [{sc.name}] at line {sc.line_number}")
    print(f"\nSlides: {len(result.slides)}")

    print("\n--- Rendered (Slide 0) ---")
    rendered = parser.render_template(result, slide_index=0)
    print(rendered)
