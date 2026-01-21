#!/usr/bin/env python3
"""
Test ConfigFramework directly
"""

import sys
import json
from pathlib import Path

# Add project root dynamically
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

try:
    from public.wizard.services.config_framework import ConfigFramework

    # Create instance
    framework = ConfigFramework()

    # Get registry by category
    registry = framework.get_registry_by_category()

    print(f"✅ Framework loaded successfully")
    print(f"   Categories: {list(registry.keys())}")
    print()

    # Build response like the API does
    response = {
        "status": "success",
        "total": sum(len(apis) for apis in registry.values()),
        "categories": {
            cat: {
                "count": len(apis),
                "apis": apis,
            }
            for cat, apis in registry.items()
        }
    }

    print("Response structure:")
    print(f"  - status: {response['status']}")
    print(f"  - total: {response['total']}")
    print(f"  - categories: {len(response['categories'])} categories")

    # Print each category
    for cat, info in response['categories'].items():
        apis = info['apis']
        print(f"\n  📋 {cat}:")
        for api in apis[:2]:  # Just show first 2 APIs per category
            print(f"     - {api['name']}: {api['status']}")
        if len(apis) > 2:
            print(f"     ... and {len(apis) - 2} more")

    # Verify status values are uppercase
    print("\n✅ Verification:")
    all_statuses = []
    for cat, info in response['categories'].items():
        for api in info['apis']:
            all_statuses.append(api['status'])

    unique_statuses = set(all_statuses)
    print(f"   Unique statuses: {sorted(unique_statuses)}")

    # Check if uppercase
    expected = {'CONNECTED', 'PARTIAL', 'MISSING', 'ERROR'}
    if unique_statuses.issubset(expected):
        print("   ✅ All statuses are UPPERCASE (correct)")
    else:
        print(f"   ❌ Unexpected statuses: {unique_statuses - expected}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
