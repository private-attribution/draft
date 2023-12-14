"use client";

import React, { useEffect, useState } from "react";
import {
  HiddenSectionChevron,
  StatusPill,
  RunTimePill,
  LogViewer,
} from "./components";
import {
  ServerLog,
  RemoteServer,
  RemoteServers,
  StatusByRemoteServer,
  StatsByRemoteServer,
  RunTimeByRemoteServer,
  initialStatus,
  initialStats,
  initialRunTime,
} from "../servers";
import { StatsComponent } from "./charts";

export default function Jobs({ params }: { params: { id: string } }) {
  // display controls
  const [logsHidden, setLogsHidden] = useState<boolean>(false);
  const [statsHidden, setStatsHidden] = useState<boolean>(false);

  const [logs, setLogs] = useState<ServerLog[]>([]);
  const [status, setStatus] = useState<StatusByRemoteServer>(initialStatus);
  const [stats, setStats] = useState<StatsByRemoteServer>(initialStats);
  const [runTime, setRunTime] = useState<RunTimeByRemoteServer>(initialRunTime);

  function flipLogsHidden() {
    setLogsHidden(!logsHidden);
  }

  function flipStatsHidden() {
    setStatsHidden(!statsHidden);
  }

  useEffect(() => {
    let webSockets: WebSocket[] = [];
    for (const remoteServer of Object.values(RemoteServers)) {
      const loggingWs = remoteServer.openLogSocket(params.id, setLogs);
      const statusWs = remoteServer.openStatusSocket(params.id, setStatus);
      const statsWs = remoteServer.openStatsSocket(
        params.id,
        setStats,
        setRunTime,
      );
      webSockets = [...webSockets, loggingWs, statusWs, statsWs];
    }

    return () => {
      for (const ws of webSockets) {
        ws.close();
      }
    };
  }, [params]);

  return (
    <>
      <h2 className="text-2xl font-bold leading-7 text-gray-900 dark:text-gray-100 sm:truncate sm:text-3xl sm:tracking-tight">
        Job Details: {params.id}
      </h2>

      <div className="w-full text-left mx-auto max-w-7xl overflow-hidden rounded-lg bg-white dark:bg-slate-950 shadow mt-10">
        <button onClick={flipStatsHidden} className="w-full h-full">
          <div className="flex justify-between px-4 py-5 sm:p-6 font-bold text-slate-900 dark:text-slate-100">
            <div className="flex">
              <HiddenSectionChevron sectionHidden={statsHidden} />
              <div className="pl-2">Stats</div>
            </div>

            {Object.values(RemoteServers).map((remoteServer: RemoteServer) => (
              <RunTimePill
                status={status}
                runTime={runTime}
                remoteServer={remoteServer}
              />
            ))}
          </div>
        </button>
        {!statsHidden &&
          Object.values(RemoteServers).map((remoteServer: RemoteServer) => (
            <StatsComponent stats={stats} remoteServer={remoteServer} />
          ))}

        <button onClick={flipLogsHidden} className="w-full h-full">
          <div className="flex justify-between px-4 py-5 sm:p-6 font-bold text-slate-900 dark:text-slate-100">
            <div className="flex">
              <HiddenSectionChevron sectionHidden={logsHidden} />
              <div className="pl-2">Logs</div>
            </div>
            {Object.values(RemoteServers).map((remoteServer: RemoteServer) => (
              <StatusPill status={status} remoteServer={remoteServer} />
            ))}
          </div>
        </button>
        {!logsHidden && <LogViewer logs={logs} />}
      </div>
    </>
  );
}
