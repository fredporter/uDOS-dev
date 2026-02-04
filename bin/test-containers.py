#!/usr/bin/env python3
"""
Container Testing Workflow Automation

Calls Goblin dev endpoints to validate all containers and writes a summary report.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _request_json(url: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None) -> Any:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    with urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def _list_containers(base_url: str) -> List[str]:
    data = _request_json(f"{base_url}/api/dev/containers")
    return [entry["name"] for entry in data.get("containers", [])]


def _test_container(base_url: str, name: str) -> Dict[str, Any]:
    return _request_json(
        f"{base_url}/api/dev/containers/test/{name}",
        method="POST",
        payload={"validate_only": True},
    )


def _write_report(report: Dict[str, Any], out_path: Optional[Path]) -> Path:
    if out_path is None:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        out_path = _repo_root() / "vault" / "07_LOGS" / f"container_tests_{stamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Goblin container tests.")
    parser.add_argument("--host", default="http://127.0.0.1:8767", help="Goblin server base URL")
    parser.add_argument("--container", action="append", help="Container name to test (repeatable)")
    parser.add_argument("--out", help="Write report to this path")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any errors")
    args = parser.parse_args()

    base_url = args.host.rstrip("/")
    try:
        containers = args.container or _list_containers(base_url)
    except (HTTPError, URLError) as exc:
        print(f"❌ Unable to reach Goblin server at {base_url}: {exc}")
        print("Start Goblin with: python dev/goblin/goblin_server.py")
        return 1

    if not containers:
        print("⚠️ No containers found to test.")
        return 0

    results: List[Dict[str, Any]] = []
    failures = 0
    for name in containers:
        try:
            result = _test_container(base_url, name)
            results.append(result)
            if result.get("errors"):
                failures += 1
            status = result.get("status", "unknown")
            print(f"{'✅' if status == 'ok' else '⚠️'} {name}: {status}")
        except (HTTPError, URLError) as exc:
            failures += 1
            results.append({"status": "error", "container": name, "errors": [str(exc)]})
            print(f"❌ {name}: {exc}")

    report = {
        "server": base_url,
        "containers_tested": len(results),
        "failures": failures,
        "results": results,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    out_path = _write_report(report, Path(args.out) if args.out else None)
    print(f"🧾 Report written: {out_path}")

    if args.strict and failures > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
