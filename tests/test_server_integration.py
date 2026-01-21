#!/usr/bin/env python3
"""
Test Server Integration
"""

import sys
sys.path.insert(0, '/Users/fredbook/Code/uDOS')

try:
    print("Testing server components...")

    # Test 1: Import ConfigFramework
    from public.wizard.services.config_framework import ConfigFramework, get_config_framework
    print("✅ ConfigFramework imported")

    # Test 2: Import FastAPI
    from fastapi import FastAPI, Depends
    print("✅ FastAPI imported")

    # Test 3: Import config routes
    from public.wizard.routes.config import router
    print("✅ config router imported")

    # Test 4: Create a test app
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/config")
    print("✅ Router included in app")

    # Test 5: Check routes
    routes = [route.path for route in app.routes]
    print(f"✅ Routes registered: {len(routes)} routes")

    # Check for framework/registry
    framework_routes = [r for r in routes if 'framework' in r]
    if framework_routes:
        print(f"✅ Framework routes found: {framework_routes}")
    else:
        print("❌ No framework routes found")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
