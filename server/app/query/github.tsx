"use server";

import { Octokit } from "octokit";

const octokit = new Octokit({ userAgent: "draft/v0.0.1" });

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

export async function Branches(owner: string, repo: string): Promise<Branch[]> {
  const branchesIter = octokit.paginate.iterator(
    octokit.rest.repos.listBranches,
    {
      owner: owner,
      repo: repo,
      per_page: 100,
      auth: process.env.OCTOKIT_GITHUB_API_KEY,
    },
  );

  let branchesArray: Branch[] = [];
  for await (const { data: branches } of branchesIter) {
    for (const branch of branches) {
      branchesArray.push({
        name: branch.name,
        commitHash: branch.commit.sha,
      });
    }
  }

  const mainBranchIndex = branchesArray.findIndex(
    (branch) => branch.name === "main",
  );
  if (mainBranchIndex != -1) {
    branchesArray.unshift(branchesArray.splice(mainBranchIndex, 1)[0]);
  }
  branchesArray.unshift({ name: "N/A", commitHash: "" });
  return branchesArray;
}

export async function Commits(owner: string, repo: string): Promise<string[]> {
  const commitsIter = octokit.paginate.iterator(
    octokit.rest.repos.listCommits,
    {
      owner: owner,
      repo: repo,
      per_page: 100,
      auth: process.env.OCTOKIT_GITHUB_API_KEY,
    },
  );

  let commitsArray: string[] = [];
  for await (const { data: commits } of commitsIter) {
    for (const commit of commits) {
      commitsArray.push(commit.sha);
    }
  }
  return commitsArray;
}

export async function isValidCommitHash(
  owner: string,
  repo: string,
  commitHash: string,
): Promise<boolean> {
  const commits = await Commits(owner, repo);
  return commits.includes(commitHash);
}
