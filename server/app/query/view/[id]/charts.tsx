"use client";
import clsx from "clsx";
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
import { StatsDataPoint, RemoteServer } from "@/app/query/servers";

ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  Title,
  CategoryScale,
  TimeScale,
);

export function StatsComponent({
  stats,
  remoteServer,
  className = "",
}: {
  stats: StatsDataPoint[];
  remoteServer: RemoteServer;
  className?: string;
}) {
  const memoryTimestamps = stats.map(
    (entry: StatsDataPoint) => entry.timestamp,
  );

  const memoryValues = stats.map(
    (entry: StatsDataPoint) => entry.memoryRSSUsage,
  );
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
          callback: function (value, _index, _values) {
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
    <div className={clsx(`w-full bg-white pt-2 dark:bg-slate-950`, className)}>
      <h2 className="w-full px-2 text-base font-bold leading-7 text-gray-900 sm:truncate sm:text-base sm:tracking-tight dark:text-gray-100">
        {remoteServer.toString()} Server
      </h2>

      <div className="md:flex">
        <div className="mb-4 w-full px-2 md:mb-0 md:w-1/2">
          {memoryChartData && (
            <Line data={memoryChartData} options={memoryChartOptions} />
          )}
        </div>
        <div className="mb-4 w-full px-2 md:mb-0 md:w-1/2">
          {cpuChartData && (
            <Line data={cpuChartData} options={cpuChartOptions} />
          )}
        </div>
      </div>
    </div>
  );
}
