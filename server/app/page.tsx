import Link from "next/link";
import Image from "next/image";
import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";
import background_img from "@/public/background.jpg";
import GitHubIcon from "@/app/logos/github";

export default async function Example() {
  const cookieStore = cookies();

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value;
        },
      },
    },
  );

  const {
    data: { session },
  } = await supabase.auth.getSession();
  const isLoggedIn = Boolean(session?.user);

  return (
    <div className="h-screen bg-gradient-to-b from-zinc-500 to-zinc-900">
      <main>
        {/* Hero section */}
        <div className="relative isolate h-screen overflow-hidden bg-gray-900 pb-16 pt-14 sm:pb-20">
          <Image
            src={background_img}
            alt=""
            className="absolute inset-0 -z-10 size-full object-cover blur brightness-50"
          />

          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56">
              <div className="hidden sm:mb-8 sm:flex sm:justify-center">
                <a href="https://github.com/private-attribution/draft/">
                  <div className="relative rounded-full px-2 py-1 text-base font-semibold leading-6 text-gray-300 ring-1 ring-white/10 hover:ring-white/20">
                    Check out <span className="font-mono font-thin">draft</span>{" "}
                    on Github
                    <GitHubIcon className="mb-1 inline-flex h-4 w-auto fill-gray-300 pl-1" />
                  </div>
                </a>
              </div>
              <div className="text-center">
                <h1 className="text-4xl font-bold tracking-tight text-white sm:text-6xl">
                  Run MPC across distinct helper parties
                </h1>
                <p className="mt-6 text-lg leading-8 text-gray-300">
                  <span className="font-mono font-thin">draft</span> coordinates
                  deployment of helper parties to perform MPC.
                </p>
                <div className="mt-10 flex items-center justify-center gap-x-6">
                  <div className="rounded-md bg-indigo-500 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-400">
                    {isLoggedIn ? (
                      <Link href="/query">Queries</Link>
                    ) : (
                      <Link href="/login">Log in</Link>
                    )}
                  </div>
                  <a
                    href="#"
                    className="text-sm font-semibold leading-6 text-white"
                  >
                    View docs <span aria-hidden="true">→</span>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
