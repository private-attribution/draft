"use server";

import { NextRequest, NextResponse } from 'next/server';
import bcrypt from "bcrypt";
import { createClient } from '@supabase/supabase-js'


const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
})


export default async function updateStatus(req: NextRequest) {
  if (req.method !== 'POST') {
    return NextResponse.json({ error: 'Method not allowed' }, { status: 405 });
  }

  const apiKey = req.headers.get('x-api-key');

  const { status, helper_party_uuid: helperPartyUUID, query_uuid: queryUUID } = await req.json() as { status: string, helper_party_uuid: string, query_uuid: string };

  if (!helperPartyUUID || !apiKey || !queryUUID) {
    return NextResponse.json({ error: 'helper_party_uuid, API key, and query_uuid are required' }, { status: 400 });
  }

  const isValid = await validateApiKey(helperPartyUUID, apiKey);
  if (!isValid) {
    return NextResponse.json({ error: 'Invalid API key or helper party ID' }, { status: 401 });
  }

  if (!status) {
    return NextResponse.json({ error: 'Status is required' }, { status: 400 });
  }

  try {
    await updateStatusFunction(helperPartyUUID, queryUUID, status);
    return NextResponse.json({ message: 'Status updated successfully' });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to update status' }, { status: 500 });
  }
}

async function validateApiKey(helperPartyUUID: string, key: string): Promise<boolean> {
  const { data, error } = await supabase
    .from('helper_parties')
    .select('hashed_api_key')
    .eq('uuid', helperPartyUUID)
    .single();

  if (error || !data) {
    console.error('Error fetching API key:', error);
    return false;
  }
  
  return bcrypt.compare(key, data.hashed_api_key);
}

async function updateStatusFunction(helperPartyUUID: string, queryUUID: string, status: string): Promise<void> {
  console.log('Status updated to:', status);
  const { error } = await supabase
    .from('helper_party_query_status')
    .insert({helper_party_uuid: helperPartyUUID, query_uuid: queryUUID, status: status})
  if (error) {
    throw error
  }
}
