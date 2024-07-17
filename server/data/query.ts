"use server";

import { notFound } from "next/navigation";
import { Database, Json } from "@/data/supabaseTypes";
import { buildSupabaseServerClient } from "@/data/supabase_server_client";
import { Status } from "@/app/query/servers";
import NewQueryId from "@/app/query/haikunator";

type QueryRow = Database["public"]["Tables"]["queries"]["Row"];
type QueryType = Database["public"]["Enums"]["query_type"];

export interface Query {
  uuid: string;
  displayId: string;
  type: QueryType;
  status: Status;
  params: Json;
  createdAt: string;
  startedAt: string | null;
  endedAt: string | null;
}

function processQueryData(data: QueryRow): Query {
  return {
    uuid: data.uuid,
    displayId: data.display_id,
    type: data.type as QueryType,
    status: data.status as Status,
    params: data.params,
    createdAt: data.created_at,
    startedAt: data.started_at,
    endedAt: data.ended_at,
  };
}

export async function getQuery(displayId: string): Promise<Query> {
  const supabase = await buildSupabaseServerClient();

  const { status, data, error } = await supabase
    .from("queries")
    .select("*")
    .eq("display_id", displayId)
    .limit(1)
    .maybeSingle();

  if (error) {
    console.error(error);
  } else if (status === 200) {
    if (data) {
      return processQueryData(data);
    } else {
      notFound();
    }
  }
  throw new Error(`${displayId} not found.`);
}

export async function getQueryByUUID(uuid: string): Promise<Query> {
  const supabase = await buildSupabaseServerClient();

  const { status, data, error } = await supabase
    .from("queries")
    .select("*")
    .eq("uuid", uuid)
    .limit(1)
    .maybeSingle();

  if (error) {
    console.error(error);
  } else if (status === 200) {
    if (data) {
      return processQueryData(data);
    } else {
      notFound();
    }
  }
  throw new Error(`${uuid} not found.`);
}

export async function createNewQuery(
  params: FormData,
  queryType: QueryType,
): Promise<Query> {
  const json = JSON.stringify(Object.fromEntries(params));
  const supabase = await buildSupabaseServerClient();
  const newQueryId = NewQueryId();

  const { data: uniqueDisplayId, error: rpcError } = await supabase.rpc(
    "generate_unique_display_id",
    { p_display_id: newQueryId },
  );

  if (rpcError) {
    throw new Error(`${rpcError}`);
  }

  const { data: queryRow, error: insertError } = await supabase
    .from("queries")
    .insert({
      display_id: uniqueDisplayId,
      status: "QUEUED",
      type: queryType,
      params: json,
    })
    .select()
    .returns<QueryRow>()
    .single();

  if (insertError) {
    throw new Error(`${insertError}`);
  }

  const query: Query = processQueryData(queryRow);
  return query;
}
