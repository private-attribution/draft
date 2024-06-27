import { Source_Code_Pro } from "next/font/google";
import clsx from "clsx";
import { ChevronDownIcon, ChevronRightIcon } from "@heroicons/react/24/solid";
import { Status, ServerLog } from "@/app/query/servers";

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

type StatusClassNameMixinsType = {
  [key in Status]: string;
};

const StatusClassNameMixins: StatusClassNameMixinsType = {
  QUEUED: "bg-slate-300 dark:bg-slate-700",
  STARTING: "bg-emerald-300 dark:bg-emerald-700 animate-pulse",
  COMPILING: "bg-emerald-300 dark:bg-emerald-700 animate-pulse",
  WAITING_TO_START: "bg-emerald-300 dark:bg-emerald-700 animate-pulse",
  IN_PROGRESS: "bg-emerald-300 dark:bg-emerald-700 animate-pulse",
  COMPLETE: "bg-cyan-300 dark:bg-cyan-700",
  KILLED: "bg-rose-200 dark:bg-rose-700 animate-pulse",
  NOT_FOUND: "bg-rose-300 dark:bg-rose-800",
  CRASHED: "bg-rose-300 dark:bg-rose-800 animate-pulse",
  UNKNOWN: "bg-rose-300 dark:bg-rose-800",
};

function StatusToTitleString(status: Status): string {
  return status
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

export function StatusPill({ status }: { status: Status }) {
  return (
    <div className={clsx(`rounded-full px-2`, StatusClassNameMixins[status])}>
      {StatusToTitleString(status)}
    </div>
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
}: {
  status: Status;
  runTime: number | null;
}) {
  const runTimeStr = runTime ? secondsToTime(runTime) : "N/A";
  return (
    <div className={clsx(`rounded-full px-2`, StatusClassNameMixins[status])}>
      {runTimeStr}
    </div>
  );
}

export function LogViewer({
  logs,
  className = "",
}: {
  logs: ServerLog[];
  className?: string;
}) {
  return (
    <div
      className={clsx(
        "w-full bg-white dark:bg-slate-950 overflow-y-scroll max-h-96 text-start text-wrap",
        className,
      )}
    >
      <div className="px-4 py-5 sm:p-6">
        <dl>
          {logs.map((log, index) => {
            const date = new Date(log.timestamp * 1000);
            return (
              <div className="flex" key={index}>
                <dt
                  className={clsx(
                    "flex-none w-80 text-slate-900 dark:text-slate-100 text-xs",
                    sourceCodePro.className,
                  )}
                >
                  {date.toISOString()} | {log.remoteServer.remoteServerNameStr}:
                </dt>
                <dd
                  className={clsx(
                    "text-slate-900 dark:text-slate-100 text-xs",
                    sourceCodePro.className,
                  )}
                >
                  {log.logLine}
                </dd>
              </div>
            );
          })}
          <div
            key="last"
            className={clsx(
              "text-slate-900 dark:text-slate-100 text-xs whitespace-pre-line animate-pulse",
              sourceCodePro.className,
            )}
          >
            {">_"}
          </div>
        </dl>
      </div>
    </div>
  );
}
