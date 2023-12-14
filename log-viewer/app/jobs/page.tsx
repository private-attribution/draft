"use client";
import React, { useState, FormEvent } from "react";
import clsx from "clsx";
import { useRouter } from "next/navigation";
import JobStartedAlert from "../alert";
import { RemoteServers } from "./servers";
import NewJobId from "./haikunator";

export default function Page() {
  const [jobId, setJobId] = useState<string | null>(null);
  const router = useRouter();

  const handleFormSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const newJobId = NewJobId();
      setJobId(newJobId);
      // Send a POST request to start the process
      console.log("sending post");
      const formData = new FormData(event.currentTarget);
      for (const remoteServer of Object.values(RemoteServers)) {
        const response = await fetch(
          remoteServer.startDemoLoggerPath(newJobId),
          {
            method: "POST",
            body: formData,
          },
        );
        const data = await response.json();
        console.log(remoteServer);
        console.log(data);
      }

      // const data = await response.json();

      await new Promise((f) => setTimeout(f, 1000));

      // Redirect to /jobs/<job_id>
      router.push(`/jobs/${newJobId}`);
    } catch (error) {
      console.error("Error starting process:", error);
    }
  };

  return (
    <>
      {jobId && <JobStartedAlert jobId={jobId} />}
      <div className="md:flex md:items-center md:justify-between">
        <DemoLogsForm handleFormSubmit={handleFormSubmit} />
      </div>
    </>
  );
}

function DemoLogsForm({
  handleFormSubmit,
}: {
  handleFormSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form
      onSubmit={handleFormSubmit}
      className="rounded-md bg-slate-50 px-8 py-6"
    >
      <h2 className="text-2xl mb-2 font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
        Demo Logger Job
      </h2>
      <SelectMenu
        id="num_lines"
        label="Number of Lines to Log"
        options={["10", "100", "1000"]}
        defaultValue="10"
        labelClassName=""
        selectClassName=""
      />
      <SelectMenu
        id="total_runtime"
        label="Time to Run Logs (Seconds)"
        options={["10", "30", "60", "600"]}
        defaultValue="10"
        labelClassName=""
        selectClassName=""
      />
      <button
        type="submit"
        className="mt-4 inline-flex items-center rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600"
      >
        Start Job
      </button>
    </form>
  );
}

function SelectMenu({
  id,
  label,
  options,
  defaultValue,
  labelClassName = "",
  selectClassName = "",
}: {
  id: string;
  label: string;
  options: string[];
  defaultValue: string;
  labelClassName: string;
  selectClassName: string;
}) {
  return (
    <div>
      <label
        htmlFor={id}
        className={clsx(
          "block text-sm font-medium leading-6 text-gray-900",
          labelClassName,
        )}
      >
        {label}
      </label>
      <select
        id={id}
        name={id}
        className={clsx(
          "mt-2 block w-full rounded-md border-0 py-1.5 pl-3 pr-10 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-indigo-600 sm:text-sm sm:leading-6",
          selectClassName,
        )}
        defaultValue={defaultValue}
      >
        {options.map((item, i) => (
          <option key={i}>{item}</option>
        ))}
      </select>
    </div>
  );
}
