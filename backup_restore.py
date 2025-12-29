#!/usr/bin/env python3
"""
Nexus Trading Bot - Backup & Restore Utility
Permite restaurar backups creados durante el deploy
"""

import os
import sys
import shutil
import argparse
from datetime import datetime

def list_backups(backup_dir="backups"):
    """List all available backups"""
    if not os.path.exists(backup_dir):
        print("❌ No hay backups disponibles")
        return []
    
    backups = []
    for item in os.listdir(backup_dir):
        backup_path = os.path.join(backup_dir, item)
        if os.path.isdir(backup_path):
            mtime = os.path.getmtime(backup_path)
            backups.append({
                'name': item,
                'path': backup_path,
                'date': datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
    
    backups.sort(key=lambda x: x['date'], reverse=True)
    return backups

def restore_backup(backup_path, dry_run=False):
    """Restore files from backup"""
    if not os.path.exists(backup_path):
        print(f"❌ Backup no encontrado: {backup_path}")
        return False
    
    print(f"📦 Restaurando desde: {backup_path}")
    
    restored = 0
    for root, dirs, files in os.walk(backup_path):
        # Calculate relative path
        rel_path = os.path.relpath(root, backup_path)
        if rel_path == '.':
            target_dir = '.'
        else:
            target_dir = rel_path
        
        # Create target directory if needed
        if target_dir != '.' and not os.path.exists(target_dir):
            if not dry_run:
                os.makedirs(target_dir)
            print(f"📁 Creando directorio: {target_dir}")
        
        # Copy files
        for file in files:
            src = os.path.join(root, file)
            if target_dir == '.':
                dst = file
            else:
                dst = os.path.join(target_dir, file)
            
            if not dry_run:
                shutil.copy2(src, dst)
            print(f"  ✅ {dst}")
            restored += 1
    
    if dry_run:
        print(f"\n🔍 DRY-RUN: Se restaurarían {restored} archivos")
    else:
        print(f"\n✅ Restaurados {restored} archivos")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Backup & Restore Utility para Nexus Trading Bot')
    parser.add_argument('action', choices=['list', 'restore'], help='Acción a realizar')
    parser.add_argument('--backup', type=str, help='Nombre del backup a restaurar (para restore)')
    parser.add_argument('--dry-run', action='store_true', help='Simular sin hacer cambios')
    
    args = parser.parse_args()
    
    if args.action == 'list':
        print("📦 Backups disponibles:\n")
        backups = list_backups()
        if backups:
            for i, backup in enumerate(backups, 1):
                print(f"{i}. {backup['name']}")
                print(f"   Fecha: {backup['date']}")
                print()
        else:
            print("No hay backups disponibles")
    
    elif args.action == 'restore':
        if not args.backup:
            print("❌ Debes especificar el nombre del backup con --backup")
            print("\n💡 Usa 'list' para ver backups disponibles:")
            print("   python backup_restore.py list")
            sys.exit(1)
        
        backup_path = os.path.join("backups", args.backup)
        if not os.path.exists(backup_path):
            print(f"❌ Backup no encontrado: {args.backup}")
            print("\n💡 Backups disponibles:")
            backups = list_backups()
            for backup in backups[:5]:
                print(f"   - {backup['name']}")
            sys.exit(1)
        
        if args.dry_run:
            print("🔍 MODO DRY-RUN: No se harán cambios reales\n")
        
        response = input(f"¿Restaurar backup '{args.backup}'? (s/N): ").strip().lower()
        if response != 's':
            print("❌ Restauración cancelada")
            sys.exit(0)
        
        restore_backup(backup_path, dry_run=args.dry_run)

if __name__ == "__main__":
    main()

