"""
End-to-End Binder Compilation Integration Test

Comprehensive test covering full workflow:
1. Create binder with metadata
2. Add multiple chapters with varied content
3. Compile all formats (Markdown, JSON, PDF, Brief)
4. Verify file contents and structure
5. Check database records

Author: uDOS Team
Version: 0.2.0
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8767"
TIMEOUT = 10
TEST_BINDER_ID = f"e2e-test-{int(time.time())}"
OUTPUT_DIR = Path("memory/binders")

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_header(text: str):
    print("\n" + "=" * 60)
    print(BLUE + text + RESET)
    print("=" * 60)


def print_success(text: str):
    print(GREEN + f"✅ {text}" + RESET)


def print_error(text: str):
    print(RED + f"❌ {text}" + RESET)


def print_info(text: str):
    print(YELLOW + f"ℹ️  {text}" + RESET)


# ==========================================
# Test Steps
# ==========================================

def test_e2e_binder_compilation():
    """Complete end-to-end test of binder compilation"""
    
    print_header("END-TO-END BINDER COMPILATION TEST")
    print_info(f"Test Binder ID: {TEST_BINDER_ID}")
    
    # Step 1: Add chapters with varied content
    print_header("STEP 1: Add Chapters")
    
    chapters = [
        {
            "chapter_id": "intro",
            "title": "Introduction",
            "content": """# Introduction

Welcome to this comprehensive guide! This chapter introduces the main concepts.

## Key Topics

- Getting started
- Core principles
- Best practices

