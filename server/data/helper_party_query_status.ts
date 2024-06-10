"use server";

import { buildSupabaseServerClient } from "@/data/supabase_server_client";
import { PostgrestError } from "@supabase/supabase-js";

export async function updateStatusFunction(
  helperPartyUUID: string,
  queryUUID: string,
  status: string,
): Promise<PostgrestError | null> {
  const supabase = buildSupabaseServerClient();
  console.log("Status updated to:", status);
  const { error } = await supabase.from("helper_party_query_status").insert({
    helper_party_uuid: helperPartyUUID,
    query_uuid: queryUUID,
    status: status,
  });
  return error;
}
