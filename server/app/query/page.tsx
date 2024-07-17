"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { StatusPill, RunTimePill } from "@/app/query/view/[id]/components";
import {
  Status,
  RemoteServer,
  RemoteServerNames,
  IPARemoteServers, //hack until the queryId is stored in a DB
  StatusByRemoteServer,
  StartTimeByRemoteServer,
  EndTimeByRemoteServer,
  initialStatusByRemoteServer,
  initialStartTimeByRemoteServer,
  initialEndTimeByRemoteServer,
} from "@/app/query/servers";
import { getQueryByUUID, Query } from "@/data/query";

type QueryData = {
  status: StatusByRemoteServer;
  startTime: StartTimeByRemoteServer;
  endTime: EndTimeByRemoteServer;
  query: Query;
};
type DataByQuery = {
  [queryID: string]: QueryData;
};

export default function Page() {
  const [queryIDs, setQueryIDs] = useState<string[]>([]);
  const [dataByQuery, setDataByQuery] = useState<DataByQuery>({});

  const updateData = (
    query: Query,
    remoteServer: RemoteServer,
    key: keyof QueryData,
    value: Status | number,
  ) => {
    setDataByQuery((prev) => {
      let _prev = prev;
      if (!prev.hasOwnProperty(query.uuid)) {
        // if queryID not in dataByQuery yet,
        // add initial status before updating value
        _prev = {
          ..._prev,
          [query.uuid]: {
            status: initialStatusByRemoteServer,
            startTime: initialStartTimeByRemoteServer,
            endTime: initialEndTimeByRemoteServer,
            query: query,
          },
        };
      }

      return {
        ..._prev,
        [query.uuid]: {
          ..._prev[query.uuid],
          [key]: {
            ..._prev[query.uuid][key],
            [remoteServer.remoteServerName]: value,
          },
        },
      };
    });
  };

  useEffect(() => {
    // poll runningQueries every second
    (async () => {
      const interval = setInterval(async () => {
        const _queryIDs: string[] =
          await IPARemoteServers[RemoteServerNames.Helper1].runningQueries();

        setQueryIDs(_queryIDs);
      }, 1000); // 1000 milliseconds = 1 second
      return () => clearInterval(interval);
    })();
  }, []);

  useEffect(() => {
    (async () => {
      let webSockets: WebSocket[] = [];

      // remove queries when no longer running
      const filteredDataByQuery = Object.fromEntries(
        Object.keys(dataByQuery)
          .filter((queryID) => queryIDs.includes(queryID))
          .map((queryID) => [queryID, dataByQuery[queryID]]),
      );
      setDataByQuery(filteredDataByQuery);

      for (const queryID of queryIDs) {
        const query: Query = await getQueryByUUID(queryID);

        for (const remoteServer of Object.values(IPARemoteServers)) {
          const statusWs = remoteServer.openStatusSocket(
            queryID,
            (status) => updateData(query, remoteServer, "status", status),
            (startTime) =>
              updateData(query, remoteServer, "startTime", startTime),
            (endTime) => updateData(query, remoteServer, "endTime", endTime),
          );
          webSockets = [...webSockets, statusWs];
        }
      }
      return () => {
        for (const ws of webSockets) {
          ws.close();
        }
      };
    })();
  }, [queryIDs, dataByQuery]);

  return (
    <>
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Current Queries
          </h2>

          {Object.entries(dataByQuery).map(([queryID, queryData]) => {
            const statusByRemoteServer = queryData.status;
            const startTimeByRemoteServer = queryData.startTime;
            const endTimeByRemoteServer = queryData.endTime;
            const query = queryData.query;

            return (
              <div
                className="mx-auto mt-10 w-full max-w-7xl overflow-hidden rounded-lg bg-slate-50 text-left shadow hover:bg-slate-200 dark:bg-slate-950 dark:hover:bg-slate-800"
                key={queryID}
              >
                <Link href={`/query/view/${query.displayId}`}>
                  <div className="size-full border-b border-gray-300 px-4 py-2 font-bold text-slate-900 sm:p-2 dark:border-gray-700 dark:text-slate-100">
                    <h3 className="py-2 pl-2 text-base font-semibold leading-6 text-gray-900 dark:text-gray-100">
                      Query: {query.displayId}
                    </h3>
                    <div className="my-2 flex justify-end text-center">
                      <dl className="mb-2 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
                        {Object.values(IPARemoteServers).map(
                          (remoteServer: RemoteServer) => {
                            const startTime =
                              startTimeByRemoteServer[
                                remoteServer.remoteServerName
                              ];
                            const endTime =
                              endTimeByRemoteServer[
                                remoteServer.remoteServerName
                              ];

                            const status =
                              statusByRemoteServer[
                                remoteServer.remoteServerName
                              ] ?? Status.UNKNOWN;

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
                    <div className="my-2 flex justify-end text-center">
                      <dl className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
                        {Object.values(IPARemoteServers).map(
                          (remoteServer: RemoteServer) => {
                            const status =
                              statusByRemoteServer[
                                remoteServer.remoteServerName
                              ] ?? Status.UNKNOWN;

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
                  </div>
                </Link>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
