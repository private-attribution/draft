"use client";

import React, { useEffect, useState } from "react";
import {
  HiddenSectionChevron,
  StatusPill,
  RunTimePill,
  LogViewer,
} from "./components";
import {
  Status,
  ServerLog,
  RemoteServer,
  IPARemoteServers, //hack until the queryId is stored in a DB
  StatusByRemoteServer,
  StatsByRemoteServer,
  RunTimeByRemoteServer,
  initialStatusByRemoteServer,
  initialStatsByRemoteServer,
  initialRunTimeByRemoteServer,
} from "../servers";
import { StatsComponent } from "./charts";

export default function Query({ params }: { params: { id: string } }) {
  // display controls
  const [logsHidden, setLogsHidden] = useState<boolean>(true);
  const [statsHidden, setStatsHidden] = useState<boolean>(true);

  const [logs, setLogs] = useState<ServerLog[]>([]);
  const [statusByRemoteServer, setStatusByRemoteServer] =
    useState<StatusByRemoteServer>(initialStatusByRemoteServer);
  const [statsByRemoteServer, setStatsByRemoteServer] =
    useState<StatsByRemoteServer>(initialStatsByRemoteServer);
  const [runTimeByRemoteServer, setRunTimeByRemoteServer] =
    useState<RunTimeByRemoteServer>(initialRunTimeByRemoteServer);

  function flipLogsHidden() {
    setLogsHidden(!logsHidden);
  }

  function flipStatsHidden() {
    setStatsHidden(!statsHidden);
  }

  useEffect(() => {
    let webSockets: WebSocket[] = [];
    for (const remoteServer of Object.values(IPARemoteServers)) {
      const loggingWs = remoteServer.openLogSocket(params.id, setLogs);
      const statusWs = remoteServer.openStatusSocket(
        params.id,
        setStatusByRemoteServer,
      );
      const statsWs = remoteServer.openStatsSocket(
        params.id,
        setStatsByRemoteServer,
        setRunTimeByRemoteServer,
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
        Query Details: {params.id}
      </h2>

      <div className="w-full text-left mx-auto max-w-7xl overflow-hidden rounded-lg bg-slate-50 dark:bg-slate-950 shadow mt-10">
        <button
          onClick={flipStatsHidden}
          className="w-full h-full border-b border-gray-300 dark:border-gray-700"
        >
          <div className="flex justify-between px-4 py-5 sm:p-6 font-bold text-slate-900 dark:text-slate-100">
            <div className="flex">
              <HiddenSectionChevron sectionHidden={statsHidden} />
              <h3 className="text-base pl-2 font-semibold leading-6 text-gray-900 dark:text-gray-100">
                Stats
              </h3>
            </div>
            <dl className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {Object.values(IPARemoteServers).map(
                (remoteServer: RemoteServer) => {
                  const runTime =
                    runTimeByRemoteServer[remoteServer.remoteServerName];
                  const status =
                    statusByRemoteServer[remoteServer.remoteServerName] ??
                    Status.UNKNOWN;

                  return (
                    <div
                      key={remoteServer.remoteServerName}
                      className="w-48 overflow-hidden rounded-lg bg-white dark:bg-slate-900 px-4 py-2 shadow"
                    >
                      <dt className="truncate text-sm font-medium text-gray-500 dark:text-gray-300">
                        {remoteServer.toString()} Run Time
                      </dt>
                      <dd>
                        <RunTimePill status={status} runTime={runTime} />
                      </dd>
                    </div>
                  );
                },
              )}
            </dl>
          </div>
        </button>
        {!statsHidden &&
          Object.values(IPARemoteServers).map((remoteServer: RemoteServer) => {
            const stats = statsByRemoteServer[remoteServer.remoteServerName];
            return (
              <div key={remoteServer.remoteServerName}>
                <StatsComponent stats={stats} remoteServer={remoteServer} />
              </div>
            );
          })}

        <button
          onClick={flipLogsHidden}
          className="w-full h-full border-b border-gray-300 dark:border-gray-700"
        >
          <div className="flex justify-between px-4 py-5 sm:p-6 font-bold text-slate-900 dark:text-slate-100">
            <div className="flex">
              <HiddenSectionChevron sectionHidden={logsHidden} />
              <h3 className="text-base pl-2 font-semibold leading-6 text-gray-900 dark:text-gray-100">
                Logs
              </h3>
            </div>
            <dl className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {Object.values(IPARemoteServers).map(
                (remoteServer: RemoteServer) => {
                  const status =
                    statusByRemoteServer[remoteServer.remoteServerName] ??
                    Status.UNKNOWN;

                  return (
                    <div
                      key={remoteServer.remoteServerName}
                      className="w-48 overflow-hidden rounded-lg bg-white dark:bg-slate-900 px-4 py-2 shadow"
                    >
                      <dt className="truncate text-sm font-medium text-gray-500 dark:text-gray-300">
                        {remoteServer.remoteServerNameStr} Status
                      </dt>
                      <dd>
                        <StatusPill status={status} />
                      </dd>
                    </div>
                  );
                },
              )}
            </dl>
          </div>
        </button>
        {!logsHidden && <LogViewer logs={logs} />}
      </div>
    </>
  );
}
