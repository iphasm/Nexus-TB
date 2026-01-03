#!/usr/bin/env python3
"""
VERIFICACIÓN: Fix de datetime imports locales
===========================================

Verifica que todos los imports de datetime estén correctamente definidos
y que no haya problemas de scope que causen errores.
"""

import os
import sys

def check_file_imports(filepath):
    """Check if a file has proper datetime imports."""
    print(f"\n🔍 Checking {filepath}...")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for global datetime import
        has_global_import = 'from datetime import' in content and 'import datetime' not in [line.strip() for line in content.split('\n') if 'import datetime' in line and 'from datetime' not in line]

        # Check for problematic local imports
        lines = content.split('\n')
        local_imports = []
        for i, line in enumerate(lines, 1):
            if 'import datetime' in line and 'from datetime' not in line:
                local_imports.append(f"Line {i}: {line.strip()}")

        if has_global_import:
            print("  ✅ Has global datetime import")
        else:
            print("  ❌ Missing global datetime import")

        if local_imports:
            print("  ⚠️  Found local datetime imports:")
            for imp in local_imports:
                print(f"     {imp}")
        else:
            print("  ✅ No problematic local imports")

        return has_global_import and not local_imports

    except Exception as e:
        print(f"  ❌ Error checking file: {e}")
        return False

def main():
    print("🔬 VERIFICACIÓN: Fix de datetime imports")
    print("=" * 50)

    # Files to check
    files_to_check = [
        'servos/ai_analyst.py',
        'servos/db.py',
        'nexus_loader.py',
        'servos/voight_kampff.py'
    ]

    all_good = True

    for filepath in files_to_check:
        if os.path.exists(filepath):
            result = check_file_imports(filepath)
            if not result:
                all_good = False
        else:
            print(f"\n❌ File not found: {filepath}")
            all_good = False

    print(f"\n{'='*50}")
    if all_good:
        print("🎉 VERIFICACIÓN EXITOSA: Todos los imports de datetime están correctos")
        print("   No debería haber más errores de 'datetime not defined'")
    else:
        print("⚠️  VERIFICACIÓN FALLIDA: Hay problemas con los imports de datetime")
        print("   Revisar los archivos marcados con ❌")

    # Test import functionality
    print(f"\n🔧 Testing imports...")
    try:
        from servos.ai_analyst import NexusAnalyst
        from servos.db import get_connection
        from datetime import datetime

        # Test datetime usage
        now = datetime.now()
        print(f"✅ datetime.now() funciona: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # Test NexusAnalyst instantiation (should not crash on datetime)
        analyst = NexusAnalyst()
        print("✅ NexusAnalyst se instancia sin errores de datetime")

    except Exception as e:
        print(f"❌ Error durante testing: {e}")
        all_good = False

    return all_good

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
