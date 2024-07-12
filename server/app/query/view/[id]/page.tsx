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
  StartTimeByRemoteServer,
  EndTimeByRemoteServer,
  initialStatusByRemoteServer,
  initialStatsByRemoteServer,
  initialStartTimeByRemoteServer,
  initialEndTimeByRemoteServer,
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
  const [startTimeByRemoteServer, setStartTimeByRemoteServer] =
    useState<StartTimeByRemoteServer>(initialStartTimeByRemoteServer);
  const [endTimeByRemoteServer, setEndTimeByRemoteServer] =
    useState<EndTimeByRemoteServer>(initialEndTimeByRemoteServer);

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
          setStartTimeByRemoteServer,
          setEndTimeByRemoteServer,
        );
        const statsWs = remoteServer.openStatsSocket(
          query.uuid,
          setStatsByRemoteServer,
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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight dark:text-gray-100">
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

      <div className="mt-6 border-y border-gray-300 dark:border-gray-700">
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
                <dd className="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0 dark:text-gray-300">
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
                      <div className="ml-4 shrink-0 font-medium text-sky-700">
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

      <div className="mx-auto mt-10 w-full max-w-7xl overflow-hidden rounded-lg bg-slate-50 text-left shadow dark:bg-slate-950">
        <button
          type="button"
          onClick={flipStatsHidden}
          className="size-full border-b border-gray-300 dark:border-gray-700"
        >
          <div className="flex justify-between px-4 py-5 font-bold text-slate-900 sm:p-6 dark:text-slate-100">
            <div className="flex">
              <HiddenSectionChevron sectionHidden={statsHidden} />
              <h3 className="pl-2 text-base font-semibold leading-6 text-gray-900 dark:text-gray-100">
                Stats
              </h3>
            </div>
            <dl className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {Object.values(IPARemoteServers).map(
                (remoteServer: RemoteServer) => {
                  const startTime =
                    startTimeByRemoteServer[remoteServer.remoteServerName];
                  const endTime =
                    endTimeByRemoteServer[remoteServer.remoteServerName];

                  const status =
                    statusByRemoteServer[remoteServer.remoteServerName] ??
                    Status.UNKNOWN;

                  return (
                    <div
                      key={remoteServer.remoteServerName}
                      className="w-48 overflow-hidden rounded-lg bg-white px-4 py-2 shadow dark:bg-slate-900"
                    >
                      <dt className="truncate text-sm font-medium text-gray-500 dark:text-gray-300">
                        {remoteServer.toString()} Run Time
                      </dt>
                      <dd>
                        <RunTimePill
                          status={status}
                          startTime={startTime}
                          endTime={endTime}
                        />
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
          type="button"
          onClick={flipLogsHidden}
          className="size-full border-b border-gray-300 dark:border-gray-700"
        >
          <div className="flex justify-between px-4 py-5 font-bold text-slate-900 sm:p-6 dark:text-slate-100">
            <div className="flex">
              <HiddenSectionChevron sectionHidden={logsHidden} />
              <h3 className="pl-2 text-base font-semibold leading-6 text-gray-900 dark:text-gray-100">
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
                      className="w-48 overflow-hidden rounded-lg bg-white px-4 py-2 shadow dark:bg-slate-900"
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
                  className="divide-y divide-gray-100 border-b border-gray-200 dark:divide-gray-900 dark:border-gray-800"
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
                              className="size-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
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
                              <div className="ml-4 shrink-0">
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
