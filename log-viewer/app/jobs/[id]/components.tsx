import React from "react";
import { Source_Code_Pro } from "next/font/google";
import clsx from "clsx";
import { ChevronDownIcon, ChevronRightIcon } from "@heroicons/react/24/solid";
import {
  Status,
  StatusByRemoteServer,
  RunTimeByRemoteServer,
  RemoteServer,
  ServerLog,
} from "../servers";

const sourceCodePro = Source_Code_Pro({ subsets: ["latin"] });

export function HiddenSectionChevron({
  sectionHidden,
}: {
  sectionHidden: boolean;
}) {
  return sectionHidden ? (
    <ChevronRightIcon className="h-4 mt-1" />
  ) : (
    <ChevronDownIcon className="h-4 mt-1" />
  );
}

export function StatusPill({
  status,
  remoteServer,
}: {
  status: StatusByRemoteServer;
  remoteServer: RemoteServer;
}) {
  const _status = status[remoteServer.remoteServerName];
  return (
    <>
      {_status === Status.Complete && (
        <div className="rounded-full bg-cyan-300 dark:bg-cyan-700 px-2">
          Completed
        </div>
      )}
      {_status === Status.InProgress && (
        <div className="animate-pulse rounded-full bg-emerald-300 dark:bg-emerald-700 px-2">
          In Progress
        </div>
      )}
      {_status === Status.NotFound && (
        <div className="rounded-full bg-rose-300 dark:bg-rose-800 px-2">
          Not Found
        </div>
      )}
    </>
  );
}

function secondsToTime(e: number) {
  const h = Math.floor(e / 3600)
      .toString()
      .padStart(2, "0"),
    m = Math.floor((e % 3600) / 60)
      .toString()
      .padStart(2, "0"),
    s = Math.floor(e % 60)
      .toString()
      .padStart(2, "0");

  return h + ":" + m + ":" + s;
}

export function RunTimePill({
  status,
  runTime,
  remoteServer,
}: {
  status: StatusByRemoteServer;
  runTime: RunTimeByRemoteServer;
  remoteServer: RemoteServer;
}) {
  const _runTime = runTime[remoteServer.remoteServerName];
  const _status = status[remoteServer.remoteServerName];
  const runTimeStr = _runTime ? secondsToTime(_runTime) : "";
  return (
    <>
      {_runTime && _status === Status.Complete && (
        <div className="rounded-full bg-cyan-300 dark:bg-cyan-700 px-2">
          {runTimeStr}
        </div>
      )}
      {_runTime && _status === Status.InProgress && (
        <div className="animate-pulse rounded-full bg-emerald-300 dark:bg-emerald-700 px-2">
          {runTimeStr}
        </div>
      )}
      {_runTime && _status === Status.NotFound && (
        <div className="rounded-full bg-rose-300 dark:bg-rose-800 px-2">
          {runTimeStr}
        </div>
      )}
    </>
  );
}

export function LogViewer({ logs }: { logs: ServerLog[] }) {
  return (
    <div className="w-full border-t border-gray-300 dark:border-gray-700 overflow-x-auto">
      <div className="px-4 py-5 sm:p-6">
        {logs.map((log, index) => (
          <div
            key={index}
            className={clsx(
              "text-slate-900 dark:text-slate-100 text-xs whitespace-pre",
              sourceCodePro.className,
            )}
          >
            {log.remoteServer.toString().slice(0, 11).padEnd(11, " ")}:{" "}
            {log.logLine}
          </div>
        ))}
      </div>
    </div>
  );
}
