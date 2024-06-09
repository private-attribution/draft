"use server";

import { NextRequest, NextResponse } from "next/server";
import bcrypt from "bcrypt";
import { createClient, PostgrestError } from "@supabase/supabase-js";
import { Database } from "@/data/supabaseTypes";
import { truncate } from "fs";

const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  },
);

export default async function POST(req: NextRequest) {
  const apiKey = req.headers.get("x-api-key");

  const {
    status,
    helper_party_uuid: helperPartyUUID,
    query_uuid: queryUUID,
  } = (await req.json()) as {
    status: string;
    helper_party_uuid: string;
    query_uuid: string;
  };

  if (!helperPartyUUID || !apiKey || !queryUUID) {
    return NextResponse.json(
      { error: "helper_party_uuid, API key, and query_uuid are required" },
      { status: 400 },
    );
  }

  if (!status) {
    return NextResponse.json({ error: "Status is required" }, { status: 400 });
  }

  const { isValid, error } = await validateApiKey(helperPartyUUID, apiKey);
  if (!isValid) {
    return NextResponse.json({ error: error?.message }, { status: 401 });
  }

  const updateStatusError = await updateStatusFunction(
    helperPartyUUID,
    queryUUID,
    status,
  );
  if (updateStatusError) {
    console.error("Error updating status:", updateStatusError);
    return NextResponse.json(
      { error: "Failed to update status" },
      { status: 500 },
    );
  }
  return NextResponse.json({ message: "Status updated successfully" });
}

async function validateApiKey(
  helperPartyUUID: string,
  key: string,
): Promise<{ isValid: boolean; error: Error | undefined }> {
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

async function updateStatusFunction(
  helperPartyUUID: string,
  queryUUID: string,
  status: string,
): Promise<PostgrestError | null> {
  console.log("Status updated to:", status);
  const { error } = await supabase.from("helper_party_query_status").insert({
    helper_party_uuid: helperPartyUUID,
    query_uuid: queryUUID,
    status: status,
  });
  return error;
}
