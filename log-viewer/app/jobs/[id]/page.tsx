"use client";
import { Source_Code_Pro } from "next/font/google";
import React, { useEffect, useState } from "react";
import clsx from "clsx";
import { ChevronDownIcon, ChevronRightIcon } from "@heroicons/react/24/solid";

const sourceCodePro = Source_Code_Pro({ subsets: ["latin"] });

enum Status {
  Complete,
  InProgress,
  NotFound,
}

function LogViewer({ jobId }: { jobId: string }) {
  const [logs, setLogs] = useState<string[]>([]);
  const [status, setStatus] = useState<Status | null>(null);
  const [hidden, setHidden] = useState<boolean>(true);

  function flipHidden() {
    setHidden(!hidden);
  }

  useEffect(() => {
    const loggingSocket = new WebSocket(`ws://localhost:8000/ws/logs/${jobId}`);
    const statusSocket = new WebSocket(
      `ws://localhost:8000/ws/status/${jobId}`,
    );

    loggingSocket.onmessage = (event) => {
      setLogs((prevLogs) => [...prevLogs, event.data]);
    };

    statusSocket.onmessage = (event) => {
      switch (JSON.parse(event.data).status) {
        case "complete": {
          setStatus(Status.Complete);
          break;
        }
        case "in-progress": {
          setStatus(Status.InProgress);
          break;
        }
        case "not-found": {
          setStatus(Status.NotFound);
          break;
        }
      }
    };

    loggingSocket.onclose = (event) => {
      console.log(`Logging WebSocket closed for process ${jobId}:`, event);
    };
    statusSocket.onclose = (event) => {
      console.log(`Status WebSocket closed for process ${jobId}:`, event);
    };

    return () => {
      loggingSocket.close();
      statusSocket.close();
    };
  }, []);

  return (
    <div className="w-full text-left mx-auto max-w-7xl overflow-hidden rounded-lg bg-white dark:bg-slate-950 shadow mt-10">
      <button onClick={flipHidden} className="w-full h-full">
        <div className="flex justify-between px-4 py-5 sm:p-6 font-bold text-slate-900 dark:text-slate-100">
          <div className="flex">
            {hidden ? (
              <ChevronRightIcon className="h-4 mt-1" />
            ) : (
              <ChevronDownIcon className="h-4 mt-1" />
            )}{" "}
            <div className="pl-2">Logs</div>
          </div>

          {status === Status.Complete && (
            <div className="rounded-full bg-cyan-300 dark:bg-cyan-700 px-2">
              Completed
            </div>
          )}
          {status === Status.InProgress && (
            <div className="rounded-full bg-emerald-300 dark:bg-emerald-700 px-2">
              In Progress
            </div>
          )}
          {status === Status.NotFound && (
            <div className="rounded-full bg-rose-300 dark:bg-rose-800 px-2">
              Not Found
            </div>
          )}
        </div>
      </button>
      {!hidden && (
        <div className="w-full border-t border-gray-300 dark:border-gray-700">
          <div className="px-4 py-5 sm:p-6">
            {logs.map((log, index) => (
              <div
                key={index}
                className={clsx(
                  "text-slate-900 dark:text-slate-100 text-xs whitespace-pre",
                  sourceCodePro.className,
                )}
              >
                {log}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Jobs({ params }: { params: { id: string } }) {
  return (
    <>
      <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
        Job Details: {params.id}
      </h2>
      <LogViewer jobId={params.id} />
    </>
  );
}
