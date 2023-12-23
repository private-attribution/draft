"use server";

import { Octokit } from "octokit";

const octokit = new Octokit({ userAgent: "draft/v0.0.1" });

export interface Branch {
  name: string;
  commitHash: string;
}

export async function Branches(owner: string, repo: string): Promise<Branch[]> {
  const branchesIter = octokit.paginate.iterator(
    octokit.rest.repos.listBranches,
    {
      owner: owner,
      repo: repo,
      per_page: 100,
      auth: process.env.GITHUB_API_KEY,
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

  const mainBranch = branchesArray.find((branch) => branch.name === "main");
  if (mainBranch) {
    branchesArray.unshift(mainBranch);
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
      auth: process.env.GITHUB_API_KEY,
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
