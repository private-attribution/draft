import React from "react";
import { Inter } from "next/font/google";
import "./globals.css";
import clsx from "clsx";
import Header from "./header";
import Footer from "./footer";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className={clsx(inter.className, "h-full")}>
        <div className="min-h-full bg-slate-100 dark:bg-slate-900">
          <Header />
          <div className="py-10">
            <main>
              <div className="mx-auto max-w-7xl sm:px-6 lg:px-8">
                {children}
              </div>
            </main>
          </div>
          <Footer />
        </div>
      </body>
    </html>
  );
}
