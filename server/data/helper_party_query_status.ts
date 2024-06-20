"use server";

import { createSupabaseServiceClient } from "@/data/supabase_server_service_client";
import { PostgrestError } from "@supabase/supabase-js";
import { Status } from "@/app/query/servers";

export async function updateStatusFunction(
  helperPartyUUID: string,
  queryUUID: string,
  status: Status,
): Promise<PostgrestError | null> {
  const supabase = await createSupabaseServiceClient();
  const { error } = await supabase
    .from("helper_party_query_status_updates")
    .insert({
      helper_party_uuid: helperPartyUUID,
      query_uuid: queryUUID,
      status: status,
    });
  return error;
}
