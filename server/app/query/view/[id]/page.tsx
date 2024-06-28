"use client";

import { useEffect, useState } from "react";
import {
  HiddenSectionChevron,
  StatusPill,
  RunTimePill,
  LogViewer,
} from "@/app/query/view/[id]/components";
import {
  Status,
  ServerLog,
  RemoteServer,
  RemoteServerNames,
  RemoteServersType,
  IPARemoteServers, //hack until the queryId is stored in a DB
  StatusByRemoteServer,
  StatsByRemoteServer,
  RunTimeByRemoteServer,
  initialStatusByRemoteServer,
  initialStatsByRemoteServer,
  initialRunTimeByRemoteServer,
} from "@/app/query/servers";
import { StatsComponent } from "@/app/query/view/[id]/charts";
import { JSONSafeParse } from "@/app/utils";
import { getQuery, Query } from "@/data/query";

export default function QueryPage({ params }: { params: { id: string } }) {
  // display controls
  const [logsHidden, setLogsHidden] = useState<boolean>(true);
  const [statsHidden, setStatsHidden] = useState<boolean>(true);
  const [query, setQuery] = useState<Query | null>(null);

  const [logs, setLogs] = useState<ServerLog[]>([]);
  const [selectedRemoteServerLogs, setSelectedRemoteServerLogs] = useState<
    string[]
  >(
    Object.keys(RemoteServerNames).filter((item) => {
      return isNaN(Number(item));
    }),
  );

  const displayedLogs = logs.filter((item) =>
    selectedRemoteServerLogs.includes(item.remoteServer.remoteServerNameStr),
  );

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

  function handleCheckbox(e: React.ChangeEvent<HTMLInputElement>) {
    const remoteServer = e.target.id;

    if (e.target.checked) {
      setSelectedRemoteServerLogs((prevSelectedRemoteServers) => [
        ...prevSelectedRemoteServers,
        remoteServer,
      ]);
    } else {
      setSelectedRemoteServerLogs((prevSelectedRemoteServers) =>
        prevSelectedRemoteServers.filter(
          (prevSelectedRemoteServer) =>
            prevSelectedRemoteServer !== remoteServer,
        ),
      );
    }
  }

  const queryParams = Object.entries(
    JSONSafeParse((query?.params as string) || "{}"),
  );

  const kill = async (remoteServers: RemoteServersType) => {
    const query: Query = await getQuery(params.id);

    const fetchPromises = Object.values(remoteServers).map(
      async (remoteServer) => {
        await fetch(remoteServer.killURL(query.uuid), {
          method: "POST",
        });
      },
    );

    await Promise.all(fetchPromises);
  };

  useEffect(() => {
    (async () => {
      const query: Query = await getQuery(params.id);
      setQuery(query);
      let webSockets: WebSocket[] = [];
      // useEffect() gets called twice locally
      // so this prevents the logs from being shown twice
      setLogs([]);
      for (const remoteServer of Object.values(IPARemoteServers)) {
        const loggingWs = remoteServer.openLogSocket(query.uuid, setLogs);
        const statusWs = remoteServer.openStatusSocket(
          query.uuid,
          setStatusByRemoteServer,
        );
        const statsWs = remoteServer.openStatsSocket(
          query.uuid,
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
    })();
  }, [params]);

  return (
    <>
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold leading-7 text-gray-900 dark:text-gray-100 sm:truncate sm:text-3xl sm:tracking-tight">
            Query Details
          </h2>
        </div>
        <div>
          <button
            onClick={() => kill(IPARemoteServers)}
            type="button"
            className="ml-3 rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600"
          >
            Kill Query
          </button>
        </div>
      </div>

      <div className="mt-6 border-t border-b border-gray-300 dark:border-gray-700">
        <dl className="divide-y divide-gray-200 dark:divide-gray-800">
          {[
            ["Display name", params.id],
            ["UUID", query?.uuid],
            ["Created at", query?.createdAt],
            ["Type", query?.type],
          ].map(([name, value]) => {
            return (
              <div
                className="px-4 py-2 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0"
                key={name?.toLowerCase().replaceAll(" ", "_")}
              >
                <dt className="text-sm font-medium leading-6 text-gray-900 dark:text-gray-100">
                  {name}:
                </dt>
                <dd className="mt-1 text-sm leading-6 text-gray-700 dark:text-gray-300 sm:col-span-2 sm:mt-0">
                  {value}
                </dd>
              </div>
            );
          })}

          <div className="px-4 py-2 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
            <dt className="text-sm font-medium leading-6 text-gray-900 dark:text-gray-100">
              Params:
            </dt>
            <dd className="mt-2 text-sm text-gray-900 sm:col-span-2 sm:mt-0">
              <ul className="divide-y divide-gray-200 rounded-md border border-gray-200">
                {queryParams.map(([key, value]) => {
                  return (
                    <li
                      className="flex items-center justify-between py-1 pl-4 pr-5 text-sm leading-6"
                      key={key}
                    >
                      <div className="flex w-0 flex-1 items-center">
                        <div className="ml-4 flex min-w-0 flex-1 gap-2">
                          <span className="truncate font-medium"> {key}</span>
                        </div>
                      </div>
                      <div className="ml-4 flex-shrink-0 font-medium text-sky-700">
                        {value as string}
                      </div>
                    </li>
                  );
                })}
              </ul>
            </dd>
          </div>
        </dl>
      </div>

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
        {!logsHidden && (
          <>
            <form>
              <div>
                <ul
                  role="list"
                  className="divide-y divide-gray-100 dark:divide-gray-900 border-b border-gray-200 dark:border-gray-800"
                >
                  {Object.values(IPARemoteServers).map(
                    (remoteServer: RemoteServer) => {
                      return (
                        <>
                          <li className="flex items-center justify-between py-2 pl-4 pr-5 text-sm leading-6">
                            <input
                              id={remoteServer.remoteServerNameStr}
                              type="checkbox"
                              defaultChecked={true}
                              onChange={handleCheckbox}
                              className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                            />
                            <div className="flex w-0 flex-1 items-center">
                              <div className="ml-4 flex min-w-0 flex-1 gap-2">
                                <span className="truncate font-medium">
                                  {remoteServer.remoteServerNameStr}-
                                  {query?.uuid}
                                  .log
                                </span>
                              </div>
                            </div>
                            {query && (
                              <div className="ml-4 flex-shrink-0">
                                <a
                                  href={remoteServer
                                    .logURL(query.uuid)
                                    .toString()}
                                  className="font-medium text-indigo-600 hover:text-indigo-500"
                                >
                                  Download
                                </a>
                              </div>
                            )}
                          </li>
                        </>
                      );
                    },
                  )}
                </ul>
              </div>
            </form>
            <LogViewer logs={displayedLogs} />
          </>
        )}
      </div>
    </>
  );
}
