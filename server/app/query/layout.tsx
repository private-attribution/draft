import React from "react";
import "@/app/globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto min-h-full max-w-7xl bg-slate-100 py-10 sm:px-6 lg:px-8 dark:bg-slate-900">
      {children}
    </div>
  );
}
