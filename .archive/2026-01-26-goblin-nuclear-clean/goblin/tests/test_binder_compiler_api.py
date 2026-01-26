"""
Binder Compiler API Integration Tests

Tests for multi-format binder compilation endpoints:
- Compile binder (Markdown, PDF, JSON, Brief)
- Manage chapters (add, update, get, delete, list)
- Export formats
- Status tracking

Author: uDOS Team
Version: 0.1.0
"""

import requests
import json
import time
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8767"
TIMEOUT = 10
TEST_BINDER_ID = f"test-binder-{int(time.time())}"

# ANSI colors for output
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_header(text: str):
    """Print formatted header"""
    width = 50
    print("\n" + "=" * width)
    print(BLUE + text + RESET)
    print("=" * width)


def print_success(text: str):
    """Print success message"""
    print(GREEN + f"✅ {text}" + RESET)


def print_error(text: str):
    """Print error message"""
    print(RED + f"❌ {text}" + RESET)


def check_server():
    """Verify server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        print_success(f"Server is running at {BASE_URL}")
        assert True
    except Exception as e:
        print_error("Cannot connect to server at {BASE_URL}")
        print(f"   Error: {e}")
        print("\n   Start the server with:")
        print("   dev/goblin/launch-goblin-dev.sh")
        assert False, "Test failed"


# ==========================================
# Test 1: Compile Binder (All Formats)
# ==========================================

def test_compile_binder():
    """Test binder compilation with multiple formats"""
    print_header("TEST: Compile Binder")
    
    try:
        payload = {
            "binder_id": TEST_BINDER_ID,
            "formats": ["markdown", "json"],
            "include_toc": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v0/binder/compile",
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        assert result["status"] == "compiled", "Expected 'compiled' status"
        assert result["binder_id"] == TEST_BINDER_ID, "Binder ID mismatch"
        assert "compiled_at" in result, "Missing compiled_at"
        
        print_success(f"Compiled binder: {TEST_BINDER_ID}")
        print(f"   Formats: {payload['formats']}")
        print(f"   Outputs: {len(result.get('outputs', []))} files")
        
        assert True
    except Exception as e:
        print_error(f"Error: {e}")
        assert False, "Test failed"


# ==========================================
# Test 2: Get Binder Chapters
# ==========================================

def test_get_chapters():
    """Test retrieving binder chapter structure"""
    print_header("TEST: Get Binder Chapters")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v0/binder/{TEST_BINDER_ID}/chapters",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        
        assert "chapters" in data, "Missing chapters key"
        chapters = data["chapters"]
        
        print_success(f"Retrieved {len(chapters)} chapters")
        for chapter in chapters[:3]:
            title = chapter.get("title", "Untitled")
            status = chapter.get("status", "unknown")
            print(f"   - {title} ({status})")
        
        assert True
    except Exception as e:
        print_error(f"Error: {e}")
        assert False, "Test failed"


# ==========================================
# Test 3: Add Chapter to Binder
# ==========================================

def test_add_chapter():
    """Test adding chapter to binder"""
    print_header("TEST: Add Chapter")
    
    try:
        payload = {
            "chapter_id": "chapter-1",
            "title": "Test Chapter",
            "content": "# Test Chapter\n\nThis is a test chapter.",
            "order": 1
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v0/binder/{TEST_BINDER_ID}/chapters",
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        assert result["status"] == "added", "Expected 'added' status"
        assert result["chapter_id"] == payload["chapter_id"], "Chapter ID mismatch"
        
        print_success(f"Added chapter: {payload['title']}")
        print(f"   Chapter ID: {result['chapter_id']}")
        print(f"   Binder: {result['binder_id']}")
        
        assert True
    except Exception as e:
        print_error(f"Error: {e}")
        assert False, "Test failed"


# ==========================================
# Test 4: Get Specific Chapter
# ==========================================

def test_get_chapter():
    """Test retrieving specific chapter content"""
    print_header("TEST: Get Chapter")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v0/binder/{TEST_BINDER_ID}/chapters/chapter-1",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        assert "chapter_id" in result, "Missing chapter_id"
        assert "content" in result, "Missing content"
        
        print_success(f"Retrieved chapter: {result['chapter_id']}")
        print(f"   Title: {result.get('title', 'N/A')}")
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Word count: {result.get('word_count', 0)}")
        
        assert True
    except Exception as e:
        print_error(f"Error: {e}")
        assert False, "Test failed"


# ==========================================
# Test 5: Update Chapter
# ==========================================

def test_update_chapter():
    """Test updating chapter content and metadata"""
    print_header("TEST: Update Chapter")
    
    try:
        payload = {
            "title": "Updated Chapter Title",
            "content": "# Updated Title\n\nUpdated content here.",
            "status": "review"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/v0/binder/{TEST_BINDER_ID}/chapters/chapter-1",
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        assert result["status"] == "updated", "Expected 'updated' status"
        assert "updated_at" in result, "Missing updated_at"
        
        print_success(f"Updated chapter: {result['chapter_id']}")
        print(f"   Binder: {result['binder_id']}")
        print(f"   Updated at: {result['updated_at']}")
        
        assert True
    except Exception as e:
        print_error(f"Error: {e}")
        assert False, "Test failed"


# ==========================================
# Test 6: Get Binder Status
# ==========================================

def test_binder_status():
    """Test retrieving binder compilation status"""
    print_header("TEST: Binder Status")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v0/binder/{TEST_BINDER_ID}/status",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        assert "status" in result, "Missing status"
        assert "completion_percent" in result, "Missing completion_percent"
        
        print_success(f"Binder status: {result['status']}")
        print(f"   Completion: {result['completion_percent']}%")
        print(f"   Chapters: {result['chapters_complete']}/{result['chapters_total']}")
        print(f"   Last compiled: {result.get('last_compiled', 'Never')}")
        
        assert True
    except Exception as e:
        print_error(f"Error: {e}")
        assert False, "Test failed"


# ==========================================
# Test 7: Export Binder
# ==========================================

def test_export_binder():
    """Test exporting binder in specific format"""
    print_header("TEST: Export Binder")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v0/binder/{TEST_BINDER_ID}/export?format=markdown",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        assert result["status"] == "exported", "Expected 'exported' status"
        assert result["format"] == "markdown", "Format mismatch"
        
        print_success(f"Exported binder as: {result['format']}")
        print(f"   Binder ID: {result['binder_id']}")
        print(f"   Outputs: {len(result.get('outputs', []))}")
        print(f"   Compiled at: {result['compiled_at']}")
        
        assert True
    except Exception as e:
        print_error(f"Error: {e}")
        assert False, "Test failed"


# ==========================================
# Test 8: Delete Chapter
# ==========================================

def test_delete_chapter():
    """Test deleting chapter from binder"""
    print_header("TEST: Delete Chapter")
    
    try:
        response = requests.delete(
            f"{BASE_URL}/api/v0/binder/{TEST_BINDER_ID}/chapters/chapter-1",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        assert result["status"] == "deleted", "Expected 'deleted' status"
        
        print_success(f"Deleted chapter: {result['chapter_id']}")
        print(f"   Binder: {result['binder_id']}")
        
        assert True
    except Exception as e:
        print_error(f"Error: {e}")
        assert False, "Test failed"


# ==========================================
# Test 9: Invalid Format Error Handling
# ==========================================

def test_invalid_format():
    """Test error handling for invalid compile format"""
    print_header("TEST: Invalid Format Error Handling")
    
    try:
        payload = {
            "binder_id": TEST_BINDER_ID,
            "formats": ["invalid-format"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v0/binder/compile",
            json=payload,
            timeout=TIMEOUT
        )
        
        # Should return 400 error
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        error = response.json()
        assert "detail" in error, "Missing error detail"
        
        print_success("Invalid format correctly rejected")
        print(f"   Status: {response.status_code}")
        print(f"   Error: {error['detail']}")
        
        assert True
    except AssertionError as e:
        print_error(f"Assertion failed: {e}")
        assert False, "Test failed"
    except Exception as e:
        print_error(f"Error: {e}")
        assert False, "Test failed"


# ==========================================
# Main Test Runner
# ==========================================

def run_all_tests():
    """Run all binder compiler API tests"""
    print("\n" + "=" * 50)
    print(BLUE + "🧪 BINDER COMPILER API TESTS" + RESET)
    print("=" * 50)
    
    # Check server first
    if not check_server():
        assert False, "Test failed"
    
    # Run all tests
    tests = [
        ("Compile Binder", test_compile_binder),
        ("Get Chapters", test_get_chapters),
        ("Add Chapter", test_add_chapter),
        ("Get Chapter", test_get_chapter),
        ("Update Chapter", test_update_chapter),
        ("Binder Status", test_binder_status),
        ("Export Binder", test_export_binder),
        ("Delete Chapter", test_delete_chapter),
        ("Invalid Format", test_invalid_format),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print_error(f"Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = GREEN + "✅ PASS" + RESET if passed else RED + "❌ FAIL" + RESET
        print(f"{status} — {test_name}")
    
    print("\n" + "=" * 50)
    if passed_count == total_count:
        print(GREEN + f"✅ ALL BINDER COMPILER API TESTS PASSED ({passed_count}/{total_count})" + RESET)
    else:
        print(RED + f"❌ SOME TESTS FAILED ({passed_count}/{total_count} passed)" + RESET)
    print("=" * 50 + "\n")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
