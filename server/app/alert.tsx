import Link from "next/link";
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/20/solid";

export function QueryStartedAlert({ queryId }: { queryId: string }) {
  return (
    <div className="-mt-16 mb-4 rounded-md bg-green-50 p-4">
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
      </div>
    </div>
  );
}

export function QueryFailedToStartAlert({ queryId }: { queryId: string }) {
  return (
    <div className="-mt-16 mb-4 rounded-md bg-red-50 p-4">
      <div className="flex">
        <div className="shrink-0">
          <ExclamationTriangleIcon
            className="size-5 text-red-400"
            aria-hidden="true"
          />
        </div>
        <div className="ml-3">
          <p className="text-sm font-medium text-red-800">
            Failed to start a query: {queryId}.
          </p>
        </div>
      </div>
    </div>
  );
}
