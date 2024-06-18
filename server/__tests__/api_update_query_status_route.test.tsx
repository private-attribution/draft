// tests/postUpdateStatus.integration.test.ts
import { testApiHandler } from "next-test-api-route-handler"; // ◄ Must be first import
import { describe, it, expect, afterAll } from "@jest/globals";
import { createSupabaseServiceClient } from "@/data/supabase_server_service_client";
import * as appHandler from "@/app/api/update_query_status/route";

const testQueryUUID = "0e067bd3-b93a-4a17-ab51-d5d042181c5f";

describe("POST updateStatus API Route Integration Test", () => {
  afterAll(async () => {
    const supabase = await createSupabaseServiceClient();
    const { error } = await supabase
      .from("helper_party_query_status_updates")
      .delete()
      .eq("query_uuid", testQueryUUID);

    if (error) {
      console.error("Cleanup database failed:", error);
    }
  });

  it("should update the status in the database", async () => {
    // Get test helper party
    const supabase = await createSupabaseServiceClient();
    const { data, error } = await supabase
      .from("helper_parties")
      .select("uuid")
      .eq("display_name", "Local test helper 1")
      .single();

    if (error) {
      throw error;
    }

    const helperPartyUUID = data.uuid;
    const helperPartyAPIKey = process.env.HELPER_PARTY_1_API_KEY!;

    await testApiHandler({
      appHandler,
      async test({ fetch }) {
        const res = await fetch({
          method: "POST",
          headers: { "x-api-key": helperPartyAPIKey },
          body: JSON.stringify({
            status: "STARTING",
            helper_party_uuid: helperPartyUUID,
            query_uuid: testQueryUUID,
          }),
        });
        await expect(res.json()).resolves.toStrictEqual({
          message: "Status updated successfully",
        });
        // Fetch the updated status from the database
        const { data: updatedData } = await supabase
          .from("helper_party_query_status_updates")
          .select("status")
          .eq("helper_party_uuid", helperPartyUUID)
          .limit(1)
          .single();

        expect(updatedData!.status).toBe("STARTING");
      },
    });
  });

  // Additional tests as needed
});
