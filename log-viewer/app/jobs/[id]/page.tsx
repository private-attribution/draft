"use client";
import { Recursive } from "next/font/google";
import React, { useEffect, useState } from "react";
import clsx from "clsx";

interface LogItem {
  log: string;
  color: string;
}

const recursiveMono = Recursive({ subsets: ["latin"], axes: ["MONO"] });

function LogViewer({ jobId, color }: { jobId: string; color: string }) {
  const [logs, setLogs] = useState<LogItem[]>([]);

  useEffect(() => {
    const socket = new WebSocket(`ws://localhost:8000/ws/${jobId}`);

    socket.onmessage = (event) => {
      setLogs((prevLogs) => [...prevLogs, { log: event.data, color }]);
    };

    socket.onclose = (event) => {
      console.error(`WebSocket closed for process ${jobId}:`, event);
    };

    return () => {
      socket.close();
    };
  }, [jobId, color, setLogs]); // Add color to the dependency array

  return (
    <div>
      {logs.map(({ log, color }, index) => (
        <div key={index} className={clsx(color, recursiveMono.className)}>
          {`Job ${jobId}: ${log}`}
        </div>
      ))}
    </div>
  );
}

export default function Jobs({ params }: { params: { id: string } }) {
  return (
    <>
      <LogViewer jobId={params.id} color="sky-900" />
    </>
  );
}
