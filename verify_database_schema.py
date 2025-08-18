#!/usr/bin/env python3
"""
Verify the new database schema and test topic/briefing functionality
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.supabase_service import SupabaseService

async def verify_database_schema():
    """Verify all new tables and relationships exist."""
    print("🔍 VERIFYING DATABASE SCHEMA")
    print("=" * 60)
    
    supabase_service = SupabaseService()
    
    # Test queries to verify schema
    test_queries = [
        {
            "name": "Topics Table",
            "query": "SELECT COUNT(*) as topic_count FROM topics WHERE is_active = true;"
        },
        {
            "name": "Sample Topics",
            "query": "SELECT name, display_name, category FROM topics WHERE category = 'technology' LIMIT 3;"
        },
        {
            "name": "Topics by Category",
            "query": "SELECT category, COUNT(*) as count FROM topics GROUP BY category ORDER BY category;"
        },
        {
            "name": "Updated Briefings Table", 
            "query": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'briefings' AND column_name IN ('user_id', 'blurb', 'briefing_time');"
        },
        {
            "name": "Topic Subscriptions Table",
            "query": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'topic_subscriptions' LIMIT 5;"
        },
        {
            "name": "Topic Briefings Table", 
            "query": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'topic_briefings' LIMIT 5;"
        }
    ]
    
    for test in test_queries:
        print(f"\n📊 Testing: {test['name']}")
        try:
            result = await supabase_service.execute_sql(test['query'])
            if result:
                print(f"   ✅ Success: {result}")
            else:
                print(f"   ❌ No result returned")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print(f"\n✅ Schema verification completed!")


async def test_topic_operations():
    """Test topic subscription and briefing operations."""
    print(f"\n\n🧪 TESTING TOPIC OPERATIONS")
    print("=" * 60)
    
    supabase_service = SupabaseService()
    
    # Test sample operations
    operations = [
        {
            "name": "Get Available Topics",
            "query": "SELECT COUNT(*) as available_topics FROM topics WHERE is_active = true;"
        },
        {
            "name": "Get Topics by Category",
            "query": "SELECT category, COUNT(*) FROM topics WHERE is_active = true GROUP BY category;"
        },
        {
            "name": "Find Biotechnology Topic",
            "query": "SELECT id, name, display_name FROM topics WHERE name = 'biotechnology';"
        }
    ]
    
    for operation in operations:
        print(f"\n🔍 {operation['name']}")
        try:
            result = await supabase_service.execute_sql(operation['query'])
            print(f"   ✅ {result}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")


async def show_usage_examples():
    """Show example queries for common operations."""
    print(f"\n\n📋 USAGE EXAMPLES")
    print("=" * 60)
    
    examples = [
        {
            "description": "Check daily free briefing limit",
            "sql": """
SELECT COUNT(*) as daily_free_briefings
FROM briefings 
WHERE user_id = '12345678-1234-5678-9abc-123456789abc'
  AND briefing_date = CURRENT_DATE 
  AND tier = 'free';
-- Should return 0 or 1 (limit: 1)
            """.strip()
        },
        {
            "description": "Check topic briefing limit for specific topic",
            "sql": """
SELECT COUNT(*) as daily_topic_briefings
FROM topic_briefings 
WHERE user_id = '12345678-1234-5678-9abc-123456789abc'
  AND topic_id = (SELECT id FROM topics WHERE name = 'biotechnology')
  AND briefing_date = CURRENT_DATE;
-- Should return 0 or 1 (limit: 1 per topic)
            """.strip()
        },
        {
            "description": "Get user's subscribed topics for homepage",
            "sql": """
SELECT t.name, t.display_name, t.category
FROM topics t
JOIN topic_subscriptions ts ON t.id = ts.topic_id
WHERE ts.user_id = '12345678-1234-5678-9abc-123456789abc' 
  AND ts.is_active = true
ORDER BY ts.priority, t.display_name;
            """.strip()
        },
        {
            "description": "Get recent briefings for user homepage",
            "sql": """
-- Daily briefings
SELECT 'daily' as type, title, briefing_type as subtype, briefing_date, briefing_time, blurb
FROM briefings
WHERE user_id = '12345678-1234-5678-9abc-123456789abc'

UNION ALL

-- Topic briefings  
SELECT 'topic' as type, tb.title, t.display_name as subtype, tb.briefing_date, tb.briefing_time, tb.blurb
FROM topic_briefings tb
JOIN topics t ON tb.topic_id = t.id
WHERE tb.user_id = '12345678-1234-5678-9abc-123456789abc'

ORDER BY briefing_time DESC
LIMIT 10;
            """.strip()
        }
    ]
    
    for example in examples:
        print(f"\n📋 {example['description']}:")
        print(f"```sql\n{example['sql']}\n```")
    
    print(f"\n✅ Usage examples documented!")


async def main():
    """Run all verification tests."""
    await verify_database_schema()
    await test_topic_operations() 
    await show_usage_examples()
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"1. Apply migrations: python apply_database_migrations.py")
    print(f"2. Update briefing generators to save to database")
    print(f"3. Add daily usage limit checks to API endpoints")
    print(f"4. Create user dashboard queries for homepage")


if __name__ == "__main__":
    asyncio.run(main())