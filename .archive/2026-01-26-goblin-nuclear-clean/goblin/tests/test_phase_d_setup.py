"""
Phase D.1: Environment Setup Verification

Tests that all Phase D prerequisites are in place:
- Goblin server accessible
- Configuration file present
- Database path ready
- Sync directory ready
- Credentials available
"""

import os
import json
import subprocess
import requests
from pathlib import Path
from typing import Dict, Tuple


class PhaseDSetup:
    """Verify Phase D environment readiness"""
    
    def __init__(self):
        self.results = []
        self.errors = []
    
    def check_goblin_server(self) -> bool:
        """Test if Goblin server is running on port 8767"""
        try:
            r = requests.get("http://localhost:8767/health", timeout=2)
            if r.status_code == 200:
                data = r.json()
                self.results.append(f"✅ Goblin server running (v{data.get('version', 'unknown')})")
                return True
            else:
                self.errors.append(f"❌ Goblin server returned {r.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.errors.append("❌ Goblin server NOT running on port 8767")
            self.errors.append("   Run: dev/goblin/launch-goblin-dev.sh")
            return False
        except Exception as e:
            self.errors.append(f"❌ Server check failed: {e}")
            return False
    
    def check_config_file(self) -> Tuple[bool, Dict]:
        """Verify goblin.json configuration exists and is valid"""
        config_path = Path("dev/goblin/config/goblin.json")
        example_path = Path("dev/goblin/config/goblin.example.json")
        
        if not config_path.exists():
            self.errors.append("❌ Goblin config missing: dev/goblin/config/goblin.json")
            self.errors.append(f"   Copy from: {example_path}")
            return False, {}
        
        try:
            with open(config_path) as f:
                config = json.load(f)
            
            # Check required sections
            required = ["server", "notion", "database"]
            missing = [k for k in required if k not in config]
            
            if missing:
                self.errors.append(f"❌ Config missing sections: {missing}")
                return False, {}
            
            self.results.append(f"✅ Goblin config exists and valid")
            return True, config
            
        except json.JSONDecodeError as e:
            self.errors.append(f"❌ Config JSON invalid: {e}")
            return False, {}
        except Exception as e:
            self.errors.append(f"❌ Config read failed: {e}")
            return False, {}
    
    def check_credentials(self) -> Dict[str, bool]:
        """Check if Notion credentials are in macOS keychain"""
        results = {}
        
        # Check API token
        try:
            token = subprocess.check_output(
                ["security", "find-generic-password", "-w", 
                 "-a", os.environ.get("USER", ""), 
                 "-s", "goblin-notion-token"],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            
            if token:
                # Check token format - Accept both secret_ (old) and ntn_ (new) formats
                if token.startswith("secret_") or token.startswith("ntn_"):
                    token_type = "legacy (secret_)" if token.startswith("secret_") else "new (ntn_)"
                    self.results.append(f"✅ Notion API token in keychain ({token_type})")
                    results["token"] = True
                else:
                    self.errors.append(f"❌ Notion token has unexpected format (starts with '{token[:4]}')")
                    self.errors.append("   Integration tokens should start with 'secret_' or 'ntn_'")
                    results["token"] = False
            else:
                self.errors.append("❌ Notion token is empty")
                results["token"] = False
                
        except subprocess.CalledProcessError:
            self.errors.append("❌ Notion API token NOT in keychain")
            self.errors.append("   Run: security add-generic-password -a \"$USER\" -s \"goblin-notion-token\" -w \"secret_YOUR_TOKEN\"")
            results["token"] = False
        
        # Check webhook secret
        try:
            secret = subprocess.check_output(
                ["security", "find-generic-password", "-w",
                 "-a", os.environ.get("USER", ""),
                 "-s", "goblin-notion-webhook"],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            
            if secret and len(secret) >= 32:
                self.results.append("✅ Webhook secret in keychain")
                results["webhook"] = True
            else:
                self.errors.append("❌ Webhook secret exists but too short")
                results["webhook"] = False
                
        except subprocess.CalledProcessError:
            self.errors.append("❌ Webhook secret NOT in keychain")
            self.errors.append("   Run: openssl rand -hex 32 | xargs security add-generic-password -a \"$USER\" -s \"goblin-notion-webhook\" -w")
            results["webhook"] = False
        
        return results
    
    def check_database_path(self) -> bool:
        """Ensure database directory exists"""
        db_path = Path("memory/goblin/sync.db")
        
        # Create parent directory if needed
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        if db_path.parent.exists():
            self.results.append(f"✅ Database directory ready: {db_path.parent}")
            return True
        else:
            self.errors.append(f"❌ Cannot create database directory: {db_path.parent}")
            return False
    
    def check_sync_directory(self) -> bool:
        """Ensure sync directory exists"""
        sync_dir = Path("memory/synced")
        
        # Create if needed
        sync_dir.mkdir(parents=True, exist_ok=True)
        
        if sync_dir.exists():
            self.results.append(f"✅ Sync directory ready: {sync_dir}")
            # Check write permissions
            test_file = sync_dir / ".test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                self.results.append("✅ Sync directory writable")
                return True
            except Exception as e:
                self.errors.append(f"❌ Sync directory not writable: {e}")
                return False
        else:
            self.errors.append(f"❌ Cannot create sync directory: {sync_dir}")
            return False
    
    def check_notion_api_connectivity(self) -> bool:
        """Test if we can reach Notion API (requires token)"""
        try:
            token = subprocess.check_output(
                ["security", "find-generic-password", "-w",
                 "-a", os.environ.get("USER", ""),
                 "-s", "goblin-notion-token"],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            
            if not token:
                self.errors.append("⚠️  Cannot test Notion API (no token)")
                return False
            
            # Test Notion API with /users/me endpoint
            r = requests.get(
                "https://api.notion.com/v1/users/me",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Notion-Version": "2022-06-28"
                },
                timeout=5
            )
            
            if r.status_code == 200:
                user = r.json()
                bot_name = user.get("name", "Unknown")
                self.results.append(f"✅ Notion API connectivity verified (Bot: {bot_name})")
                return True
            else:
                self.errors.append(f"❌ Notion API returned {r.status_code}: {r.text}")
                return False
                
        except subprocess.CalledProcessError:
            self.errors.append("⚠️  Cannot test Notion API (no token in keychain)")
            return False
        except requests.exceptions.RequestException as e:
            self.errors.append(f"❌ Notion API connection failed: {e}")
            return False
    
    def run_all_checks(self) -> Dict:
        """Run all environment checks"""
        print("=" * 60)
        print("Phase D.1: Environment Setup Verification")
        print("=" * 60)
        print()
        
        checks = {
            "server": self.check_goblin_server(),
            "config": self.check_config_file()[0],
            "credentials": all(self.check_credentials().values()),
            "database": self.check_database_path(),
            "sync_dir": self.check_sync_directory(),
            "notion_api": self.check_notion_api_connectivity()
        }
        
        # Print results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        
        for msg in self.results:
            print(msg)
        
        if self.errors:
            print("\n" + "-" * 60)
            print("ERRORS / WARNINGS")
            print("-" * 60)
            for msg in self.errors:
                print(msg)
        
        # Summary
        print("\n" + "=" * 60)
        passed = sum(checks.values())
        total = len(checks)
        
        if passed == total:
            print(f"🎉 ALL CHECKS PASSED ({passed}/{total})")
            print("\n✅ Phase D.1 READY - Proceed to Phase D.2 (Webhook Testing)")
        else:
            print(f"⚠️  CHECKS: {passed}/{total} passed, {total - passed} failed")
            print("\n❌ Fix errors above before proceeding to Phase D.2")
        
        print("=" * 60)
        
        return {
            "passed": passed,
            "total": total,
            "ready": passed == total,
            "checks": checks
        }


def main():
    """Run Phase D.1 setup verification"""
    verifier = PhaseDSetup()
    result = verifier.run_all_checks()
    
    # Exit code: 0 if ready, 1 if not
    exit(0 if result["ready"] else 1)


if __name__ == "__main__":
    main()
