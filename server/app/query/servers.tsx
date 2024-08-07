import React from "react";

export enum RemoteServerNames {
  Coordinator,
  Helper1,
  Helper2,
  Helper3,
}

export interface ServerLog {
  remoteServer: RemoteServer;
  logLine: string;
  timestamp: number;
}

export enum Status {
  QUEUED = "QUEUED",
  STARTING = "STARTING",
  COMPILING = "COMPILING",
  WAITING_TO_START = "WAITING_TO_START",
  IN_PROGRESS = "IN_PROGRESS",
  COMPLETE = "COMPLETE",
  KILLED = "KILLED",
  NOT_FOUND = "NOT_FOUND",
  CRASHED = "CRASHED",
  UNKNOWN = "UNKNOWN",
}

function getStatusFromString(statusString: string): Status {
  const status: Status = statusString as Status;
  if (Object.values(Status).includes(status)) {
    return status;
  } else {
    return Status.UNKNOWN;
  }
}

export interface StatusEvent {
  status: Status;
  startTime: number;
  endTime: number | null;
}

function buildStatusEventFromJSON(statusJSON: any): StatusEvent {
  return {
    status: getStatusFromString(statusJSON.status),
    startTime: statusJSON.start_time,
    endTime: statusJSON.end_time ?? null,
  };
}

export type StatusByRemoteServer = {
  [key in RemoteServerNames]: Status | null;
};

export const initialStatusByRemoteServer: StatusByRemoteServer =
  Object.fromEntries(
    Object.values(RemoteServerNames).map((serverName) => [[serverName], null]),
  );

export type StartTimeByRemoteServer = {
  [key in RemoteServerNames]: number | null;
};

export type EndTimeByRemoteServer = {
  [key in RemoteServerNames]: number | null;
};

export type StatusEventByRemoteServer = {
  [key in RemoteServerNames]: StatusEvent | null;
};

export const initialStartTimeByRemoteServer: StartTimeByRemoteServer =
  Object.fromEntries(
    Object.values(RemoteServerNames).map((serverName) => [[serverName], null]),
  );

export const initialEndTimeByRemoteServer: StartTimeByRemoteServer =
  Object.fromEntries(
    Object.values(RemoteServerNames).map((serverName) => [[serverName], null]),
  );

export const initialStatusEventByRemoteServer: StatusEventByRemoteServer =
  Object.fromEntries(
    Object.values(RemoteServerNames).map((serverName) => [[serverName], null]),
  );

export interface StatsDataPoint {
  timestamp: string;
  memoryRSSUsage: number;
  cpuUsage: number;
}

export type StatsByRemoteServer = {
  [key in RemoteServerNames]: StatsDataPoint[];
};

export const initialStatsByRemoteServer: StatsByRemoteServer =
  Object.fromEntries(
    Object.values(RemoteServerNames).map((serverName) => [[serverName], []]),
  );

export class RemoteServer {
  protected baseURL: URL;
  remoteServerName: RemoteServerNames;
  remoteServerNameStr: string;

  constructor(remoteServerName: RemoteServerNames, baseURL: URL) {
    this.baseURL = baseURL;
    this.remoteServerName = remoteServerName;
    this.remoteServerNameStr = RemoteServerNames[this.remoteServerName];
  }

  startURL(id: string): never | URL {
    throw new Error("Not Implemented");
  }

  killURL(id: string): never | URL {
    throw new Error("Not Implemented");
  }

  queryStatusURL(id: string): URL {
    return new URL(`/start/${id}/status`, this.baseURL);
  }

  async queryStatus(id: string): Promise<StatusEvent> {
    const status_response = await fetch(this.queryStatusURL(id));
    const statusJSON = await status_response.json();
    return buildStatusEventFromJSON(statusJSON);
  }

  runningQueriesURL(): URL {
    return new URL(`/start/running-queries`, this.baseURL);
  }

  async runningQueries(): Promise<string[]> {
    const queries_response = await fetch(this.runningQueriesURL());
    const queriesJSON = await queries_response.json();
    return queriesJSON.running_queries;
  }

  logURL(id: string): URL {
    return new URL(`/start/${id}/log-file`, this.baseURL);
  }

  logsWebSocketURL(id: string): URL {
    const webSocketURL = new URL(`/ws/logs/${id}`, this.baseURL);
    webSocketURL.protocol = "wss";
    return webSocketURL;
  }

  statusWebSocketURL(id: string): URL {
    const webSocketURL = new URL(`/ws/status/${id}`, this.baseURL);
    webSocketURL.protocol = "wss";
    return webSocketURL;
  }

  statsWebSocketURL(id: string): URL {
    const webSocketURL = new URL(`/ws/stats/${id}`, this.baseURL);
    webSocketURL.protocol = "wss";
    return webSocketURL;
  }

  protected logsSocket(id: string): WebSocket {
    return new WebSocket(this.logsWebSocketURL(id));
  }

  protected statusSocket(id: string): WebSocket {
    return new WebSocket(this.statusWebSocketURL(id));
  }

  protected statsSocket(id: string): WebSocket {
    return new WebSocket(this.statsWebSocketURL(id));
  }

