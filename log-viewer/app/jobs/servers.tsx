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
  Complete,
  InProgress,
  NotFound,
}

export interface StatsDataPoint {
  timestamp: string;
  memoryUsage: number;
  cpuUsage: number;
}

export type StatusByRemoteServer = {
  [key in RemoteServerNames]: Status | null;
};

export const initialStatus: StatusByRemoteServer = Object.fromEntries(
  Object.values(RemoteServerNames).map((serverName) => [[serverName], null]),
);

export type StatsByRemoteServer = {
  [key in RemoteServerNames]: StatsDataPoint[];
};

export const initialStats: StatsByRemoteServer = Object.fromEntries(
  Object.values(RemoteServerNames).map((serverName) => [[serverName], []]),
);

export type RunTimeByRemoteServer = {
  [key in RemoteServerNames]: number | null;
};

export const initialRunTime: RunTimeByRemoteServer = Object.fromEntries(
  Object.values(RemoteServerNames).map((serverName) => [[serverName], null]),
);

export class RemoteServer {
  private baseURL: URL;
  remoteServerName: RemoteServerNames;
  remoteServerNameStr: string;

  constructor(remoteServerName: RemoteServerNames, baseURL: URL) {
    this.baseURL = baseURL;
    this.remoteServerName = remoteServerName;
    this.remoteServerNameStr = RemoteServerNames[this.remoteServerName];
  }

  startDemoLoggerPath(id: string): URL {
    return new URL(`/start/demo-logger/${id}`, this.baseURL);
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

  private logsSocket(id: string): WebSocket {
    return new WebSocket(this.logsWebSocketURL(id));
  }

  private statusSocket(id: string): WebSocket {
    return new WebSocket(this.statusWebSocketURL(id));
  }

  private statsSocket(id: string): WebSocket {
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
      switch (JSON.parse(event.data).status) {
        case "complete": {
          updateStatus(Status.Complete);
          break;
        }
        case "in-progress": {
          updateStatus(Status.InProgress);
          break;
        }
        case "not-found": {
          updateStatus(Status.NotFound);
          break;
        }
      }
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
      // https://psutil.readthedocs.io/en/latest/#psutil.Process.memory_info
      // we grab rss memory aka “Resident Set Size”, this is the non-swapped physical memory a process has used
      const statsDataPoint: StatsDataPoint = {
        timestamp: eventData.timestamp,
        memoryUsage: eventData.memory_info[0],
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

type RemoteServersObject = {
  [key in RemoteServerNames]: RemoteServer;
};
export const RemoteServers: RemoteServersObject = {
  [RemoteServerNames.Coordinator]: new RemoteServer(
    RemoteServerNames.Coordinator,
    new URL("http://localhost:17430"),
  ),
  [RemoteServerNames.Helper1]: new RemoteServer(
    RemoteServerNames.Helper1,
    new URL("http://localhost:17431"),
  ),
  [RemoteServerNames.Helper2]: new RemoteServer(
    RemoteServerNames.Helper2,
    new URL("http://localhost:17432"),
  ),
  [RemoteServerNames.Helper3]: new RemoteServer(
    RemoteServerNames.Helper3,
    new URL("http://localhost:17433"),
  ),
};
