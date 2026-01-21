"""
Binder Compiler Service

Compiles multi-chapter knowledge binders from:
- Research outputs
- Task results
- Manual additions
- Template structures

Output formats:
- Markdown (primary)
- PDF (via pandoc/weasyprint)
- JSON (structured data)
- Dev brief (Markdown + YAML frontmatter)

Author: uDOS Team
Version: 0.1.0
"""

import sqlite3
import logging
import json
import subprocess
import hashlib
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import yaml

logger = logging.getLogger('goblin.binder')


class BinderCompiler:
    """Compile multi-format binder outputs"""
    
    def __init__(self, db_path: Optional[Path] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize binder compiler
        
        Args:
            db_path: Path to SQLite database (default: memory/synced/goblin.db)
            config: Configuration dictionary with output_dir and formats
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent.parent / "memory" / "synced" / "goblin.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "memory/binders"))
        self.formats = self.config.get("formats", ["markdown", "json"])
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema if needed
        self._init_db()
        
        logger.info(f"[BINDER] Initialized (output: {self.output_dir})")
    
    def _init_db(self):
        """Initialize database schema if needed"""
        try:
            # Read and execute schema
            schema_path = Path(__file__).parent.parent / "schemas" / "binder_schema.sql"
            
            if schema_path.exists():
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                
                # Execute schema (split by semicolon for multiple statements)
                cursor.executescript(schema_sql)
                
                conn.commit()
                conn.close()
                logger.info(f"[BINDER] Database initialized at {self.db_path}")
            else:
                logger.warning(f"[BINDER] Schema file not found: {schema_path}")
        except Exception as e:
            logger.error(f"[BINDER] Database initialization error: {e}")
    
    async def compile_binder(self, binder_id: str, formats: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compile binder in specified formats
        
        Args:
            binder_id: Binder identifier
            formats: List of formats to generate (default: all configured)
        
        Returns:
            {
                "status": "compiled",
                "binder_id": "...",
                "outputs": [...]
            }
        """
        if formats is None:
            formats = self.formats
        
        logger.info(f"[GOBLIN:BINDER] Compiling {binder_id} → {formats}")
        
        # Get chapters
        chapters = await self.get_chapters(binder_id)
        
        if not chapters:
            logger.warning(f"[BINDER] No chapters found for {binder_id}")
        
        outputs = []
        
        if "markdown" in formats:
            md_output = await self._compile_markdown(binder_id, chapters)
            if md_output:
                outputs.append(md_output)
        
        if "json" in formats:
            json_output = await self._compile_json(binder_id, chapters)
            if json_output:
                outputs.append(json_output)
        
        if "pdf" in formats:
            pdf_output = await self._compile_pdf(binder_id, chapters)
            if pdf_output:
                outputs.append(pdf_output)
        
        if "brief" in formats:
            brief_output = await self._compile_brief(binder_id, chapters)
            if brief_output:
                outputs.append(brief_output)
        
        return {
            "status": "compiled",
            "binder_id": binder_id,
            "compiled_at": datetime.now().isoformat(),
            "outputs": outputs
        }
    
    def _generate_id(self, prefix: str = "id") -> str:
        """Generate unique ID"""
        import secrets
        return f"{prefix}_{secrets.token_hex(6)}"
    
    def _calculate_word_count(self, text: str) -> int:
        """Calculate word count in text"""
        # Remove markdown syntax for more accurate count
        text = re.sub(r'[#*`\[\]()]', '', text)
        words = text.split()
        return len(words)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    async def get_chapters(self, binder_id: str) -> List[Dict[str, Any]]:
        """Get binder chapter structure"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    chapter_id, title, order_index as "order", status, 
                    word_count, has_code, has_images, has_tables,
                    created_at, updated_at
                FROM chapters
                WHERE binder_id = ?
                ORDER BY order_index ASC
            """, (binder_id,))
            
            chapters = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return chapters
        except Exception as e:
            logger.error(f"[BINDER] Error getting chapters: {e}")
            return []
    
    async def add_chapter(self, binder_id: str, chapter: Dict[str, Any]) -> Dict[str, Any]:
        """Add chapter to binder"""
        logger.info(f"[GOBLIN:BINDER] Adding chapter to {binder_id}: {chapter.get('title')}")
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            chapter_id = chapter.get("chapter_id")
            title = chapter.get("title")
            content = chapter.get("content", "")
            order_index = chapter.get("order", 1)
            
            # Calculate word count
            word_count = self._calculate_word_count(content)
            
            # Detect content features
            has_code = "```" in content
            has_images = "![" in content
            has_tables = "|" in content and "\n|" in content
            
            # Generate unique ID
            id = self._generate_id("chap")
            
            cursor.execute("""
                INSERT INTO chapters (
                    id, binder_id, chapter_id, title, content,
                    order_index, word_count, has_code, has_images, has_tables
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (id, binder_id, chapter_id, title, content,
                  order_index, word_count, has_code, has_images, has_tables))
            
            conn.commit()
            conn.close()
            
            return {
                "status": "added",
                "binder_id": binder_id,
                "chapter_id": chapter_id,
                "title": title
            }
        except Exception as e:
            logger.error(f"[BINDER] Error adding chapter: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def update_chapter(self, binder_id: str, chapter_id: str, content: str) -> Dict[str, Any]:
        """Update chapter content"""
        logger.info(f"[GOBLIN:BINDER] Updating {binder_id}/{chapter_id}")
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Calculate new word count and features
            word_count = self._calculate_word_count(content)
            has_code = "```" in content
            has_images = "![" in content
            has_tables = "|" in content and "\n|" in content
            
            cursor.execute("""
                UPDATE chapters
                SET content = ?, word_count = ?, has_code = ?, has_images = ?, has_tables = ?
                WHERE binder_id = ? AND chapter_id = ?
            """, (content, word_count, has_code, has_images, has_tables, binder_id, chapter_id))
            
            conn.commit()
            conn.close()
            
            return {
                "status": "updated",
                "binder_id": binder_id,
                "chapter_id": chapter_id,
                "updated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"[BINDER] Error updating chapter: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _compile_markdown(self, binder_id: str, chapters: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate markdown binder"""
        try:
            output_path = self.output_dir / f"{binder_id}.md"
            
            # Build markdown content
            lines = []
            lines.append(f"# Binder: {binder_id}\n")
            lines.append(f"*Compiled: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            # Table of contents
            lines.append("## Table of Contents\n")
            for i, chapter in enumerate(chapters, 1):
                title = chapter.get('title', f'Chapter {i}')
                lines.append(f"{i}. [{title}](#{self._slugify(title)})")
            lines.append("\n---\n\n")
            
            # Chapters
            for i, chapter in enumerate(chapters, 1):
                title = chapter.get('title', f'Chapter {i}')
                content = chapter.get('content', '')
                
                lines.append(f"## {title}\n\n")
                lines.append(f"{content}\n\n")
                lines.append("---\n\n")
            
            # Write file
            markdown_content = "\n".join(lines)
            output_path.write_text(markdown_content, encoding='utf-8')
            
            # Calculate stats
            file_size = output_path.stat().st_size
            checksum = self._calculate_checksum(str(output_path))
            
            # Record output in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            output_id = self._generate_id("out")
            cursor.execute("""
                INSERT INTO outputs (id, binder_id, format, file_path, file_size, checksum)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (output_id, binder_id, "markdown", str(output_path), file_size, checksum))
            
            conn.commit()
            conn.close()
            
            logger.info(f"[BINDER] Markdown compiled: {output_path} ({file_size} bytes)")
            
            return {
                "format": "markdown",
                "path": str(output_path),
                "size_bytes": file_size,
                "checksum": checksum
            }
        except Exception as e:
            logger.error(f"[BINDER] Markdown compilation error: {e}")
            return None
    
    async def _compile_json(self, binder_id: str, chapters: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate JSON binder"""
        try:
            import json
            
            output_path = self.output_dir / f"{binder_id}.json"
            
            # Build JSON structure
            data = {
                "binder_id": binder_id,
                "compiled_at": datetime.now().isoformat(),
                "chapters": chapters,
                "stats": {
                    "total_chapters": len(chapters),
                    "total_words": sum(ch.get('word_count', 0) for ch in chapters)
                }
            }
            
            # Write file
            output_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
            
            # Calculate stats
            file_size = output_path.stat().st_size
            checksum = self._calculate_checksum(str(output_path))
            
            # Record output in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            output_id = self._generate_id("out")
            cursor.execute("""
                INSERT INTO outputs (id, binder_id, format, file_path, file_size, checksum)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (output_id, binder_id, "json", str(output_path), file_size, checksum))
            
            conn.commit()
            conn.close()
            
            logger.info(f"[BINDER] JSON compiled: {output_path} ({file_size} bytes)")
            
            return {
                "format": "json",
                "path": str(output_path),
                "size_bytes": file_size,
                "checksum": checksum
            }
        except Exception as e:
            logger.error(f"[BINDER] JSON compilation error: {e}")
            return None
    
    async def _compile_pdf(self, binder_id: str, chapters: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate PDF binder via pandoc"""
        try:
            import subprocess
            
            # Check if pandoc is installed
            try:
                subprocess.run(["which", "pandoc"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                logger.warning("[BINDER] pandoc not found - skipping PDF generation")
                return None
            
            # First compile markdown
            md_output = await self._compile_markdown(binder_id, chapters)
            if not md_output:
                return None
            
            md_path = md_output["path"]
            pdf_path = self.output_dir / f"{binder_id}.pdf"
            
            # Convert to PDF
            result = subprocess.run(
                ["pandoc", md_path, "-o", str(pdf_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"[BINDER] pandoc error: {result.stderr}")
                return None
            
            # Calculate stats
            file_size = pdf_path.stat().st_size
            checksum = self._calculate_checksum(str(pdf_path))
            
            # Record output in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            output_id = self._generate_id("out")
            cursor.execute("""
                INSERT INTO outputs (id, binder_id, format, file_path, file_size, checksum)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (output_id, binder_id, "pdf", str(pdf_path), file_size, checksum))
            
            conn.commit()
            conn.close()
            
            logger.info(f"[BINDER] PDF compiled: {pdf_path} ({file_size} bytes)")
            
            return {
                "format": "pdf",
                "path": str(pdf_path),
                "size_bytes": file_size,
                "checksum": checksum
            }
        except Exception as e:
            logger.error(f"[BINDER] PDF compilation error: {e}")
            return None
    
    async def _compile_brief(self, binder_id: str, chapters: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate dev brief format"""
        try:
            output_path = self.output_dir / f"{binder_id}-brief.md"
            
            # Build brief content
            lines = []
            lines.append(f"# Dev Brief: {binder_id}\n")
            lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            # Executive summary
            total_words = sum(ch.get('word_count', 0) for ch in chapters)
            lines.append("## Executive Summary\n")
            lines.append(f"- **Total Chapters:** {len(chapters)}")
            lines.append(f"- **Total Words:** {total_words:,}")
            lines.append(f"- **Estimated Reading Time:** {total_words // 200} minutes\n\n")
            
            # Chapter overview
            lines.append("## Chapter Overview\n")
            for i, chapter in enumerate(chapters, 1):
                title = chapter.get('title', f'Chapter {i}')
                word_count = chapter.get('word_count', 0)
                has_code = chapter.get('has_code', False)
                has_images = chapter.get('has_images', False)
                has_tables = chapter.get('has_tables', False)
                
                features = []
                if has_code: features.append("📝 Code")
                if has_images: features.append("🖼️ Images")
                if has_tables: features.append("📊 Tables")
                
                lines.append(f"\n### {i}. {title}")
                lines.append(f"- **Words:** {word_count}")
                if features:
                    lines.append(f"- **Features:** {' | '.join(features)}")
            
            lines.append("\n---\n\n")
            
            # Full content (condensed)
            for i, chapter in enumerate(chapters, 1):
                title = chapter.get('title', f'Chapter {i}')
                content = chapter.get('content', '')
                
                # First 500 chars only
                preview = content[:500]
                if len(content) > 500:
                    preview += "..."
                
                lines.append(f"## {title}\n\n{preview}\n\n")
            
            # Write file
            brief_content = "\n".join(lines)
            output_path.write_text(brief_content, encoding='utf-8')
            
            # Calculate stats
            file_size = output_path.stat().st_size
            checksum = self._calculate_checksum(str(output_path))
            
            # Record output in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            output_id = self._generate_id("out")
            cursor.execute("""
                INSERT INTO outputs (id, binder_id, format, file_path, file_size, checksum)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (output_id, binder_id, "brief", str(output_path), file_size, checksum))
            
            conn.commit()
            conn.close()
            
            logger.info(f"[BINDER] Brief compiled: {output_path} ({file_size} bytes)")
            
            return {
                "format": "brief",
                "path": str(output_path),
                "size_bytes": file_size,
                "checksum": checksum
            }
        except Exception as e:
            logger.error(f"[BINDER] Brief compilation error: {e}")
            return None
    
    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug"""
        import re
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text
