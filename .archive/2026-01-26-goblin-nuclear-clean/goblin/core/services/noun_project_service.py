"""
Noun Project API Service for uDOS
Provides icon search and download functionality from The Noun Project.

API Documentation: https://api.thenounproject.com/documentation/
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("noun-project")


class NounProjectService:
    """
    Service for interacting with The Noun Project API.

    Features:
    - OAuth authentication
    - Icon search by keyword
    - Icon download (SVG/PNG)
    - Local caching system
    - Rate limiting awareness
    """

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize Noun Project service.

        Args:
            api_key: API key (default: from environment)
            api_secret: API secret (default: from environment)
        """
        self.api_key = api_key or os.getenv("NOUN_PROJECT_API_KEY")
        self.api_secret = api_secret or os.getenv("NOUN_PROJECT_SECRET")

        if not self.api_key or not self.api_secret:
            logger.warning(
                "[LOCAL] Noun Project API credentials not found in environment"
            )
            logger.warning(
                "[LOCAL] Set NOUN_PROJECT_API_KEY and NOUN_PROJECT_SECRET to enable"
            )

        self.base_url = "http://api.thenounproject.com"
        self.cache_dir = Path("memory/.cache/icons")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_index_file = self.cache_dir / "index.json"
        self.cache_index = self._load_cache_index()

        # Rate limiting (100 requests per hour for free tier)
        self.rate_limit = 100
        self.rate_window = timedelta(hours=1)
        self.request_history: List[datetime] = []

        logger.info(f"[LOCAL] Noun Project service initialized")
        logger.info(f"[LOCAL] Cache directory: {self.cache_dir}")

    def _load_cache_index(self) -> Dict[str, Any]:
        """Load cache index from disk."""
        if self.cache_index_file.exists():
            try:
                with open(self.cache_index_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[LOCAL] Failed to load cache index: {e}")
                return {"icons": {}, "searches": {}}
        return {"icons": {}, "searches": {}}

    def _save_cache_index(self):
        """Save cache index to disk."""
        try:
            with open(self.cache_index_file, "w") as f:
                json.dump(self.cache_index, f, indent=2)
        except Exception as e:
            logger.error(f"[LOCAL] Failed to save cache index: {e}")

    def _check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits.

        Returns:
            True if request can proceed, False if rate limited
        """
        now = datetime.now()
        # Remove old requests outside the time window
        self.request_history = [
            req_time
            for req_time in self.request_history
            if now - req_time < self.rate_window
        ]

        if len(self.request_history) >= self.rate_limit:
            oldest = min(self.request_history)
            wait_time = (oldest + self.rate_window - now).total_seconds()
            logger.warning(f"[LOCAL] Rate limit reached. Wait {wait_time:.0f} seconds")
            return False

        return True

    def _record_request(self):
        """Record a successful API request."""
        self.request_history.append(datetime.now())

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make authenticated request to Noun Project API.

        Args:
            endpoint: API endpoint (e.g., '/icon/1234')
            params: Query parameters

        Returns:
            JSON response or None on error
        """
        if not self.api_key or not self.api_secret:
            logger.error("[LOCAL] API credentials not configured")
            return None

        if not self._check_rate_limit():
            return None

        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(
                url,
                params=params or {},
                auth=(self.api_key, self.api_secret),
                timeout=10,
            )

            self._record_request()

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"[LOCAL] Resource not found: {endpoint}")
                return None
            elif response.status_code == 429:
                logger.warning("[LOCAL] Rate limit exceeded (429)")
                return None
            else:
                logger.error(
                    f"[LOCAL] API error: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"[LOCAL] Request failed: {e}")
            return None

    def search_icons(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        limit_to_public_domain: bool = False,
    ) -> Optional[List[Dict]]:
        """
        Search for icons by keyword.

        Args:
            query: Search keyword
            limit: Number of results (max 50)
            offset: Result offset for pagination
            limit_to_public_domain: Only return public domain icons

        Returns:
            List of icon metadata dicts or None on error
        """
        # Check cache first
        cache_key = f"{query}_{limit}_{offset}_{limit_to_public_domain}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()

        if cache_hash in self.cache_index.get("searches", {}):
            cached = self.cache_index["searches"][cache_hash]
            # Cache valid for 7 days
            if datetime.now().timestamp() - cached["timestamp"] < 7 * 24 * 60 * 60:
                logger.info(f"[LOCAL] Using cached search results for: {query}")
                return cached["results"]

        logger.info(f"[LOCAL] Searching icons: {query} (limit={limit})")

        params = {
            "query": query,
            "limit": min(limit, 50),  # API max is 50
            "offset": offset,
        }

        if limit_to_public_domain:
            params["limit_to_public_domain"] = 1

        response = self._make_request("/icons/" + query, params)

        if response and "icons" in response:
            results = response["icons"]

            # Cache the search results
            self.cache_index.setdefault("searches", {})[cache_hash] = {
                "query": query,
                "timestamp": datetime.now().timestamp(),
                "results": results,
            }
            self._save_cache_index()

            logger.info(f"[LOCAL] Found {len(results)} icons")
            return results

        return None

    def get_icon(self, icon_id: int) -> Optional[Dict]:
        """
        Get detailed icon information.

        Args:
            icon_id: Noun Project icon ID

        Returns:
            Icon metadata dict or None on error
        """
        logger.info(f"[LOCAL] Fetching icon: {icon_id}")

        response = self._make_request(f"/icon/{icon_id}")

        if response and "icon" in response:
            return response["icon"]

        return None

    def download_icon(
        self, icon_id: int, format: str = "svg", size: Optional[int] = None
    ) -> Optional[Path]:
        """
        Download icon to local cache.

        Args:
            icon_id: Noun Project icon ID
            format: 'svg' or 'png'
            size: PNG size in pixels (for PNG format only)

        Returns:
            Path to downloaded file or None on error
        """
        # Check if already cached
        cache_key = f"{icon_id}.{format}"
        if size and format == "png":
            cache_key = f"{icon_id}_{size}.png"

        cached_path = self.cache_dir / cache_key

        if cached_path.exists():
            logger.info(f"[LOCAL] Using cached icon: {cache_key}")
            return cached_path

        # Get icon metadata
        icon_data = self.get_icon(icon_id)
        if not icon_data:
            return None

        # Determine download URL
        if format == "svg":
            download_url = icon_data.get("icon_url")
        elif format == "png":
            if size:
                download_url = icon_data.get("preview_url_" + str(size))
            else:
                download_url = icon_data.get("preview_url")  # Default size
        else:
            logger.error(f"[LOCAL] Unsupported format: {format}")
            return None

        if not download_url:
            logger.error(f"[LOCAL] No download URL for icon {icon_id}")
            return None

        # Download the file
        logger.info(f"[LOCAL] Downloading icon {icon_id} as {format}")

        try:
            response = requests.get(download_url, timeout=30)
            response.raise_for_status()

            with open(cached_path, "wb") as f:
                f.write(response.content)

            # Update cache index
            self.cache_index.setdefault("icons", {})[str(icon_id)] = {
                "id": icon_id,
                "format": format,
                "size": size,
                "path": str(cached_path),
                "downloaded": datetime.now().timestamp(),
                "term": icon_data.get("term", "unknown"),
            }
            self._save_cache_index()

            logger.info(f"[LOCAL] Downloaded: {cached_path}")
            return cached_path

        except Exception as e:
            logger.error(f"[LOCAL] Download failed: {e}")
            return None

    def get_cached_icon(self, icon_id: int, format: str = "svg") -> Optional[Path]:
        """
        Get cached icon without downloading.

        Args:
            icon_id: Noun Project icon ID
            format: 'svg' or 'png'

        Returns:
            Path to cached file or None if not cached
        """
        cache_key = f"{icon_id}.{format}"
        cached_path = self.cache_dir / cache_key

        if cached_path.exists():
            return cached_path

        return None

    def clear_cache(self, older_than_days: Optional[int] = None):
        """
        Clear icon cache.

        Args:
            older_than_days: Only clear files older than N days (None = all)
        """
        logger.info(f"[LOCAL] Clearing cache (older_than_days={older_than_days})")

        if older_than_days is None:
            # Clear everything
            for file in self.cache_dir.glob("*"):
                if file.name != "index.json":
                    file.unlink()
            self.cache_index = {"icons": {}, "searches": {}}
            self._save_cache_index()
            logger.info("[LOCAL] Cache cleared")
        else:
            # Clear old files
            cutoff = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)
            cleared = 0

            for icon_id, data in list(self.cache_index.get("icons", {}).items()):
                if data.get("downloaded", 0) < cutoff:
                    file_path = Path(data["path"])
                    if file_path.exists():
                        file_path.unlink()
                    del self.cache_index["icons"][icon_id]
                    cleared += 1

            self._save_cache_index()
            logger.info(f"[LOCAL] Cleared {cleared} cached icons")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        icons = self.cache_index.get("icons", {})
        searches = self.cache_index.get("searches", {})

        total_size = sum(
            Path(data["path"]).stat().st_size
            for data in icons.values()
            if Path(data["path"]).exists()
        )

        return {
            "cached_icons": len(icons),
            "cached_searches": len(searches),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
        }


