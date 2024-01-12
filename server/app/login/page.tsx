import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import Link from "next/link";
import { createServerClient } from "@supabase/ssr";
import { GlobeAltIcon } from "@heroicons/react/24/outline";
import GitHubOAuthComponent from "@/app/login/GitHubOAuthComponent";

export default async function LoginPage() {
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

  if (session) {
    redirect("/query");
  }

  return (
    <>
      <div className="px-6 py-12 shadow sm:rounded-lg sm:px-12 h-screen">
        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-[480px]">
          <div className="bg-white px-6 py-12 shadow sm:rounded-lg sm:px-12">
            <div className="flex min-h-full flex-1 flex-col justify-center py-6 sm:px-6 lg:px-8">
              <Link href="/" className="-m-1.5 pb-8">
                <GlobeAltIcon className="h-12 w-12 stroke-indigo-500 mx-auto" />
              </Link>
              <h2 className="text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
                Sign in with GitHub
              </h2>
            </div>
            <div className="mx-auto w-5/6">
              <GitHubOAuthComponent />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
