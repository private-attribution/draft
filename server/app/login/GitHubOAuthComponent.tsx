"use client";

import GitHubIcon from "@/app/logos/github";
import { createBrowserClient } from "@supabase/ssr";

export default function GitHubOAuthComponent() {
  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );

  let url =
    process?.env?.NEXT_PUBLIC_SITE_URL ?? // Set this to your site URL in production env.
    process?.env?.NEXT_PUBLIC_VERCEL_URL ?? // Automatically set by Vercel.
    "https://draft.test/";
  // Make sure to include `https://`
  url = url.includes("https://") ? url : `https://${url}`;
  // Make sure to include a trailing `/`.
  url = url.charAt(url.length - 1) === "/" ? url : `${url}/`;

  const handleGitHubLogin = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "github",
      options: {
        redirectTo: `${url}auth/callback`,
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
      <span className="text-base font-semibold leading-6">GitHub</span>
    </button>
  );
}
