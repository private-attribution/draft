import React from "react";
import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";
import { Inter } from "next/font/google";
import "./globals.css";
import clsx from "clsx";
import Header from "./header";
import Footer from "./footer";

const inter = Inter({ subsets: ["latin"] });

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
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
    <html lang="en" className="h-full">
      <body className={clsx(inter.className, "h-full")}>
        <div className="min-h-full bg-slate-100 dark:bg-slate-900">
          {isLoggedIn && <Header user={session?.user} />}
          <main>{children}</main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
