"use server";

import { Octokit } from "octokit";

const octokit = new Octokit();

export async function Branches(owner: string, repo: string): Promise<string[]> {
  var iter_branches = octokit.paginate.iterator(
    octokit.rest.repos.listBranches,
    {
      owner: owner,
      repo: repo,
      per_page: 100,
      auth: process.env.GITHUB_API_KEY,
    },
  );

  let branches_array: string[] = [];
  for await (const { data: branches } of iter_branches) {
    for (const branch of branches) {
      branches_array.push(branch.name);
    }
  }
  return branches_array;
}
