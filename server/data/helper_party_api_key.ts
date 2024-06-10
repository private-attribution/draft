"use server";

import bcrypt from "bcrypt";
import { buildSupabaseServerClient } from "@/data/supabase_server_client";

export async function validateApiKey(
  helperPartyUUID: string,
  key: string,
): Promise<{ isValid: boolean; error: Error | undefined }> {
  const supabase = buildSupabaseServerClient();
  const currentTimestamp = new Date().toISOString();
  const { data, error } = await supabase
    .from("helper_party_api_keys")
    .select("hashed_api_key, revoked, expires_at")
    .eq("helper_party_uuid", helperPartyUUID)
    .order("created_at", { ascending: false });

  if (error) {
    console.error("Error fetching API key from database:", error);
    throw error;
  }

  if (!data) {
    console.error(`helperParty<$helperPartyUUID> has no API keys`);
    return { isValid: false, error: Error("No API key found.") };
  }

  for (let row of data) {
    let valid = await bcrypt.compare(key, row.hashed_api_key);
    if (valid) {
      switch (true) {
        case row.revoked: {
          return { isValid: false, error: Error("API key revoked.") };
        }
        case row.expires_at < currentTimestamp: {
          return { isValid: false, error: Error("API key expired.") };
        }
        default: {
          return { isValid: true, error: undefined };
        }
      }
    }
  }
  return { isValid: false, error: Error("API key invalid.") };
}
