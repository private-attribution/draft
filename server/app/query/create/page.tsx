"use client";
import { useState, useRef, FormEvent, useEffect, Fragment } from "react";
import clsx from "clsx";
import { Listbox, Transition, Combobox } from "@headlessui/react";
import {
  CheckIcon,
  ChevronUpDownIcon,
  ArrowPathIcon,
} from "@heroicons/react/20/solid";
import { useRouter } from "next/navigation";
import { ExclamationCircleIcon } from "@heroicons/react/20/solid";
import QueryStartedAlert from "@/app/alert";
import {
  DemoLoggerRemoteServers,
  IPARemoteServers,
  RemoteServersType,
} from "@/app/query/servers";
import NewQueryId from "@/app/query/haikunator";
import { Branch, Branches, Commits } from "@/app/query/github";

export default function Page() {
  const [queryId, setQueryId] = useState<string | null>(null);
  const router = useRouter();

  const handleFormSubmit = async (
    event: FormEvent<HTMLFormElement>,
    remoteServers: RemoteServersType,
  ) => {
    event.preventDefault();
    try {
      const newQueryId = NewQueryId();
      setQueryId(newQueryId);
      // Send a POST request to start the process
      console.log("sending post");
      const formData = new FormData(event.currentTarget);
      for (const remoteServer of Object.values(remoteServers)) {
        const response = await fetch(remoteServer.startURL(newQueryId), {
          method: "POST",
          body: formData,
        });
        const data = await response.json();
        console.log(remoteServer);
        console.log(data);
      }

      // const data = await response.json();
      await new Promise((f) => setTimeout(f, 1000));

      // Redirect to /query/view/<newQueryId>
      router.push(`/query/view/${newQueryId}`);
    } catch (error) {
      console.error("Error starting process:", error);
    }
  };

  const handleDemoLogsFormSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    await handleFormSubmit(event, DemoLoggerRemoteServers);
  };

  const handleIPAFormSubmit = async (event: FormEvent<HTMLFormElement>) => {
    await handleFormSubmit(event, IPARemoteServers);
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
      />
      <SelectMenu
        id="total_runtime"
        label="Time to Run Logs (Seconds)"
        options={["10", "30", "60", "600"]}
        defaultValue="10"
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
  enum CommitSpecifier {
    COMMIT_HASH,
    BRANCH,
  }
  const owner = "private-attribution";
  const repo = "ipa";
  const [branches, setBranches] = useState<Branch[]>([]);
  const [commitHashes, setCommitHashes] = useState<string[]>([]);
  const branchNames = branches.map((branch) => branch.name);
  const [selectedBranchName, setSelectedBranchName] = useState<string>("main");
  const [selectedCommitHash, setSelectedCommitHash] = useState<string>("");
  const [validCommitHash, setValidCommitHash] = useState<boolean>(true);
  const commitHashInputRef = useRef<HTMLInputElement>(null);
  const [commitSpecifier, setCommitSpecifier] = useState<CommitSpecifier>(
    CommitSpecifier.BRANCH,
  );
  const disableBranch = commitSpecifier != CommitSpecifier.BRANCH;
  const disableCommitHash = commitSpecifier != CommitSpecifier.COMMIT_HASH;
  const filteredCommitHashes =
    selectedCommitHash === ""
      ? []
      : commitHashes.filter((commit) => {
          return commit
            .toLowerCase()
            .startsWith(selectedCommitHash.toLowerCase());
        });

  useEffect(() => {
    const branch = branches.find(
      (branch) => branch.name === selectedBranchName,
    );
    if (branch && commitSpecifier != CommitSpecifier.COMMIT_HASH) {
      setSelectedCommitHash(branch.commitHash);
      setValidCommitHash(true);
    }
  }, [
    selectedBranchName,
    branches,
    commitSpecifier,
    CommitSpecifier.COMMIT_HASH,
  ]);

  useEffect(() => {
    const branch = branches.find(
      (branch) => branch.commitHash === selectedCommitHash,
    );

    const fetchCommitIsValid = async () => {
      const _valid = filteredCommitHashes.length > 0;
      setValidCommitHash(_valid);
    };
    if (branch) {
      setSelectedBranchName(branch.name);
      setValidCommitHash(true);
    } else if (commitSpecifier != CommitSpecifier.BRANCH) {
      setSelectedBranchName("[Specific commit]");
      fetchCommitIsValid().catch(console.error);
    }
  }, [
    selectedCommitHash,
    commitSpecifier,
    CommitSpecifier.BRANCH,
    branches,
    commitHashes,
  ]);

  useEffect(() => {
    const fetchBranches = async () => {
      const _branches = await Branches(owner, repo, false);
      setBranches(_branches);
    };
    const fetchCommitHashes = async () => {
      const _commitHashes = await Commits(owner, repo, false);
      setCommitHashes(_commitHashes);
    };
    fetchBranches().catch(console.error);
    fetchCommitHashes().catch(console.error);
  }, []);

  const refreshBranches = async (selectedCommitHash: string) => {
    const _branches = await Branches(owner, repo, true);
    setBranches(_branches);
    const _commitHashes = await Commits(owner, repo, true);
    setCommitHashes(_commitHashes);
  };

  return (
    <form
      onSubmit={handleIPAFormSubmit}
      className="rounded-md bg-slate-50 px-8 py-6 w-96"
    >
      <h2 className="text-2xl mb-2 font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
        IPA Query
      </h2>
      <div className="flex items-end">
        <div
          className="flex-grow"
          onClick={() => {
            setCommitSpecifier(CommitSpecifier.BRANCH);
          }}
        >
          <PassedStateSelectMenu
            id="branch"
            label="Branch"
            options={branchNames}
            selected={selectedBranchName}
            setSelected={setSelectedBranchName}
            disabled={disableBranch}
          />
        </div>
        <button
          className="relative cursor-default rounded-md bg-white py-2.5 px-3 ml-1 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-600 sm:text-sm sm:leading-6"
          onClick={(e) => {
            e.preventDefault();
            refreshBranches(selectedCommitHash);
          }}
        >
          <ArrowPathIcon className="h-4 w-4" />
        </button>
      </div>
      <div
        className="relative mt-2 rounded-md shadow-sm"
        onClick={() => {
          setCommitSpecifier(CommitSpecifier.COMMIT_HASH);
          if (commitHashInputRef.current) {
            commitHashInputRef.current.select();
          }
        }}
      >
        <label
          htmlFor="commit_hash"
          className={clsx(
            "block text-md font-medium leading-6 text-gray-900 pt-4 pl-[-30px]",
            disableCommitHash && "opacity-25",
          )}
        >
          Commit Hash
        </label>
        <Combobox value={selectedCommitHash} onChange={setSelectedCommitHash}>
          <Combobox.Input
            onChange={(event) => setSelectedCommitHash(event.target.value)}
            type="string"
            name="commit_hash"
            id="commit_hash"
            ref={commitHashInputRef}
            className={clsx(
              "block w-full rounded-md border-0 py-1.5 pl-3 text-gray-900 ring-1 ring-inset focus:ring-2 focus:ring-inset sm:text-sm sm:leading-6",
              !validCommitHash &&
                "text-red-900 ring-red-300 placeholder:text-red-300 focus:ring-red-500",
              disableCommitHash && "opacity-25",
            )}
          />
          <Combobox.Options className="absolute z-10 w-full mt-1 overflow-auto max-h-60 text-gray-900 bg-white shadow-lg rounded-md border border-gray-300 divide-y divide-gray-200 ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
            {filteredCommitHashes.map((commit) => (
              <Combobox.Option key={commit} value={commit} as={Fragment}>
                {({ active, selected }) => (
                  <li
                    className={clsx(
                      "py-2 px-2.5",
                      active ? "bg-blue-500 text-white" : "text-black",
                    )}
                  >
                    {commit}
                  </li>
                )}
              </Combobox.Option>
            ))}
          </Combobox.Options>
        </Combobox>

        {!validCommitHash && (
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 pt-10">
            <ExclamationCircleIcon
              className="h-5 w-5 text-red-500"
              aria-hidden="true"
            />
          </div>
        )}
      </div>
      {!validCommitHash && (
        <p className="mt-2 text-sm text-red-600" id="email-error">
          Not a valid commit hash.
        </p>
      )}

      <SelectMenu
        id="size"
        label="Input Size"
        options={["1000", "10000", "100000", "1000000"]}
        defaultValue="1000"
      />
      <SelectMenu
        id="max_breakdown_key"
        label="Maximum Number of Breakdown Keys"
        options={["16", "32", "64", "128", "256"]}
        defaultValue="64"
      />
      <SelectMenu
        id="max_trigger_value"
        label="Maxiumum Trigger Value"
        options={["1", "3", "7", "15", "31", "63", "127", "255", "511", "1023"]}
        defaultValue="7"
      />
      <SelectMenu
        id="per_user_credit_cap"
        label="Per User Credit Cap"
        options={["16", "32", "64", "128", "256"]}
        defaultValue="64"
      />
      <button
        type="submit"
        className={clsx(
          "mt-4 inline-flex items-center rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600",
          !validCommitHash && "opacity-25 hover:bg-emerald-600",
        )}
        disabled={!validCommitHash}
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
  disabled = false,
}: {
  id: string;
  label: string;
  options: string[];
  defaultValue: string;
  labelClassName?: string;
  selectClassName?: string;
  disabled?: boolean;
}) {
  const [selected, setSelected] = useState<string>(defaultValue);
  return PassedStateSelectMenu({
    id,
    label,
    options,
    selected,
    setSelected,
    labelClassName,
    selectClassName,
    disabled,
  });
}