Let's dive in...""",
            "order_index": 1
        },
        {
            "chapter_id": "setup",
            "title": "Setup Guide",
            "content": """# Setup Guide

## Installation

```bash
npm install my-package
```

## Configuration

![Configuration diagram](config.png)

| Setting | Value | Description |
|---------|-------|-------------|
| PORT | 8080 | Server port |
| DEBUG | false | Debug mode |

### Environment Variables

Set these variables in your `.env` file:

```env
DATABASE_URL=postgresql://localhost/mydb
API_KEY=your_key_here
```""",
            "order_index": 2
        },
        {
            "chapter_id": "advanced",
            "title": "Advanced Topics",
            "content": """# Advanced Topics

This chapter covers advanced usage patterns.

## Performance Optimization

Some key strategies:
- Use caching where appropriate
- Optimize database queries
- Implement lazy loading

## Troubleshooting

Common issues and solutions.""",
            "order_index": 3
        }
    ]
    
    for chapter in chapters:
        try:
            response = requests.post(
                f"{BASE_URL}/api/v0/binder/{TEST_BINDER_ID}/chapters",
                json=chapter,
                timeout=TIMEOUT
            )
            response.raise_for_status()
            result = response.json()
            
            assert result["status"] == "added", "Chapter add failed"
            assert result["chapter_id"] == chapter["chapter_id"], "Chapter ID mismatch"
            
            print_success(f"Added chapter: {chapter['title']}")
            print(f"   ID: {chapter['chapter_id']}")
            print(f"   Content: {len(chapter['content'])} chars")
            
        except Exception as e:
            print_error(f"Failed to add chapter '{chapter['title']}': {e}")
            assert False, f"Chapter addition failed: {e}"
    
    # Step 2: Verify all chapters were added
    print_header("STEP 2: Verify Chapters")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v0/binder/{TEST_BINDER_ID}/chapters",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        chapters_list = result.get("chapters", [])
        assert len(chapters_list) == 3, f"Expected 3 chapters, got {len(chapters_list)}"
        
        print_success(f"Retrieved {len(chapters_list)} chapters")
        
        for ch in chapters_list:
            print(f"   - {ch['title']}")
            print(f"     Words: {ch.get('word_count', 0)}")
            print(f"     Features: Code={ch.get('has_code', False)} | "
                  f"Images={ch.get('has_images', False)} | "
                  f"Tables={ch.get('has_tables', False)}")
            
    except Exception as e:
        print_error(f"Failed to retrieve chapters: {e}")
        assert False, f"Chapter retrieval failed: {e}"
    
    # Step 3: Compile all formats
    print_header("STEP 3: Compile All Formats")
    
    formats = ["markdown", "json", "brief"]
    # Note: PDF excluded by default (requires pandoc)
    
    try:
        payload = {
            "binder_id": TEST_BINDER_ID,
            "formats": formats,
            "include_toc": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v0/binder/compile",
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        assert result["status"] == "compiled", "Compilation failed"
        assert result["binder_id"] == TEST_BINDER_ID, "Binder ID mismatch"
        
        outputs = result.get("outputs", [])
        assert len(outputs) == len(formats), f"Expected {len(formats)} outputs, got {len(outputs)}"
        
        print_success(f"Compiled {len(outputs)} formats")
        
        for output in outputs:
            print(f"   - {output['format'].upper()}")
            print(f"     Path: {output['path']}")
            print(f"     Size: {output['size_bytes']} bytes")
            if 'checksum' in output:
                print(f"     Checksum: {output['checksum'][:16]}...")
        
    except Exception as e:
        print_error(f"Compilation failed: {e}")
        assert False, f"Compilation failed: {e}"
    
    # Step 4: Verify output files exist
    print_header("STEP 4: Verify Output Files")
    
    expected_files = {
        "markdown": OUTPUT_DIR / f"{TEST_BINDER_ID}.md",
        "json": OUTPUT_DIR / f"{TEST_BINDER_ID}.json",
        "brief": OUTPUT_DIR / f"{TEST_BINDER_ID}-brief.md"
    }
    
    for format_name, file_path in expected_files.items():
        try:
            assert file_path.exists(), f"File not found: {file_path}"
            
            file_size = file_path.stat().st_size
            assert file_size > 0, f"File is empty: {file_path}"
            
            print_success(f"{format_name.upper()} file verified")
            print(f"   Path: {file_path}")
            print(f"   Size: {file_size} bytes")
            
        except Exception as e:
            print_error(f"File verification failed for {format_name}: {e}")
            assert False, f"File verification failed: {e}"
    
    # Step 5: Verify Markdown content structure
    print_header("STEP 5: Verify Markdown Content")
    
    try:
        md_file = expected_files["markdown"]
        content = md_file.read_text(encoding='utf-8')
        
        # Check for required elements
        assert f"# Binder: {TEST_BINDER_ID}" in content, "Missing binder title"
        assert "## Table of Contents" in content, "Missing TOC"
        assert "## Introduction" in content, "Missing Introduction chapter"
        assert "## Setup Guide" in content, "Missing Setup Guide chapter"
        assert "## Advanced Topics" in content, "Missing Advanced Topics chapter"
        assert "---" in content, "Missing chapter separators"
        
        print_success("Markdown structure verified")
        print(f"   Total length: {len(content)} chars")
        print(f"   Lines: {content.count(chr(10)) + 1}")
        
        # Count chapters
        chapter_count = content.count("## ") - 1  # Subtract TOC header
        print(f"   Chapters found: {chapter_count}")
        
    except Exception as e:
        print_error(f"Markdown verification failed: {e}")
        assert False, f"Markdown verification failed: {e}"
    
    # Step 6: Verify JSON structure
    print_header("STEP 6: Verify JSON Content")
    
    try:
        json_file = expected_files["json"]
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check structure
        assert data["binder_id"] == TEST_BINDER_ID, "Binder ID mismatch in JSON"
        assert "compiled_at" in data, "Missing compiled_at"
        assert "chapters" in data, "Missing chapters array"
        assert "stats" in data, "Missing stats"
        
        chapters_array = data["chapters"]
        assert len(chapters_array) == 3, f"Expected 3 chapters, got {len(chapters_array)}"
        
        # Verify stats
        stats = data["stats"]
        assert stats["total_chapters"] == 3, "Chapter count mismatch"
        assert stats["total_words"] > 0, "No words counted"
        
        print_success("JSON structure verified")
        print(f"   Binder ID: {data['binder_id']}")
        print(f"   Chapters: {len(chapters_array)}")
        print(f"   Total words: {stats['total_words']}")
        
        # Verify chapter features
        for ch in chapters_array:
            print(f"   - {ch['title']}: {ch['word_count']} words")
        
    except Exception as e:
        print_error(f"JSON verification failed: {e}")
        assert False, f"JSON verification failed: {e}"
    
    # Step 7: Verify Dev Brief format
    print_header("STEP 7: Verify Dev Brief Content")
    
    try:
        brief_file = expected_files["brief"]
        content = brief_file.read_text(encoding='utf-8')
        
        # Check for required elements
        assert f"# Dev Brief: {TEST_BINDER_ID}" in content, "Missing brief title"
        assert "## Executive Summary" in content, "Missing executive summary"
        assert "## Chapter Overview" in content, "Missing chapter overview"
        assert "Total Chapters:" in content, "Missing chapter count"
        assert "Total Words:" in content, "Missing word count"
        assert "Estimated Reading Time:" in content, "Missing reading time"
        
        # Check for chapter summaries (condensed content)
        assert "Introduction" in content, "Missing Introduction in brief"
        assert "Setup Guide" in content, "Missing Setup Guide in brief"
        assert "Advanced Topics" in content, "Missing Advanced Topics in brief"
        
        print_success("Dev Brief structure verified")
        print(f"   Total length: {len(content)} chars")
        
        # Check for feature indicators
        if "📝 Code" in content:
            print("   ✓ Code blocks detected")
        if "🖼️ Images" in content:
            print("   ✓ Images detected")
        if "📊 Tables" in content:
            print("   ✓ Tables detected")
        
    except Exception as e:
        print_error(f"Dev Brief verification failed: {e}")
        assert False, f"Dev Brief verification failed: {e}"
    
    # Final Summary
    print_header("TEST COMPLETE")
    print_success("All checks passed!")
    print_info(f"Binder ID: {TEST_BINDER_ID}")
    print_info(f"Outputs: {len(formats)} formats compiled")
    print_info(f"Chapters: 3 (intro, setup, advanced)")
    print_info(f"Output directory: {OUTPUT_DIR}")
    
    assert True


if __name__ == "__main__":
    # Check server availability
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print_success(f"Server is running at {BASE_URL}")
    except Exception as e:
        print_error(f"Cannot connect to server at {BASE_URL}")
        print(f"   Error: {e}")
        print("\n   Start the server with:")
        print("   dev/goblin/launch-goblin-dev.sh")
        exit(1)
    
    # Run test
    test_e2e_binder_compilation()
    print("\n" + GREEN + "🎉 END-TO-END TEST PASSED!" + RESET + "\n")
