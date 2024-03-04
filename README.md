# DRAFT - Distributed Relay and Automation Facilitation Tool
![image of a draft beer tap](server/public/beer-tap.png)

draft is a project designed to help test [IPA](https://github.com/private-attribution/ipa) at scale. It contains 2 components:

1. draft-server: a web front end and service that starts queries an displays logs from the MPC helper servers
2. draft-sidecar: a sidecar back end API that runs next to the IPA binary on helper servers. this include a CLI for setup and running.

# Get started

## Local Dev


### Running Locally

Make sure the repo is cloned and you're working in the root directory of the repo:

```
git clone https://github.com/eriktaubeneck/draft.git
cd draft
```


Assuming all requirements are installed, start prerequisites:

```
colima start
supabase start --workdir server
```

Start `draft` for local dev:
```
draft start-local-dev
```

### Requirements

Requirements:
1. Python 3.11
2. Node 20
3. [Supabase CLI](https://supabase.com/docs/guides/cli/getting-started)
4. Docker

#### macOS install


**Docker**

There are multiple options to run Docker locally. One such option is [colima](https://github.com/abiosoft/colima).

```
brew install docker
brew install colima
colima start
ln -sf ~/.colima/docker.sock /var/run/docker.sock
```

The `ln` at the end is because Supabase requires interacting with the local Docker API. See [this Supabase issue](https://github.com/supabase/cli/issues/153) and [this colima issue.](https://github.com/abiosoft/colima/issues/144) This likely requires `sudo`.


**Github App**

The `draft` web front end uses Github for authentication. In order to login locally, you'll need to create a new application for development. Visit [https://github.com/settings/apps/new](https://github.com/settings/apps/new) to create a new Github app using the following parameters:
1. *name*: draft-local-dev (recommended, but not required)
2. *Homepage URL:* http://localhost:54321
3. *Callback URL:* http://localhost:54321/auth/v1/callback
4. *Request user authorization (OAuth) during installation:* yes
5. *Webhook active:* false
6. *Permissions:* Read-only access to email address
7. *Where can this GitHub App be installed?:* Only on this account

Once you have created the app, you'll need to create a file `server/.env` and add both the `CLIENT_ID` and a generated `CLIENT_SECRET`.

```
SUPABASE_AUTH_GITHUB_CLIENT_ID="<CLIENT_ID>"
SUPABASE_AUTH_GITHUB_SECRET="<CLIENT_SECRET>"
```


**Supabase CLI**

```
brew install supabase/tap/supabase
```

After installing, run

```
supabase start --workdir server
```

In the output, you'll find an `ANON_KEY`. Update the `server/.env` file one more time to include two new variables:

```
NEXT_PUBLIC_SUPABASE_URL="http://localhost:54321"
NEXT_PUBLIC_SUPABASE_ANON_KEY="<ANON_KEY>"
NEXT_PUBLIC_SITE_URL=http://localhost:3000
SUPABASE_AUTH_GITHUB_CLIENT_ID="<CLIENT_ID>"
SUPABASE_AUTH_GITHUB_SECRET="<CLIENT_SECRET>"
```

**Traefik**

install traefik

```
brew install traefik
```

update /etc/hosts with (requires sudo)

```
127.0.0.1 draft.test
127.0.0.1 helper0.draft.test
127.0.0.1 helper1.draft.test
127.0.0.1 helper2.draft.test
127.0.0.1 helper3.draft.test
127.0.0.1 sidecar0.draft.test
127.0.0.1 sidecar1.draft.test
127.0.0.1 sidecar2.draft.test
127.0.0.1 sidecar3.draft.test
```

make local certs

install mkcert with

```
brew install mkcert
```

make the cert with

```
mkcert -cert-file "local_dev/config/cert.pem" -key-file "local_dev/config/key.pem" "draft.test" "*.draft.test"
```

**Run local dev**

You're now ready to install, run, and develop on `draft`!

To start the local development environment:

```
draft start-local-dev
```

(Make sure `draft` is installed, see next section.)

### Install draft

If needed, clone this repo:
```
git clone https://github.com/eriktaubeneck/draft.git
cd draft
```

**Install `draft`**
```
python -m virtualenv .venv
source .venv/bin/activate
pip install --editable .
```


## Credit
[Beer tap icons created by wanicon - Flaticon]("https://www.flaticon.com/free-icons/beer-tap")
