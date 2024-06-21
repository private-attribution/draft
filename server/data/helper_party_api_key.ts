"use server";

import bcrypt from "bcrypt";
import { createSupabaseServiceClient } from "@/data/supabase_server_service_client";

export async function validateApiKey(
  helperPartyUUID: string,
  key: string,
): Promise<boolean> {
  const supabase = await createSupabaseServiceClient();
  // toISOString() always and only returns UTC timestamps
  // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/toISOString
  const currentTimestamp = new Date().toISOString();
  const { data, error } = await supabase
    .from("helper_party_api_keys")
    .select("hashed_api_key")
    .eq("helper_party_uuid", helperPartyUUID)
    .gt("expires_at", currentTimestamp)
    .order("created_at", { ascending: false });

  if (error) {
    throw error;
  }
  if (!data.length) {
    return false;
  }

  for (let row of data) {
    // We need to loop through keys, to see if the provided key
    // matches any of the the stored and unexpired hashed_api_key.
    // There should only be at most one valid key at any given time,
    // but we cannot enforce that in the DB.
    // If we find a match, it's valid.
    // If we don't find a match for the whole loop, it's an invalid key.
    let valid = await bcrypt.compare(key, row.hashed_api_key);
    if (valid) {
      return true;
    }
  }
  return false;
}
