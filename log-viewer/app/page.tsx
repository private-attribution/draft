"use client";

import React, { useState } from "react";
import axios from "axios";
import { useRouter } from "next/navigation";
import JobStartedAlert from "./alert";

export default function Page() {
  const [jobId, setJobId] = useState(null);
  const router = useRouter();

  const handleStartButtonClick = async () => {
    try {
      // Send a POST request to start the process
      console.log("sending post");
      const response = await axios.post("http://localhost:8000/start");
      const { process_id: newJobId } = response.data;

      // Redirect to /jobs/<job_id>
      router.push(`/jobs/${newJobId}`);
    } catch (error) {
      console.error("Error starting process:", error);
    }
  };

  return (
    <>
      <div className="md:flex md:items-center md:justify-between">
        {jobId && <JobStartedAlert jobId={jobId} />}
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Current Jobs
          </h2>
        </div>
        <div className="mt-4 flex md:ml-4 md:mt-0">
          <button
            type="button"
            onClick={handleStartButtonClick}
            className="ml-3 inline-flex items-center rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600"
          >
            Start New Job
          </button>
        </div>
      </div>
    </>
  );
}
