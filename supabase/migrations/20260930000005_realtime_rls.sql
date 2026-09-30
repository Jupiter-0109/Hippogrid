-- HippoGrid Migration: Phase 12 Realtime & Row Level Security
-- Enables Realtime on System-of-Record operational tables
-- Enforces read-only access for anon role; writes restricted to backend service_role / protected procedures

-- 1. Enable Row Level Security (RLS)
ALTER TABLE service_continuity ENABLE ROW LEVEL SECURITY;
ALTER TABLE resource_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE plan_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- 2. RLS Policies: Allow read-only access for anon / authenticated clients
DROP POLICY IF EXISTS "Allow anon read service_continuity" ON service_continuity;
CREATE POLICY "Allow anon read service_continuity" ON service_continuity
    FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "Allow anon read resource_plans" ON resource_plans;
CREATE POLICY "Allow anon read resource_plans" ON resource_plans
    FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "Allow anon read plan_feedback" ON plan_feedback;
CREATE POLICY "Allow anon read plan_feedback" ON plan_feedback
    FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "Allow anon read audit_logs" ON audit_logs;
CREATE POLICY "Allow anon read audit_logs" ON audit_logs
    FOR SELECT TO anon, authenticated USING (true);

-- Writes are disallowed for anon role (enforced by absence of INSERT/UPDATE/DELETE policies for anon)
-- Protected business operations must execute through backend FastAPI with service_role / DB pooler credentials

-- 3. Add Tables to Supabase Realtime Publication
-- Enables live websocket broadcast when records are inserted or updated
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime') THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE service_continuity;
        ALTER PUBLICATION supabase_realtime ADD TABLE resource_plans;
        ALTER PUBLICATION supabase_realtime ADD TABLE plan_feedback;
        ALTER PUBLICATION supabase_realtime ADD TABLE audit_logs;
    END IF;
EXCEPTION WHEN OTHERS THEN
    -- If already added or publication is managed differently
    RAISE NOTICE 'Realtime publication setup note: %', SQLERRM;
END $$;