function PassedStateSelectMenu({
  id,
  label,
  options,
  selected,
  setSelected,
  labelClassName = "",
  selectClassName = "",
  disabled = false,
}: {
  id: string;
  label: string;
  options: string[];
  selected: string;
  setSelected: (value: string) => void;
  labelClassName?: string;
  selectClassName?: string;
  disabled?: boolean;
}) {
  return (
    <Listbox
      value={selected}
      name={id}
      onChange={setSelected}
      disabled={disabled}
    >
      {({ open }) => (
        <>
          <Listbox.Label
            className={clsx(
              "block text-sm font-medium leading-6 text-gray-900",
              labelClassName,
              disabled && "opacity-25",
            )}
          >
            {label}
          </Listbox.Label>
          <div
            className={clsx(
              "relative mt-2",
              selectClassName,
              disabled && "opacity-25",
            )}
          >
            {disabled ? (
              // Listbox.Button overrides the onClick, but we only need that to reactivate.
              <div className="relative w-full cursor-default rounded-md bg-white py-1.5 pl-3 pr-10 text-left text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-600 sm:text-sm sm:leading-6">
                <span className="block truncate">{selected}</span>
                <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                  <ChevronUpDownIcon
                    className="h-5 w-5 text-gray-400"
                    aria-hidden="true"
                  />
                </span>
              </div>
            ) : (
              <Listbox.Button className="relative w-full cursor-default rounded-md bg-white py-1.5 pl-3 pr-10 text-left text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-600 sm:text-sm sm:leading-6">
                <span className="block truncate">{selected}</span>
                <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                  <ChevronUpDownIcon
                    className="h-5 w-5 text-gray-400"
                    aria-hidden="true"
                  />
                </span>
              </Listbox.Button>
            )}

            <Transition
              show={open}
              as={Fragment}
              leave="transition ease-in duration-100"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <Listbox.Options
                className={clsx(
                  "absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm",
                )}
              >
                {options.map((value) => (
                  <Listbox.Option
                    key={value}
                    className={({ active }) =>
                      clsx(
                        active ? "bg-indigo-600 text-white" : "text-gray-900",
                        "relative cursor-default select-none py-2 pl-3 pr-9",
                      )
                    }
                    value={value}
                  >
                    {({ selected, active }) => (
                      <>
                        <span
                          className={clsx(
                            selected ? "font-semibold" : "font-normal",
                            "block truncate",
                          )}
                        >
                          {value}
                        </span>

                        {selected ? (
                          <span
                            className={clsx(
                              active ? "text-white" : "text-indigo-600",
                              "absolute inset-y-0 right-0 flex items-center pr-4",
                            )}
                          >
                            <CheckIcon className="h-5 w-5" aria-hidden="true" />
                          </span>
                        ) : null}
                      </>
                    )}
                  </Listbox.Option>
                ))}
              </Listbox.Options>
            </Transition>
          </div>
        </>
      )}
    </Listbox>
  );
}
