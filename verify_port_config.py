#!/usr/bin/env python3
"""
Verify port configuration for health checker
"""

import os
import re

def verify_port_config():
    """Verify that all files use the correct port (8080)"""
    print("🔍 Verifying Port Configuration (8080)")
    print("=" * 40)

    issues = []

    # Check Dockerfile
    print("1. Checking Dockerfile...")
    with open('Dockerfile', 'r') as f:
        dockerfile_content = f.read()
        if 'EXPOSE 8080' in dockerfile_content:
            print("   ✅ Dockerfile exposes port 8080")
        else:
            print("   ❌ Dockerfile does not expose port 8080")
            issues.append("Dockerfile EXPOSE port")

    # Check nexus_loader.py
    print("2. Checking nexus_loader.py...")
    with open('nexus_loader.py', 'r') as f:
        loader_content = f.read()
        if "'PORT', '8080'" in loader_content:
            print("   ✅ nexus_loader.py uses port 8080 as default")
        else:
            print("   ❌ nexus_loader.py does not use port 8080 as default")
            issues.append("nexus_loader.py default port")

    # Check railway.json
    print("3. Checking railway.json...")
    with open('railway.json', 'r') as f:
        railway_content = f.read()
        if '"healthcheckPath": "/health"' in railway_content:
            print("   ✅ railway.json has health check configured")
        else:
            print("   ❌ railway.json missing health check config")
            issues.append("railway.json health check")

    # Check health checker docs
    print("4. Checking health checker documentation...")
    doc_path = 'docs/health_checker_README.md'
    if os.path.exists(doc_path):
        with open(doc_path, 'r') as f:
            doc_content = f.read()
            if "default: 8080" in doc_content:
                print("   ✅ Documentation mentions port 8080")
            else:
                print("   ❌ Documentation does not mention port 8080")
                issues.append("Documentation port reference")

    # Summary
    print("\n" + "=" * 40)
    if issues:
        print(f"❌ Found {len(issues)} configuration issues:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("✅ All port configurations are correct!")
        print("🎯 Health checker will use port 8080")
        print("🌐 Railway URL: https://nexus-core-production.up.railway.app/health")
        return True

if __name__ == "__main__":
    success = verify_port_config()
    if not success:
        exit(1)
