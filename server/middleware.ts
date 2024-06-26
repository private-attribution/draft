import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value;
        },
        set(name: string, value: string, options: CookieOptions) {
          request.cookies.set({
            name,
            value,
            ...options,
          });
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          });
          response.cookies.set({
            name,
            value,
            ...options,
          });
        },
        remove(name: string, options: CookieOptions) {
          request.cookies.set({
            name,
            value: "",
            ...options,
          });
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          });
          response.cookies.set({
            name,
            value: "",
            ...options,
          });
        },
      },
    },
  );

  if (
    process.env.NODE_ENV === "development" &&
    process.env.BYPASS_AUTH === "true"
  ) {
    const dummyEmail: string = process.env.DUMMY_EMAIL!;
    const dummyPassword: string = process.env.DUMMY_PASSWORD!;
    const { data, error: signInError } = await supabase.auth.signInWithPassword(
      {
        email: dummyEmail,
        password: dummyPassword,
      },
    );

    if (signInError) {
      const { error: signUpError } = await supabase.auth.signUp({
        email: dummyEmail,
        password: dummyPassword,
      });
      if (signUpError) {
        console.error("Sign-in error:", signInError);
        console.error("Sign-up error:", signUpError);
        throw new Error("Failed to handle local development auth bypass.");
      }
    }
    return response;
  }
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const allowedPathsRegex = new RegExp(`^(/|/login|/auth/callback|/docs/.+)$`);
  if (!user && !allowedPathsRegex.test(request.nextUrl.pathname)) {
    const url = request.nextUrl.clone();
    url.pathname = `/404`;
    return NextResponse.rewrite(url);
  }

  return response;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * Feel free to modify this pattern to include more paths.
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
