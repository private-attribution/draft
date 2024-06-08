# DRAFT - Distributed Relay and Automation Facilitation Tool
![image of a draft beer tap](server/public/beer-tap.png)

draft is a project designed to help test [IPA](https://github.com/private-attribution/ipa) at scale. It contains two components:

1. draft-server: a web front end and service that starts queries and displays logs from the MPC helper servers.
2. draft-sidecar: a sidecar backend API that runs next to the IPA binary on helper servers. This includes a CLI for setup and running.


# Get started

## Deploying a Helper Party

### Requirements

*Instructions for AWS Linux 2023*

1. Provision an EC2 instance. Download the provided `ssh_connect.pem` key and add it to `~/.ssh`.
2. Point a subdomain of a domain you control to the public IP address.
3. Add the host to your `~/.ssh/config` file:
```
Host ipa
    Hostname <subdomain-name-for-helper>
    User ec2-user
    IdentityFile ~/.ssh/ssh_connect.pem
```
4. Update the `draft/ansible/inventory.ini` file to only include a single host. (Unless you are running all 4 servers.)
5. Provision your machine: `ansible-playbook -i ansible/inventory.ini ansible/provision.yaml`

To deploy new changes in draft, run: `ansible-playbook -i ansible/inventory.ini ansible/deploy.yaml`

### Generating TLS certs with Let's Encrypt

You will need a domain name and TLS certificates for the sidecar to properly run over HTTPS. The following instructions assume your domain is `example.com`, please replace with the domain you'd like to use. You will need to create two subdomains, `sidecar.example.com` and `helper.example.com`. (Note, you could also use a subdomain as your base domain, e.g., `test.example.com` with two subdomains of that: `sidecar.test.example.com` and `helper.test.example.com`.)

1. Set up DNS records for `sidecar.example.com` and `helper.example.com` pointing to a server you control.
2. Make sure you've installed the requirements above, and are using the virtual environment.
3. Install `certbot`: `pip install certbot`
4. `sudo .venv/bin/certbot certonly --standalone -m cert-renewal@example.com -d "sidecar.example.com,helper.example.com"`
    1. Note that you must point directly to `.venv/bin/certbot` as `sudo` does not operate in the virtualenv.
5. Accept the [Let's Encrypt terms](https://letsencrypt.org/documents/LE-SA-v1.3-September-21-2022.pdf).


### Make Configuration

For this stage, you'll need to know a few things about the other parties involved:
1. Their root domain
2. Their public keys
3. Everyone's *identity* (e.g., 0, 1, 2, 3)


Once you know these:
1. Make a config directory `mkdir config`
2. Copy the default network config: `cp local_dev/config/network.toml config/.`
3. Update that file.
    1. Replace `helper0.draft.test` and `sidecar0.draft.test` with the respective domains for party with identity=0.
    2. Repeat for identity= 1, 2, and 3.
    3. Replace respective certificates with their public keys.
4. Move your Let's Encrypt key and cert into place: `sudo ln -s /etc/letsencrypt/live/sidecar.example.com/fullchain.pem config/cert.pem` and `sudo ln -s /etc/letsencrypt/live/sidecar.example.com/privkey.pem key.pem`
5. Generate IPA-specific keys:
    1. Compile `ipa` with `cargo build --bin helper --features="web-app real-world-infra compact-gate stall-detection multi-threading" --no-default-features --release`
    2. Make the keys with `target/release/helper keygen --name localhost --tls-key h1.key --tls-cert h1.pem --mk-public-key h1_mk.pub --mk-private-key h1_mk.key` (replace h1 with for each helper)
    3. Add the public keys content into `network.toml`
    4. Add the public keys to `config/pub` (all helpers need all helper public keys).
    4. For each helper, put their private keys in `config`.


### Run draft

```
draft start-helper-sidecar --identity <identity> --root_domain example.com --config_path config
```

This will start the sidecar in the background. To confirm, visit `example.com/status`.


## Local Dev

`draft` provides a fully functional local development setup to work on both the frontend web interface and the sidecar.

### Running local development

If `draft` and the other prerequisites are already installed, run:
```
draft start-local-dev
```

You can follow the logs with:
```
draft follow-local-dev-logs
```

And you can view the front end at [https://draft.test](https://draft.test).



### Prerequisites

Requirements:
1. Python 3.11
2. Node 20
3. [Supabase CLI](https://supabase.com/docs/guides/cli/getting-started)
4. Docker

#### macOS install prerequisites

```brew install python3```
```brew install node```
```brew install supabase/tap/supabase```
```brew install traefik```


**Docker**

There are multiple options to run Docker locally. One such option is [colima](https://github.com/abiosoft/colima).

```
brew install docker
brew install colima
ln -sf ~/.colima/docker.sock /var/run/docker.sock
```

The `ln` at the end is because Supabase requires interacting with the local Docker API. See [this Supabase issue](https://github.com/supabase/cli/issues/153) and [this colima issue.](https://github.com/abiosoft/colima/issues/144) This likely requires `sudo`.

### Installation

Make sure the repo is cloned, and you're working in the root directory of the repo:

```
git clone https://github.com/eriktaubeneck/draft.git
cd draft
```

**Start colima and supabse:**

```
colima start
supabase start --workdir server
```
In the output, you'll find an `ANON_KEY`. Create the file `server/.env.development.local` and add:

```
NEXT_PUBLIC_SUPABASE_ANON_KEY="<ANON_KEY>"
```

**Add local draft.test domain to `/etc/hosts`:**

```
echo "#draft local domains\n127.0.0.1 draft.test\n127.0.0.1 sidecar0.draft.test\n127.0.0.1 sidecar1.draft.test\n127.0.0.1 sidecar2.draft.test\n127.0.0.1 sidecar3.draft.test" | sudo tee -a /etc/hosts
```

**make local certs**

install mkcert with

```
brew install mkcert
```

make the cert with

```
mkcert -cert-file "local_dev/config/cert.pem" -key-file "local_dev/config/key.pem" "draft.test" "*.draft.test"
```

If you get a warning about the cert not being installed (i.e., it's the first time you've used mkcert), also run:
```
mkcert -install
```

### Install draft

```
python -m venv .venv
source .venv/bin/activate
pip install --editable .
```

## Appendix

### IPA-specific certs

We check in self-signed certs that are only for local development (and are not secure! They are in a public repo!)

They will periodically expire. You can regenerate them with a compiled helper binary:

```
target/release/helper keygen --name helper1.draft.test --tls-key local_dev/config/h1.key --tls-cert local_dev/config/pub/h1.pem --mk-public-key local_dev/config/pub/h1_mk.pub --mk-private-key local_dev/config/h1_mk.key
target/release/helper keygen --name helper2.draft.test --tls-key local_dev/config/h2.key --tls-cert local_dev/config/pub/h2.pem --mk-public-key local_dev/config/pub/h2_mk.pub --mk-private-key local_dev/config/h2_mk.key
target/release/helper keygen --name helper3.draft.test --tls-key local_dev/config/h3.key --tls-cert local_dev/config/pub/h3.pem --mk-public-key local_dev/config/pub/h3_mk.pub --mk-private-key local_dev/config/h3_mk.key
```

The public content will also need to be pasted into `local_dev/config/network.toml` for each helper.

### Local Github Authentication

By default, local authentication is turned off (technically, you're automatically logged in as a demo user.) If you want to test Github authentication locally, you'll need to create a new application for development. Visit [https://github.com/settings/apps/new](https://github.com/settings/apps/new) to create a new Github app using the following parameters:
1. *name*: draft-local-dev (recommended, but not required)
2. *Homepage URL:* http://localhost:54321
3. *Callback URL:* http://localhost:54321/auth/v1/callback
4. *Request user authorization (OAuth) during installation:* yes
5. *Webhook active:* false
6. *Permissions:* Read-only access to email address
7. *Where can this GitHub App be installed?:* Only on this account

Once you have created the app, you'll need to update `server/.env.development.local` to include both the `CLIENT_ID` and a generated `CLIENT_SECRET`, and set the `BYPASS_AUTH` flag.

```
SUPABASE_AUTH_GITHUB_CLIENT_ID="<CLIENT_ID>"
SUPABASE_AUTH_GITHUB_SECRET="<CLIENT_SECRET>"
BYPASS_AUTH=false
```



# Credit
[Beer tap icons created by wanicon - Flaticon]("https://www.flaticon.com/free-icons/beer-tap")
