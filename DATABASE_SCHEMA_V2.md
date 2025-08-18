# MarketMotion Database Schema V2

## Overview

Enhanced database structure supporting user-specific briefings, topic subscriptions, and daily usage limits.

## Schema Changes Summary

### New Tables
1. **`topics`** - Stock market sectors and industries for topic briefings
2. **`topic_subscriptions`** - User subscriptions to specific topics
3. **`topic_briefings`** - Topic-specific briefings for users

### Updated Tables
1. **`briefings`** - Added user association and highlight blurbs

## Detailed Table Structures

### 1. `topics` Table
Stores available topics for subscription and briefing generation.

```sql
CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,              -- "biotechnology", "artificial_intelligence"
    display_name TEXT NOT NULL,             -- "Biotechnology", "Artificial Intelligence"
    category TEXT NOT NULL,                 -- "healthcare", "technology", "energy", etc.
    description TEXT,                       -- Brief topic description
    is_active BOOLEAN DEFAULT true,         -- Whether topic is available for subscription
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Initial Stock Market Sectors (30 topics):**
- **Healthcare**: biotechnology, pharmaceutical, medical_devices, healthcare_services
- **Technology**: artificial_intelligence, software, semiconductors, cybersecurity, cloud_computing
- **Energy**: renewable_energy, oil_gas, electric_vehicles, nuclear_energy
- **Finance**: banking, fintech, insurance, real_estate
- **Industrial**: aerospace_defense, manufacturing, transportation, construction
- **Consumer**: retail, food_beverage, entertainment, automotive
- **Materials**: metals_mining, chemicals
- **Utilities**: utilities
- **Communication**: telecommunications, media

### 2. `topic_subscriptions` Table
Manages user subscriptions to topics.

```sql
CREATE TABLE topic_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    subscribed_at TIMESTAMPTZ DEFAULT now(),
    is_active BOOLEAN DEFAULT true,         -- Active subscription
    notification_enabled BOOLEAN DEFAULT true, -- For future notifications
    priority INTEGER DEFAULT 1,            -- Topic ordering on dashboard
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, topic_id)
);
```

### 3. `topic_briefings` Table
Stores topic-specific briefings for users.

```sql
CREATE TABLE topic_briefings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    title TEXT NOT NULL,                    -- "Biotechnology News - August 18, 2025"
    briefing_date DATE NOT NULL,
    briefing_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    word_count INTEGER,
    duration_seconds INTEGER,
    text_content TEXT,
    audio_file_path TEXT,
    text_file_path TEXT,
    blurb TEXT,                            -- 2-sentence highlights
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, topic_id, briefing_date) -- One per user per topic per day
);
```

### 4. Updated `briefings` Table
Enhanced existing table for user association.

```sql
-- New columns added:
ALTER TABLE briefings ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE briefings ADD COLUMN blurb TEXT;
ALTER TABLE briefings ADD COLUMN briefing_time TIMESTAMPTZ DEFAULT now();

-- Updated briefing_type constraint:
CHECK (briefing_type IN ('morning', 'midday', 'evening', 'free_morning', 'free_midday', 'free_evening', 'custom', 'premium_morning', 'premium_midday', 'premium_evening'))
```

## User Access Rules

### Free Users
- **Daily Briefings**: 1 short free briefing per day
- **Topic Briefings**: None
- **Access**: Only `briefings` where `tier = 'free'` and `user_id = their_id`

### Premium Users  
- **Daily Briefings**: 3 daily briefings (morning, midday, evening)
- **Topic Briefings**: 1 per subscribed topic per day
- **Access**: All `briefings` where `user_id = their_id`, plus all `topic_briefings`

## Daily Usage Limits Implementation

### Free User Limit Check
```sql
-- Check if free user has used their daily briefing
SELECT COUNT(*) 
FROM briefings 
WHERE user_id = $1 
  AND briefing_date = CURRENT_DATE 
  AND tier = 'free';
-- Limit: 1
```

### Topic Briefing Limit Check
```sql
-- Check if user has used their daily topic briefing for specific topic
SELECT COUNT(*) 
FROM topic_briefings 
WHERE user_id = $1 
  AND topic_id = $2 
  AND briefing_date = CURRENT_DATE;
-- Limit: 1 per topic
```

### Premium User Daily Briefings
```sql
-- Check premium user daily briefing usage
SELECT COUNT(*) 
FROM briefings 
WHERE user_id = $1 
  AND briefing_date = CURRENT_DATE 
  AND tier = 'premium';
-- Limit: 3
```

## Queries for Homepage Display

### User's Topic Subscriptions
```sql
SELECT t.id, t.name, t.display_name, t.category, ts.priority
FROM topics t
JOIN topic_subscriptions ts ON t.id = ts.topic_id
WHERE ts.user_id = $1 AND ts.is_active = true
ORDER BY ts.priority, t.display_name;
```

### Recent Topic Briefings for User
```sql
SELECT tb.title, tb.briefing_date, tb.briefing_time, tb.blurb, t.display_name
FROM topic_briefings tb
JOIN topics t ON tb.topic_id = t.id
WHERE tb.user_id = $1
ORDER BY tb.briefing_time DESC
LIMIT 10;
```

### Recent Daily Briefings for User
```sql
SELECT title, briefing_type, briefing_date, briefing_time, blurb
FROM briefings
WHERE user_id = $1
ORDER BY briefing_time DESC
LIMIT 10;
```

## Migration Application Order

1. `001_create_topics_table.sql`
2. `002_create_topic_subscriptions_table.sql` 
3. `003_create_topic_briefings_table.sql`
4. `004_update_briefings_table.sql`
5. `005_populate_topics_table.sql`

## Row Level Security (RLS)

All tables have RLS enabled:
- **Users see only their own data**
- **Public briefings visible to everyone** (for free tier)
- **Topics visible to all users** (for subscription selection)

## Future Enhancements

### Planned Features
- Notification preferences per topic
- Topic priority ordering for dashboard
- Briefing scheduling and automation
- Usage analytics and reporting
- Topic popularity tracking

### Extensible Design
- `metadata` JSONB columns for flexible data storage
- `is_active` flags for soft deletion
- `priority` fields for custom ordering
- Foreign key constraints for data integrity

## Integration with Briefing Generators

### Daily Briefings
```python
# Save to briefings table with user association
await supabase_service.save_briefing(
    user_id=user_id,
    title="Morning Market Update - August 18, 2025",
    briefing_type="premium_morning",
    text_content=briefing_text,
    audio_file_path=audio_path,
    blurb="Markets opened mixed with tech stocks leading gains. Fed minutes show dovish sentiment."
)
```

### Topic Briefings
```python
# Save to topic_briefings table
await supabase_service.save_topic_briefing(
    user_id=user_id,
    topic_id=topic_id,
    title="Biotechnology News - August 18, 2025", 
    text_content=briefing_text,
    audio_file_path=audio_path,
    blurb="Gene therapy breakthrough announced. Two major pharma mergers reported."
)
```

---

*Ready for implementation when Supabase is in write mode*