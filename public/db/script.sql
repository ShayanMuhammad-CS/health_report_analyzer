-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_sessions table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title TEXT,
    report_text TEXT,
    analysis_result TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create chat_messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    content TEXT,
    role TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

-- Add indexes to improve query performance
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);

-- Add unique constraint to prevent duplicate emails
ALTER TABLE users ADD CONSTRAINT unique_email UNIQUE (email);

-- === 🚨 PERMISSIONS & RLS FOR SUPABASE ===
-- Run these to fix the "42501 permission denied" errors during sign-up and usage

-- 1. Grant base Postgres permissions to the API roles
GRANT ALL ON TABLE public.users TO anon, authenticated;
GRANT ALL ON TABLE public.chat_sessions TO anon, authenticated;
GRANT ALL ON TABLE public.chat_messages TO anon, authenticated;

-- 2. Turn on Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- 3. Create base policies (Allows all operations for development)
-- Note: Before launching publicly, restrict these using auth.uid() = id
CREATE POLICY "Allow public access to users" ON public.users FOR ALL USING (true);
CREATE POLICY "Allow public access to chat_sessions" ON public.chat_sessions FOR ALL USING (true);
CREATE POLICY "Allow public access to chat_messages" ON public.chat_messages FOR ALL USING (true);
