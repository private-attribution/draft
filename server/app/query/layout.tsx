import React from "react";
import { Inter } from "next/font/google";
import "@/app/globals.css";
import clsx from "clsx";
import Header from "@/app/header";
import Footer from "@/app/footer";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-full bg-slate-100 dark:bg-slate-900 py-10 mx-auto max-w-7xl sm:px-6 lg:px-8">
      {children}
    </div>
  );
}
