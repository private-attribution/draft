"use server";

import { NextRequest, NextResponse } from "next/server";
import { validateApiKey } from "@/data/helper_party_api_key";
import { updateStatusFunction } from "@/data/helper_party_query_status";

export async function POST(req: NextRequest) {
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
