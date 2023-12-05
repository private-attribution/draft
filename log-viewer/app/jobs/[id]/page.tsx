"use client";
import { Source_Code_Pro } from "next/font/google";
import React, { useEffect, useState } from "react";
import clsx from "clsx";
import { ChevronDownIcon, ChevronRightIcon } from "@heroicons/react/24/solid";
import { Line } from "react-chartjs-2";
import "chartjs-adapter-spacetime";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  CategoryScale,
  TimeScale,
  ChartOptions,
} from "chart.js";

ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  Title,
  CategoryScale,
  TimeScale,
);

const sourceCodePro = Source_Code_Pro({ subsets: ["latin"] });

enum Status {
  Complete,
  InProgress,
  NotFound,
}

interface StatsDataPoint {
  timestamp: string;
  memoryUsage: number;
  cpuUsage: number;
}

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
      </div>
    </>
  );
}

function HiddenSectionChevron({ sectionHidden }: { sectionHidden: boolean }) {
  return sectionHidden ? (
    <ChevronRightIcon className="h-4 mt-1" />
  ) : (
    <ChevronDownIcon className="h-4 mt-1" />
  );
}

function StatusPill({ status }: { status: Status | null }) {
  return (
    <>
      {status === Status.Complete && (
        <div className="rounded-full bg-cyan-300 dark:bg-cyan-700 px-2">
          Completed
        </div>
      )}
      {status === Status.InProgress && (
        <div className="animate-pulse rounded-full bg-emerald-300 dark:bg-emerald-700 px-2">
          In Progress
        </div>
      )}
      {status === Status.NotFound && (
        <div className="rounded-full bg-rose-300 dark:bg-rose-800 px-2">
          Not Found
        </div>
      )}
    </>
  );
}

function secondsToTime(e: number) {
  const h = Math.floor(e / 3600)
      .toString()
      .padStart(2, "0"),
    m = Math.floor((e % 3600) / 60)
      .toString()
      .padStart(2, "0"),
    s = Math.floor(e % 60)
      .toString()
      .padStart(2, "0");

  return h + ":" + m + ":" + s;
}

function RunTimePill({
  status,
  runTime,
}: {
  status: Status | null;
  runTime: number | null;
}) {
  const runTimeStr = runTime ? secondsToTime(runTime) : "";
  return (
    <>
      {runTime && status === Status.Complete && (
        <div className="rounded-full bg-cyan-300 dark:bg-cyan-700 px-2">
          {runTimeStr}
        </div>
      )}
      {runTime && status === Status.InProgress && (
        <div className="animate-pulse rounded-full bg-emerald-300 dark:bg-emerald-700 px-2">
          {runTimeStr}
        </div>
      )}
      {runTime && status === Status.NotFound && (
        <div className="rounded-full bg-rose-300 dark:bg-rose-800 px-2">
          {runTimeStr}
        </div>
      )}
    </>
  );
}

function LogViewer({ logs }: { logs: string[] }) {
  return (
    <div className="w-full border-t border-gray-300 dark:border-gray-700">
      <div className="px-4 py-5 sm:p-6">
        {logs.map((log, index) => (
          <div
            key={index}
            className={clsx(
              "text-slate-900 dark:text-slate-100 text-xs whitespace-pre",
              sourceCodePro.className,
            )}
          >
            {log}
          </div>
        ))}
      </div>
    </div>
  );
}

function StatsComponent({ stats }: { stats: StatsDataPoint[] }) {
  const memoryTimestamps = stats.map(
    (entry: StatsDataPoint) => entry.timestamp,
  );

  const memoryValues = stats.map((entry: StatsDataPoint) => entry.memoryUsage);
  const cpuValues = stats.map((entry: StatsDataPoint) => entry.cpuUsage);

  const memoryChartData = {
    labels: memoryTimestamps,
    datasets: [
      {
        label: "RSS Memory Usage",
        data: memoryValues,
        fill: false,
        borderColor: "rgba(75,192,192,1)",
      },
    ],
  };

  const cpuChartData = {
    labels: memoryTimestamps,
    datasets: [
      {
        label: "CPU Usage (%)",
        data: cpuValues,
        fill: false,
        borderColor: "rgba(75,192,192,1)",
      },
    ],
  };

  const memoryChartOptions: ChartOptions<"line"> = {
    scales: {
      x: {
        type: "time",
      },

      y: {
        title: {
          display: true,
          text: "RSS Memory Usage",
        },
        ticks: {
          // Use the callback function to format labels
          callback: function (value, index, values) {
            const valueNum = parseInt(`${value}`);
            if (value === 0) return "0 B"; // Special case for zero

            const k = 1024;
            const sizes = ["B", "KB", "MB", "GB"];

            const i = Math.floor(Math.log(valueNum) / Math.log(k));

            // Format the label with appropriate unit (MB or GB)
            return (
              parseFloat((valueNum / Math.pow(k, i)).toFixed(2)) +
              " " +
              sizes[i]
            );
          },
        },
      },
    },
  };

  const cpuChartOptions: ChartOptions<"line"> = {
    scales: {
      x: {
        type: "time",
      },

      y: {
        title: {
          display: true,
          text: "CPU Usage (%)",
        },
        min: 0,
        max: 100,
      },
    },
  };

  return (
    <div className="md:flex">
      <div className="w-full md:w-1/2 mb-4 md:mb-0 px-2">
        {memoryChartData && (
          <Line data={memoryChartData} options={memoryChartOptions} />
        )}
      </div>
      <div className="w-full md:w-1/2 mb-4 md:mb-0 px-2">
        {cpuChartData && <Line data={cpuChartData} options={cpuChartOptions} />}
      </div>
    </div>
  );
}