  openLogSocket(
    id: string,
    setLogs: React.Dispatch<React.SetStateAction<ServerLog[]>>,
  ): WebSocket {
    const ws = this.logsSocket(id);
    ws.onmessage = (event) => {
      let newLog: ServerLog;
      try {
        const logValue = JSON.parse(event.data);
        newLog = {
          remoteServer: this,
          logLine: logValue.record.message,
          timestamp: logValue.record.time.timestamp,
        };
      } catch (e) {
        newLog = {
          remoteServer: this,
          logLine: event.data,
          timestamp: Date.now(),
        };
      }

      // only retain last 10,000 logs
      const maxNumLogs = 10000;
      setLogs((prevLogs) => {
        if (
          prevLogs.length === 0 ||
          newLog.timestamp >= prevLogs[prevLogs.length - 1].timestamp
        ) {
          // most the time, we put the new log at the end of the array
          return [...prevLogs.slice(-maxNumLogs), newLog];
        } else {
          // if the timestamp is out of order, e.g., less than the
          // end of the array, we put it in the right location
          const lastPreviousLogIndex = prevLogs.findLastIndex(
            (log) => log.timestamp < newLog.timestamp,
          );

          return [
            ...prevLogs.slice(-maxNumLogs, lastPreviousLogIndex + 1),
            newLog,
            ...prevLogs.slice(lastPreviousLogIndex - 1),
          ];
        }
      });
    };
    ws.onclose = (event) => {
      console.log(
        `Logging WebSocket closed for process ${id} on server ${this.remoteServerNameStr}:`,
        event,
      );
    };
    return ws;
  }

  openStatusSocket(
    id: string,
    setStatusEvent: (statusEvent: StatusEvent) => void,
  ): WebSocket {
    const ws = this.statusSocket(id);

    ws.onmessage = (event) => {
      const statusEvent = buildStatusEventFromJSON(JSON.parse(event.data));
      setStatusEvent(statusEvent);
    };

    ws.onclose = (event) => {
      console.log(
        `Status WebSocket closed for process ${id} on server ${this.remoteServerNameStr}:`,
        event,
      );
    };
    return ws;
  }

  openStatsSocket(
    id: string,
    setStats: React.Dispatch<React.SetStateAction<StatsByRemoteServer>>,
  ): WebSocket {
    const ws = this.statsSocket(id);

    const updateStats = (statsDataPoint: StatsDataPoint) => {
      setStats((prevStats) => {
        const thisPrevStats = prevStats[this.remoteServerName];
        return {
          ...prevStats,
          [this.remoteServerName]: [...thisPrevStats, statsDataPoint],
        };
      });
    };

    ws.onmessage = (event) => {
      const eventData = JSON.parse(event.data);
      const statsDataPoint: StatsDataPoint = {
        timestamp: eventData.timestamp,
        memoryRSSUsage: eventData.memory_rss_usage,
        cpuUsage: eventData.cpu_percent,
      };

      updateStats(statsDataPoint);
    };

    ws.onclose = (event) => {
      console.log(
        `Stats WebSocket closed for process ${id} on server ${this.remoteServerNameStr}:`,
        event,
      );
    };

    return ws;
  }

  toString(): string {
    return this.remoteServerNameStr;
  }
}

export class DemoLoggerRemoteServer extends RemoteServer {
  startURL(id: string): URL {
    return new URL(`/start/demo-logger/${id}`, this.baseURL);
  }
}

export type RemoteServersType = {
  [key in RemoteServerNames]: RemoteServer;
};
export const DemoLoggerRemoteServers: RemoteServersType = {
  [RemoteServerNames.Coordinator]: new DemoLoggerRemoteServer(
    RemoteServerNames.Coordinator,
    new URL(
      process?.env?.NEXT_PUBLIC_COORDINATOR_URL ?? "http://localhost:17430",
    ),
  ),
  [RemoteServerNames.Helper1]: new DemoLoggerRemoteServer(
    RemoteServerNames.Helper1,
    new URL(process?.env?.NEXT_PUBLIC_HELPER1_URL ?? "http://localhost:17431"),
  ),
  [RemoteServerNames.Helper2]: new DemoLoggerRemoteServer(
    RemoteServerNames.Helper2,
    new URL(process?.env?.NEXT_PUBLIC_HELPER2_URL ?? "http://localhost:17432"),
  ),
  [RemoteServerNames.Helper3]: new DemoLoggerRemoteServer(
    RemoteServerNames.Helper3,
    new URL(process?.env?.NEXT_PUBLIC_HELPER3_URL ?? "http://localhost:17433"),
  ),
};

export class IPAHelperRemoteServer extends RemoteServer {
  startURL(id: string): URL {
    return new URL(`/start/ipa-helper/${id}`, this.baseURL);
  }
  killURL(id: string): URL {
    return new URL(`/stop/kill/${id}`, this.baseURL);
  }
}

export class IPACoordinatorRemoteServer extends RemoteServer {
  startURL(id: string): URL {
    return new URL(`/start/ipa-query/${id}`, this.baseURL);
  }
  killURL(id: string): URL {
    return new URL(`/stop/kill/${id}`, this.baseURL);
  }
}

export const IPARemoteServers: RemoteServersType = {
  [RemoteServerNames.Coordinator]: new IPACoordinatorRemoteServer(
    RemoteServerNames.Coordinator,
    new URL(
      process?.env?.NEXT_PUBLIC_COORDINATOR_URL ??
        "https://sidecar0.draft.test",
    ),
  ),
  [RemoteServerNames.Helper1]: new IPAHelperRemoteServer(
    RemoteServerNames.Helper1,
    new URL(
      process?.env?.NEXT_PUBLIC_HELPER1_URL ?? "https://sidecar1.draft.test",
    ),
  ),
  [RemoteServerNames.Helper2]: new IPAHelperRemoteServer(
    RemoteServerNames.Helper2,
    new URL(
      process?.env?.NEXT_PUBLIC_HELPER2_URL ?? "https://sidecar2.draft.test",
    ),
  ),
  [RemoteServerNames.Helper3]: new IPAHelperRemoteServer(
    RemoteServerNames.Helper3,
    new URL(
      process?.env?.NEXT_PUBLIC_HELPER3_URL ?? "https://sidecar3.draft.test",
    ),
  ),
};
