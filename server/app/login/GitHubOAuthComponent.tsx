"use client";

import GitHubIcon from "@/app/logos/github";
import { createBrowserClient } from "@supabase/ssr";

export default function GitHubOAuthComponent() {
  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );

  let url = process?.env?.NEXT_PUBLIC_SITE_URL;

  const handleGitHubLogin = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "github",
      options: {
        redirectTo: `${url}/auth/callback`,
      },
    });

    if (error) {
      console.log({ error });
    }
  };

  return (
    <button
      onClick={handleGitHubLogin}
      className="flex w-full items-center justify-center gap-3 rounded-md bg-[#24292F] px-3 py-2 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#24292F]"
    >
      <GitHubIcon className="flex h-6 w-auto fill-white pr-1 align-[-1px]" />
      <span className="text-md font-semibold leading-6">GitHub</span>
    </button>
  );
}
