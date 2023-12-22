import React from "react";

export default function Example() {
  return (
    <footer className="bg-white dark:bg-slate-950 h-full sticky top-[100vh]">
      <div className="mx-auto max-w-7xl overflow-hidden px-6 py-4">
        <p className="text-center text-xs leading-5 text-gray-500">
          &copy; 2023 Erik Taubeneck. All rights reserved.{" "}
          <a
            href="https://github.com/eriktaubeneck/draft"
            className="text-gray-800 dark:text-gray-200 hover:text-gray-600 hover:dark:text-gray-400"
          >
            draft
          </a>{" "}
          is an open source project issued under the{" "}
          <a
            href="https://github.com/eriktaubeneck/draft/blob/main/LICENSE.md"
            className="text-gray-800 dark:text-gray-200 hover:text-gray-600 hover:dark:text-gray-400"
          >
            MIT License.
          </a>
        </p>
        <p className="text-center text-xs leading-5 text-gray-500">
          <a
            href="https://www.flaticon.com/free-icons/beer-tap"
            title="beer tap icons"
            className="text-gray-800 dark:text-gray-200 hover:text-gray-600 hover:dark:text-gray-400"
          >
            Beer tap icons created by wanicon - Flaticon.
          </a>
        </p>
      </div>
    </footer>
  );
}
