-- Migration: Create topic_subscriptions table for user topic subscriptions
-- File: 002_create_topic_subscriptions_table.sql

-- Create topic_subscriptions table
CREATE TABLE topic_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    subscribed_at TIMESTAMPTZ DEFAULT now(),
    is_active BOOLEAN DEFAULT true,
    notification_enabled BOOLEAN DEFAULT true, -- For future notification features
    priority INTEGER DEFAULT 1, -- For ordering topics on user dashboard
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    -- Ensure one subscription per user per topic
    UNIQUE(user_id, topic_id)
);

-- Add RLS policies for topic subscriptions
ALTER TABLE topic_subscriptions ENABLE ROW LEVEL SECURITY;

-- Users can only see their own subscriptions
CREATE POLICY "Users can view own topic subscriptions" ON topic_subscriptions
    FOR SELECT USING (auth.uid() = user_id);

-- Users can manage their own subscriptions
CREATE POLICY "Users can manage own topic subscriptions" ON topic_subscriptions
    FOR ALL USING (auth.uid() = user_id);

-- Create indexes for efficient querying
CREATE INDEX idx_topic_subscriptions_user_id ON topic_subscriptions(user_id);
CREATE INDEX idx_topic_subscriptions_topic_id ON topic_subscriptions(topic_id);
CREATE INDEX idx_topic_subscriptions_active ON topic_subscriptions(user_id, is_active);