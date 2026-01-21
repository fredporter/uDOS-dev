#!/usr/bin/env python3
"""
Test Server Routes After Fix
"""

import sys
from pathlib import Path

# Add project root dynamically
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

try:
    print("Testing fixed server components...")

    # Test 1: Import and create server
    from public.wizard.server import WizardServer
    print("✅ WizardServer imported")

    # Test 2: Create the app
    server = WizardServer()
    app = server.create_app()
    print("✅ App created")

    # Test 3: Check routes
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append(route.path)

    print(f"✅ Routes registered: {len(routes)} routes")

    # Check for specific endpoints
    important_routes = [
        '/api/v1/config/framework/registry',
        '/api/v1/config/framework/status',
        '/api/v1/config/dashboard',
        '/api/v1/config/editor/files',
        '/api/v1/config/editor/read',
        '/api/v1/config/editor/write',
    ]

    print("\n📍 Important endpoints:")
    for route in important_routes:
        if route in routes:
            print(f"  ✅ {route}")
        else:
            print(f"  ❌ {route} - NOT FOUND")

    # List all config routes
    config_routes = [r for r in routes if '/config' in r]
    print(f"\n📋 All config routes ({len(config_routes)}):")
    for route in sorted(config_routes):
        print(f"  - {route}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
