import { createClient } from '@supabase/supabase-js';

const meta = import.meta as any;
const supabaseUrl = (meta.env && meta.env.VITE_SUPABASE_URL) || 'https://ucihhursqublehkxpqqm.supabase.co';
const supabaseAnonKey = (meta.env && meta.env.VITE_SUPABASE_ANON_KEY) || 'sb_publishable_9pmd4Eqyp0Sxly3bZq_NRA_bwdM3Fwe';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
