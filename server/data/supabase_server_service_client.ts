"use server";

import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { Database } from "@/data/supabaseTypes";

export async function createSupabaseServiceClient(): Promise<
  SupabaseClient<Database>
> {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
  );

  return supabase;
}
