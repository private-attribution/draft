import React, { ReactNode } from "react";

export enum RemoteServerNames {
  Coordinator,
  Helper1,
  Helper2,
  Helper3,
}

export interface ServerLog {
  remoteServer: RemoteServer;
  logLine: string;
}

export enum Status {
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

export interface StatsDataPoint {
  timestamp: string;
  memoryRSSUsage: number;
  cpuUsage: number;
}

export type StatusByRemoteServer = {
  [key in RemoteServerNames]: Status | null;
};

export const initialStatusByRemoteServer: StatusByRemoteServer =
  Object.fromEntries(
    Object.values(RemoteServerNames).map((serverName) => [[serverName], null]),
  );

export type StatsByRemoteServer = {
  [key in RemoteServerNames]: StatsDataPoint[];
};

export const initialStatsByRemoteServer: StatsByRemoteServer =
  Object.fromEntries(
    Object.values(RemoteServerNames).map((serverName) => [[serverName], []]),
  );

export type RunTimeByRemoteServer = {
  [key in RemoteServerNames]: number | null;
};

export const initialRunTimeByRemoteServer: RunTimeByRemoteServer =
  Object.fromEntries(
    Object.values(RemoteServerNames).map((serverName) => [[serverName], null]),
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

  logsWebSocketURL(id: string): URL {
    const webSocketURL = new URL(`/ws/logs/${id}`, this.baseURL);
    webSocketURL.protocol = "ws";
    return webSocketURL;
  }

  statusWebSocketURL(id: string): URL {
    const webSocketURL = new URL(`/ws/status/${id}`, this.baseURL);
    webSocketURL.protocol = "ws";
    return webSocketURL;
  }

  statsWebSocketURL(id: string): URL {
    const webSocketURL = new URL(`/ws/stats/${id}`, this.baseURL);
    webSocketURL.protocol = "ws";
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
      const newLog: ServerLog = {
        remoteServer: this,
        logLine: event.data,
      };

      // only retain last 1000 logs
      setLogs((prevLogs) => [...prevLogs.slice(-1000), newLog]);
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
    setStatus: React.Dispatch<React.SetStateAction<StatusByRemoteServer>>,
  ): WebSocket {
    const ws = this.statusSocket(id);

    const updateStatus = (status: Status) => {
      setStatus((prevStatus) => ({
        ...prevStatus,
        [this.remoteServerName]: status,
      }));
    };

    ws.onmessage = (event) => {
      const statusString: string = JSON.parse(event.data).status;
      const status = getStatusFromString(statusString);
      updateStatus(status);
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
    setRunTime: React.Dispatch<React.SetStateAction<RunTimeByRemoteServer>>,
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

    const updateRunTime = (runTime: number) => {
      setRunTime((prevRunTime) => {
        return {
          ...prevRunTime,
          [this.remoteServerName]: runTime,
        };
      });
    };

    ws.onmessage = (event) => {
      const eventData = JSON.parse(event.data);
      updateRunTime(eventData.run_time);
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
    new URL("http://localhost:17430"),
  ),
  [RemoteServerNames.Helper1]: new DemoLoggerRemoteServer(
    RemoteServerNames.Helper1,
    new URL("http://localhost:17431"),
  ),
  [RemoteServerNames.Helper2]: new DemoLoggerRemoteServer(
    RemoteServerNames.Helper2,
    new URL("http://localhost:17432"),
  ),
  [RemoteServerNames.Helper3]: new DemoLoggerRemoteServer(
    RemoteServerNames.Helper3,
    new URL("http://localhost:17433"),
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
    new URL("http://localhost:17430"),
  ),
  [RemoteServerNames.Helper1]: new IPAHelperRemoteServer(
    RemoteServerNames.Helper1,
    new URL("http://localhost:17431"),
  ),
  [RemoteServerNames.Helper2]: new IPAHelperRemoteServer(
    RemoteServerNames.Helper2,
    new URL("http://localhost:17432"),
  ),
  [RemoteServerNames.Helper3]: new IPAHelperRemoteServer(
    RemoteServerNames.Helper3,
    new URL("http://localhost:17433"),
  ),
};
