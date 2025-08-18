#!/usr/bin/env python3
"""
Apply all database migrations for the enhanced briefing system
Run this script when Supabase is in write mode
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def apply_all_migrations():
    """Print all migrations for manual application on Supabase website."""
    print("🚀 DATABASE MIGRATIONS TO APPLY")
    print("=" * 60)
    print("Copy and paste each SQL block into the Supabase SQL Editor")
    print("=" * 60)
    
    # Migration files in order
    migration_files = [
        "migrations/001_create_topics_table.sql",
        "migrations/002_create_topic_subscriptions_table.sql", 
        "migrations/003_create_topic_briefings_table.sql",
        "migrations/004_update_briefings_table.sql",
        "migrations/005_populate_topics_table.sql"
    ]
    
    for i, migration_file in enumerate(migration_files, 1):
        print(f"\n{'='*20} MIGRATION {i} {'='*20}")
        print(f"File: {migration_file}")
        print("="*60)
        
        try:
            # Read migration file
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            print(sql_content)
            print("="*60)
            print(f"✅ Copy the above SQL and run it in Supabase SQL Editor")
                
        except FileNotFoundError:
            print(f"   ❌ Migration file not found: {migration_file}")
        except Exception as e:
            print(f"   ❌ Error reading migration: {str(e)}")
    
    print(f"\n🏁 All migrations printed above!")
    print(f"\n💡 After applying migrations manually:")
    print(f"   python verify_database_schema.py")


if __name__ == "__main__":
    asyncio.run(apply_all_migrations())