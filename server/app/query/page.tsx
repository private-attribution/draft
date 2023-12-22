"use client";
import React, { useState, FormEvent } from "react";
import clsx from "clsx";
import { useRouter } from "next/navigation";
import QueryStartedAlert from "../alert";
import { RemoteServers, RemoteServerNames } from "./servers";
import NewQueryId from "./haikunator";

export default function Page() {
  const [queryId, setQueryId] = useState<string | null>(null);
  const router = useRouter();

  const handleDemoLogsFormSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    try {
      const newQueryId = NewQueryId();
      setQueryId(newQueryId);
      // Send a POST request to start the process
      console.log("sending post");
      const formData = new FormData(event.currentTarget);
      for (const remoteServer of Object.values(RemoteServers)) {
        const response = await fetch(
          remoteServer.startDemoLoggerPath(newQueryId),
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

      // Redirect to /query/<newQueryId>
      router.push(`/query/${newQueryId}`);
    } catch (error) {
      console.error("Error starting process:", error);
    }
  };

  const handleIPAFormSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const newQueryId = NewQueryId();
      setQueryId(newQueryId);
      // Send a POST request to start the process
      console.log("sending post");
      const formData = new FormData(event.currentTarget);
      for (const remoteServer of Object.values(RemoteServers)) {
        let path: URL;
        if (remoteServer.remoteServerName === RemoteServerNames.Coordinator) {
          path = remoteServer.startIPAQueryPath(newQueryId);
        } else {
          path = remoteServer.startIPAHelperPath(newQueryId);
        }

        const response = await fetch(path, {
          method: "POST",
          body: formData,
        });
        const data = await response.json();
        console.log(remoteServer);
        console.log(data);
      }

      // const data = await response.json();

      await new Promise((f) => setTimeout(f, 1000));

      // Redirect to /query/<newQueryId>
      router.push(`/query/${newQueryId}`);
    } catch (error) {
      console.error("Error starting process:", error);
    }
  };

  return (
    <>
      {queryId && <QueryStartedAlert queryId={queryId} />}
      <div className="md:flex md:items-start md:justify-between">
        <DemoLogsForm handleDemoLogsFormSubmit={handleDemoLogsFormSubmit} />
        <IPAForm handleIPAFormSubmit={handleIPAFormSubmit} />
      </div>
    </>
  );
}

function DemoLogsForm({
  handleDemoLogsFormSubmit,
}: {
  handleDemoLogsFormSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form
      onSubmit={handleDemoLogsFormSubmit}
      className="rounded-md bg-slate-50 px-8 py-6 w-96"
    >
      <h2 className="text-2xl mb-2 font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
        Demo Logger Query
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
        Start Query
      </button>
    </form>
  );
}

function IPAForm({
  handleIPAFormSubmit,
}: {
  handleIPAFormSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form
      onSubmit={handleIPAFormSubmit}
      className="rounded-md bg-slate-50 px-8 py-6 w-96"
    >
      <h2 className="text-2xl mb-2 font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
        IPA Query
      </h2>
      <SelectMenu
        id="size"
        label="Input Size"
        options={["1000", "10000", "100000", "1000000"]}
        defaultValue="1000"
        labelClassName=""
        selectClassName=""
      />
      <SelectMenu
        id="max_breakdown_keys"
        label="Max Breakdown Keys"
        options={["16", "32", "64", "128", "256"]}
        defaultValue="64"
        labelClassName=""
        selectClassName=""
      />
      <SelectMenu
        id="max_trigger_value"
        label="Max Trigger Value"
        options={["1", "3", "7", "15", "31", "63", "127", "255", "511", "1023"]}
        defaultValue="7"
        labelClassName=""
        selectClassName=""
      />
      <SelectMenu
        id="per_user_credit_cap"
        label="Per User Credit Cap"
        options={["16", "32", "64", "128", "256"]}
        defaultValue="64"
        labelClassName=""
        selectClassName=""
      />
      <button
        type="submit"
        className="mt-4 inline-flex items-center rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600"
      >
        Start Query
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