# Singleton instance
_service_instance: Optional[NounProjectService] = None


def get_noun_project_service() -> NounProjectService:
    """Get or create singleton Noun Project service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = NounProjectService()
    return _service_instance


# Example usage and testing
if __name__ == "__main__":
    import sys

    service = get_noun_project_service()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m core.services.noun_project_service search <query>")
        print("  python -m core.services.noun_project_service download <icon_id>")
        print("  python -m core.services.noun_project_service stats")
        sys.exit(1)

    command = sys.argv[1]

    if command == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else "document"
        results = service.search_icons(query, limit=5)

        if results:
            print(f'\nFound {len(results)} icons for "{query}":\n')
            for icon in results:
                print(f"  ID: {icon['id']}")
                print(f"  Term: {icon['term']}")
                print(f"  Attribution: {icon.get('attribution', 'N/A')}")
                print()
        else:
            print("No results found or API error")

    elif command == "download":
        icon_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        if not icon_id:
            print("Error: Provide icon ID")
            sys.exit(1)

        path = service.download_icon(icon_id)
        if path:
            print(f"Downloaded: {path}")
        else:
            print("Download failed")

    elif command == "stats":
        stats = service.get_cache_stats()
        print("\nCache Statistics:")
        print(f"  Cached icons: {stats['cached_icons']}")
        print(f"  Cached searches: {stats['cached_searches']}")
        print(f"  Total size: {stats['total_size_mb']} MB")
        print(f"  Cache dir: {stats['cache_dir']}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
