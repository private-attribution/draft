# Remote Runner

Remote runner is a project designed to help test [IPA](https://github.com/private-attribution/ipa) at scale. It contains 3 sub-projects:

1. helper-cli: a thin wrapper with handy cli commands for setting up and running the system
2. log-viewer: a web front end that starts queries an displays logs from the MPC helper servers
3. runner: a sidecar back end API that runs next to the IPA binary on helper servers

## Get started

### Local Dev

Requirements:
1. Python 3.11
2. Node 20



Setup:

```
#Clone this repo
git clone https://github.com/eriktaubeneck/remote-runner.git
cd remote-runner

# install helper-cli
virtualenv .venv
source .venv/bin/activate
pip install --editable cli

# start dev environment
helper-cli start-local-dev
```
