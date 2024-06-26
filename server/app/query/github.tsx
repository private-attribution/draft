"use server";

import { Octokit } from "octokit";

export interface Branch {
  name: string;
  commitHash: string;
}

// TODO: raise error if api key is expired
if (process.env.OCTOKIT_GITHUB_API_KEY === undefined) {
  console.warn(
    "WARNING: Octokit requires a personal access token to function properly. Please add OCTOKIT_GITHUB_API_KEY to .env. It does not require any permissions.",
  );
}

const octokit = new Octokit({
  userAgent: "draft/v0.0.1",
  auth: process.env.OCTOKIT_GITHUB_API_KEY,
});

export async function Branches(
  owner: string,
  repo: string,
  bypassCache: boolean,
): Promise<Branch[]> {
  const branchesRequestParams: any = {
    owner: owner,
    repo: repo,
    per_page: 100,
    request: {
      cache: bypassCache ? "reload" : "default",
    },
    timestamp: bypassCache ? new Date().getTime().toString() : "",
  };
  const branchesIter = octokit.paginate.iterator(
    octokit.rest.repos.listBranches,
    branchesRequestParams,
  );

  let branchesArray: Branch[] = [];
  for await (const { data: branches } of branchesIter) {
    for (const branch of branches) {
      branchesArray.push({
        name: branch.name,
        commitHash: branch.commit.sha.substring(0, 7),
      });
    }
  }

  const pullsRequestParams: any = {
    owner: owner,
    repo: repo,
    state: "open",
    per_page: 100,
    request: {
      cache: bypassCache ? "reload" : "default",
    },
    timestamp: bypassCache ? new Date().getTime().toString() : "",
  };

  const pullRequestsIter = octokit.paginate.iterator(
    octokit.rest.pulls.list,
    pullsRequestParams,
  );

  for await (const { data: pullRequests } of pullRequestsIter) {
    for (const pullRequest of pullRequests) {
      branchesArray.push({
        name: `#${pullRequest.number}: ${pullRequest.title}`,
        commitHash: pullRequest.head.sha.substring(0, 7),
      });
    }
  }

  const mainBranchIndex = branchesArray.findIndex(
    (branch) => branch.name === "main",
  );
  if (mainBranchIndex != -1) {
    branchesArray.unshift(branchesArray.splice(mainBranchIndex, 1)[0]);
  }
  return branchesArray;
}

export async function Commits(
  owner: string,
  repo: string,
  bypassCache: boolean,
  maxCommits: number,
): Promise<string[]> {
  const requestParams: any = {
    owner: owner,
    repo: repo,
    per_page: 100,
    request: {
      cache: bypassCache ? "reload" : "default",
    },
    timestamp: bypassCache ? new Date().getTime().toString() : "",
  };
  const commitsIter = octokit.paginate.iterator(
    octokit.rest.repos.listCommits,
    requestParams,
  );

  let commitsArray: string[] = [];
  let pages: number = 0;
  for await (const { data: commits } of commitsIter) {
    for (const commit of commits) {
      commitsArray.push(commit.sha);
    }
    pages++;
    if (pages * 100 > maxCommits) {
      break;
    }
  }
  return commitsArray;
}
