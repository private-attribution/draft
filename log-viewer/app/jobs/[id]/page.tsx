"use client";

import React, { useEffect, useState } from "react";
import {
  Status,
  HiddenSectionChevron,
  StatusPill,
  RunTimePill,
  LogViewer,
} from "./components";
import { StatsComponent, StatsDataPoint } from "./charts";

export default function Jobs({ params }: { params: { id: string } }) {
  const [logs, setLogs] = useState<string[]>([]);
  const [status, setStatus] = useState<Status | null>(null);
  const [logsHidden, setLogsHidden] = useState<boolean>(false);
  const [statsHidden, setStatsHidden] = useState<boolean>(false);
  const [runTime, setRunTime] = useState<number | null>(null);
  const [stats, setStats] = useState<StatsDataPoint[]>([]);

  function flipLogsHidden() {
    setLogsHidden(!logsHidden);
  }

  function flipStatsHidden() {
    setStatsHidden(!statsHidden);
  }

  useEffect(() => {
    const loggingSocket = new WebSocket(
      `ws://localhost:8000/ws/logs/${params.id}`,
    );
    const statusSocket = new WebSocket(
      `ws://localhost:8000/ws/status/${params.id}`,
    );
    const statsSocket = new WebSocket(
      `ws://localhost:8000/ws/stats/${params.id}`,
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

    statsSocket.onmessage = (event) => {
      const eventData = JSON.parse(event.data);
      setRunTime(eventData.run_time);
      // https://psutil.readthedocs.io/en/latest/#psutil.Process.memory_info
      // we grab rss memory aka “Resident Set Size”, this is the non-swapped physical memory a process has used
      const statsDataPoint: StatsDataPoint = {
        timestamp: eventData.timestamp,
        memoryUsage: eventData.memory_info[0],
        cpuUsage: eventData.cpu_percent,
      };

      setStats((prevStats: StatsDataPoint[]) => [...prevStats, statsDataPoint]);
    };

    loggingSocket.onclose = (event) => {
      console.log(`Logging WebSocket closed for process ${params.id}:`, event);
    };
    statusSocket.onclose = (event) => {
      console.log(`Status WebSocket closed for process ${params.id}:`, event);
    };
    statsSocket.onclose = (event) => {
      console.log(`Stats WebSocket closed for process ${params.id}:`, event);
    };

    return () => {
      loggingSocket.close();
      statusSocket.close();
      statsSocket.close();
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
            <RunTimePill status={status} runTime={runTime} />
          </div>
        </button>
        {!statsHidden && <StatsComponent stats={stats} />}

        <button onClick={flipLogsHidden} className="w-full h-full">
          <div className="flex justify-between px-4 py-5 sm:p-6 font-bold text-slate-900 dark:text-slate-100">
            <div className="flex">
              <HiddenSectionChevron sectionHidden={logsHidden} />
              <div className="pl-2">Logs</div>
            </div>
            <StatusPill status={status} />
          </div>
        </button>
        {!logsHidden && <LogViewer logs={logs} />}
      </div>
    </>
  );
}
