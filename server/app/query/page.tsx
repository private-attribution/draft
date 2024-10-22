"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { StatusPill, RunTimePill } from "@/app/query/view/[id]/components";
import {
  StatusEvent,
  RemoteServer,
  RemoteServerNames,
  IPARemoteServers, //hack until the queryId is stored in a DB
  StatusEventByRemoteServer,
  initialStatusEventByRemoteServer,
} from "@/app/query/servers";
import { getQueryByUUID, Query } from "@/data/query";

type QueryData = {
  statusEvent: StatusEventByRemoteServer;
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
    statusEvent: StatusEvent,
  ) => {
    setDataByQuery((prev) => {
      let _prev = prev;
      if (!Object.hasOwn(prev, query.uuid)) {
        // if queryID not in dataByQuery yet,
        // add initial status before updating value.
        // otherwise prev[query.uuid][statusEvent][remteServer.ServerName]
        // doesn't exist, and cannot be updated. we need to fill in the
        // nested structure, which `initialStatusEventByRemoteServer` does.
        _prev = {
          ..._prev,
          [query.uuid]: {
            statusEvent: initialStatusEventByRemoteServer,
            query: query,
          },
        };
      }

      return {
        ..._prev,
        [query.uuid]: {
          ..._prev[query.uuid],
          statusEvent: {
            ..._prev[query.uuid].statusEvent,
            [remoteServer.remoteServerName]: statusEvent,
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
      setDataByQuery((prev) => {
        return Object.fromEntries(
          Object.keys(prev)
            .filter((queryID) => queryIDs.includes(queryID))
            .map((queryID) => [queryID, prev[queryID]]),
        );
      });

      const promises = queryIDs.map(async (queryID) => {
        const query: Query = await getQueryByUUID(queryID);
        const remoteServerPromises = Object.values(IPARemoteServers).map(
          async (remoteServer) => {
            const statusEvent: StatusEvent =
              await remoteServer.queryStatus(queryID);
            updateData(query, remoteServer, statusEvent);
          },
        );
        await Promise.all(remoteServerPromises);
      });
      await Promise.all(promises);
    })();
  }, [queryIDs]);

  return (
    <>
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight dark:text-gray-100">
            Current Queries
          </h2>

          {Object.keys(dataByQuery).length == 0 && (
            <h3 className="text-lg font-bold leading-7 text-gray-900 sm:truncate sm:text-xl sm:tracking-tight dark:text-gray-100">
              None currently running.
            </h3>
          )}

          {Object.entries(dataByQuery).map(([queryID, queryData]) => {
            const statusEventByRemoteServer = queryData.statusEvent;
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
                            const statusEvent: StatusEvent | null =
                              statusEventByRemoteServer[
                                remoteServer.remoteServerName
                              ];
                            if (statusEvent === null) {
                              return (
                                <div key={remoteServer.remoteServerName}></div>
                              );
                            }

                            return (
                              <div
                                key={remoteServer.remoteServerName}
                                className="w-48 overflow-hidden rounded-lg bg-white px-4 py-2 shadow dark:bg-slate-900"
                              >
                                <dt className="truncate text-sm font-medium text-gray-500 dark:text-gray-300">
                                  {remoteServer.toString()} Run Time
                                </dt>
                                <dd>
                                  <RunTimePill statusEvent={statusEvent} />
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
                            const statusEvent: StatusEvent | null =
                              statusEventByRemoteServer[
                                remoteServer.remoteServerName
                              ];
                            if (statusEvent === null) {
                              return (
                                <div key={remoteServer.remoteServerName}></div>
                              );
                            }

                            return (
                              <div
                                key={remoteServer.remoteServerName}
                                className="w-48 overflow-hidden rounded-lg bg-white px-4 py-2 shadow dark:bg-slate-900"
                              >
                                <dt className="truncate text-sm font-medium text-gray-500 dark:text-gray-300">
                                  {remoteServer.remoteServerNameStr} Status
                                </dt>
                                <dd>
                                  <StatusPill status={statusEvent.status} />
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
