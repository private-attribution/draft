import Link from "next/link";
import { CheckCircleIcon, XMarkIcon } from "@heroicons/react/20/solid";

export default function QueryStartedAlert({ queryId }: { queryId: string }) {
  return (
    <div className="rounded-md bg-green-50 p-4">
      <div className="flex">
        <div className="shrink-0">
          <CheckCircleIcon
            className="size-5 text-green-400"
            aria-hidden="true"
          />
        </div>
        <div className="ml-3">
          <p className="text-sm font-medium text-green-800">
            Successfully started Query: {queryId}. Redirecting to
            <Link href={`/query/view/${queryId}`}>
              /query/view/{queryId}{" "}
            </Link>.{" "}
          </p>
        </div>
        <div className="ml-auto pl-3">
          <div className="-m-1.5">
            <button
              type="button"
              className="inline-flex rounded-md bg-green-50 p-1.5 text-green-500 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-green-600 focus:ring-offset-2 focus:ring-offset-green-50"
            >
              <span className="sr-only">Dismiss</span>
              <XMarkIcon className="size-5" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
