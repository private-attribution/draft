export default function Example() {
  return (
    <footer className="sticky top-[100vh] h-full bg-white dark:bg-slate-950">
      <div className="mx-auto max-w-7xl overflow-hidden px-6 py-4">
        <p className="text-center text-xs leading-5 text-gray-500">
          &copy; 2023. All rights reserved.{" "}
          <a
            href="https://github.com/eriktaubeneck/draft"
            className="text-gray-800 hover:text-gray-600 dark:text-gray-200 hover:dark:text-gray-400"
          >
            draft
          </a>{" "}
          is an open source project issued under the{" "}
          <a
            href="https://github.com/eriktaubeneck/draft/blob/main/LICENSE.md"
            className="text-gray-800 hover:text-gray-600 dark:text-gray-200 hover:dark:text-gray-400"
          >
            MIT License.
          </a>
        </p>
        <p className="text-center text-xs leading-5 text-gray-500">
          <a
            href="https://www.flaticon.com/free-icons/beer-tap"
            title="beer tap icons"
            className="text-gray-800 hover:text-gray-600 dark:text-gray-200 hover:dark:text-gray-400"
          >
            Beer tap icons created by wanicon - Flaticon.
          </a>
        </p>
      </div>
    </footer>
  );
}
