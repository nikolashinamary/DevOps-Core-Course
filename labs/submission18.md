# Lab 18 Submission — Reproducible Builds with Nix

## Repository Scope

- Lab workspace: `labs/lab18/app_python`
- Evidence directory: `labs/lab18/evidence`
- Branch: `feature/lab18`

---

## Task 1 — Reproducible Python App with Nix (6 pts)

### 1.1 Nix Installation and Verification

Installed using the Determinate Systems installer:

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

Verification:

```
$ nix --version
nix (Determinate Nix 3.19.0) 2.34.6

$ nix run nixpkgs#hello
Hello, World!
```

Flakes are enabled by default with the Determinate installer — no manual `nix.conf` edits needed.

### 1.2 Application Overview

The app is the DevOps Info Service from Lab 1 — a Flask application exposing `/`, `/health`, `/visits`, and `/metrics` endpoints. Source lives in `labs/lab18/app_python/`.

`requirements.txt`:
```
Flask==3.1.0
prometheus-client==0.23.1
```

Traditional Lab 1 workflow:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Problems with this approach:
- Python interpreter version depends on the host system
- `pip install` resolves transitive dependencies at runtime — they can change between runs
- Virtual environment is not portable across machines
- No cryptographic guarantee of what was actually installed

### 1.3 Nix Derivation

File: `labs/lab18/app_python/default.nix`

```nix
{ pkgs }:

pkgs.python313Packages.buildPythonApplication rec {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = [
    pkgs.python313Packages.flask
    pkgs.python313Packages.prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin
    mkdir -p $out/libexec/${pname}

    cp app.py $out/libexec/${pname}/app.py
    chmod +x $out/libexec/${pname}/app.py

    makeWrapper ${pkgs.python313}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/libexec/${pname}/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH"

    runHook postInstall
  '';

  doCheck = false;
}
```

Field explanations:
- `buildPythonApplication` — builds an installable Python app with proper wrappers
- `pname` / `version` — package identity, used to compute the store path hash
- `src = ./.` — source is the current directory; Nix copies it into a pure sandbox
- `format = "other"` — tells Nix this is not a setuptools/pyproject package
- `propagatedBuildInputs` — runtime Python dependencies resolved from the pinned nixpkgs revision
- `nativeBuildInputs = [ pkgs.makeWrapper ]` — build-time tool to wrap the script with the correct interpreter
- `installPhase` — copies `app.py` to the store and creates a wrapper binary that sets `PYTHONPATH`
- `doCheck = false` — skips the test phase

Build and run:

```bash
$ nix build .#default --print-out-paths
/nix/store/l1km4rvmr03x328y8qpbablhm6aqxfmr-devops-info-service-1.0.0

$ VISITS_FILE=/tmp/lab18-visits PORT=8080 ./result/bin/devops-info-service
```

Screenshots: see below.

### 1.4 Reproducibility Proof

Build 1:
```
$ nix build .#default --print-out-paths
/nix/store/l1km4rvmr03x328y8qpbablhm6aqxfmr-devops-info-service-1.0.0
```

Delete from store and rebuild:
```
$ nix-store --delete /nix/store/l1km4rvmr03x328y8qpbablhm6aqxfmr-devops-info-service-1.0.0
$ nix build .#default --print-out-paths
/nix/store/l1km4rvmr03x328y8qpbablhm6aqxfmr-devops-info-service-1.0.0
```

**Identical store path.** Nix rebuilt from scratch and produced the exact same hash.

NAR hash of the output:
```
$ nix hash path result
sha256-DEcZL8zebpIsiBoVZxEJi0Sdiir6onPh9UI8pZJ2XKU=
```

Evidence files: `task1-store-path-1.txt`, `task1-store-path-2.txt`, `task1-result-sha256.txt`

#### Nix store path format explained

```
/nix/store/l1km4rvmr03x328y8qpbablhm6aqxfmr-devops-info-service-1.0.0
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^^^^^^^^^^^
           32-char base32 hash               human-readable name
```

The hash is computed from all source files, all declared dependencies and their transitive closure, build instructions, and toolchain versions. Same inputs → same hash → Nix reuses the cached build.

#### pip vs Nix comparison

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
|--------|-------------------|--------------|
| Python version | System-dependent | Pinned in derivation (`python313`) |
| Dependency resolution | Runtime (`pip install`) | Build-time (pure sandbox) |
| Transitive deps | Not pinned | Pinned via nixpkgs revision |
| Reproducibility | Approximate | Bit-for-bit identical |
| Portability | Requires same OS + Python | Works anywhere Nix runs |
| Binary cache | No | Yes (`cache.nixos.org`) |
| Isolation | Virtual environment | Sandboxed build (no network, no `/home`) |

#### Reflection: How would Nix have helped in Lab 1?

With Nix from the start every team member would get the exact same Python 3.13.5 and Flask 3.1.0 with identical transitive deps. CI would produce the same binary as local development. Onboarding would be `nix develop` instead of "install Python, create venv, pip install, debug version mismatches".

---

## Task 2 — Reproducible Docker Images with Nix (4 pts)

### 2.1 Lab 2 Dockerfile Review

File: `labs/lab18/app_python/Dockerfile`

```dockerfile
FROM python:3.13-slim
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
CMD ["python", "app.py"]
```

### 2.2 Lab 2 Dockerfile Reproducibility Test

Two no-cache builds of the same Dockerfile:

```bash
docker build --no-cache -t lab18-lab2-nocache1 ./app_python
docker build --no-cache -t lab18-lab2-nocache2 ./app_python
```

Created timestamps:
```
Build 1: 2026-05-11T18:03:59.140947877+03:00
Build 2: 2026-05-11T18:04:07.405291272+03:00
```

Saved image SHA256:
```
Build 1: 74d688232fd3d2f63275ee6b6cf97ff7567353e5d0b9327b97ec911a6b6b0b16
Build 2: e2f2845fb7188bb88ef889925af022d71e9dde3dbe4593fcf80802e0f7ff9491
```

**Different hashes from identical source.** The Dockerfile is not reproducible — timestamps are embedded in every layer.

Evidence: `task2-lab2-nocache-created-1.txt`, `task2-lab2-nocache-created-2.txt`, `task2-lab2-nocache-save-sha256-1.txt`, `task2-lab2-nocache-save-sha256-2.txt`

### 2.3 Nix Docker Image

File: `labs/lab18/app_python/docker.nix`

```nix
{ pkgs }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  copyToRoot = pkgs.buildEnv {
    name = "image-root";
    paths = [ app pkgs.coreutils ];
    pathsToLink = [ "/bin" "/libexec" ];
  };

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
  };

  created = "1970-01-01T00:00:01Z";
}
```

Field explanations:
- `dockerTools.buildImage` — produces a Docker-compatible `.tar.gz` without running Docker
- `copyToRoot` — declares exactly what goes into the image filesystem; no base image, no `apt-get`
- `pkgs.buildEnv` — merges multiple derivations into a single directory tree
- `config.Cmd` — uses the absolute Nix store path of the binary, so it never changes
- `created = "1970-01-01T00:00:01Z"` — fixed epoch timestamp; key to reproducibility

Build and load:

```bash
$ nix build .#dockerImage --print-out-paths
/nix/store/d8yx0cffg9dp0db00c5g7ivla384p4is-docker-image-devops-info-service-nix.tar.gz

$ docker load < result
Loaded image: devops-info-service-nix:1.0.0

$ docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0

$ curl -s http://localhost:5001/health
{"status":"healthy","timestamp":"2026-05-11T15:22:01.483920+00:00","uptime_seconds":3}
```

Evidence: `task2-nix-docker-build-1.txt`, `task2-nix-docker-run-1.txt`

### 2.4 Nix Docker Reproducibility Proof

```
Build 1: ecafa92dca6712a47183387bbd064ffcb08fe0d214725767b5c1de9027cdb6a9  result
         /nix/store/d8yx0cffg9dp0db00c5g7ivla384p4is-docker-image-devops-info-service-nix.tar.gz

Build 2: ecafa92dca6712a47183387bbd064ffcb08fe0d214725767b5c1de9027cdb6a9  result
         /nix/store/d8yx0cffg9dp0db00c5g7ivla384p4is-docker-image-devops-info-service-nix.tar.gz
```

**Identical SHA256 and identical store path.** The tarball is bit-for-bit identical across builds.

Evidence: `task2-nix-docker-sha256-1.txt`

### 2.5 Image Comparison

```
$ docker images | grep -E "lab18|devops-info-service-nix"
lab18-lab2-nocache2:latest      156MB
lab18-lab2-nocache1:latest      156MB
devops-info-service-nix:1.0.0   143MB
```

| Aspect | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|--------|-----------------|------------------------|
| Base image | `python:3.13-slim` (changes over time) | No base image |
| Timestamps | Different on each build | Fixed: `1970-01-01T00:00:01Z` |
| Package install | `pip install` at build time | Nix store paths (immutable) |
| Reproducibility | ❌ Different SHA256 each build | ✅ Identical SHA256 always |
| Image size | 156MB | 143MB |
| Security surface | Full Debian base + pip | Minimal closure only |

#### Why can't traditional Dockerfiles achieve bit-for-bit reproducibility?

1. **Timestamps** — Docker embeds the build time into every layer. Even `--no-cache` produces a different hash.
2. **Mutable tags** — `FROM python:3.13-slim` resolves to whatever image is behind that tag today.
3. **Runtime resolution** — `pip install` fetches from PyPI at build time; the index can change.

Nix avoids all three: fixed timestamp, content-addressed store paths, all deps resolved before the build starts.

---

## Bonus Task — Modern Nix with Flakes (2 pts)

### flake.nix

File: `labs/lab18/app_python/flake.nix`

```nix
{
  description = "Lab 18 - Reproducible builds for DevOps Info Service";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in
    {
      packages = forAllSystems (system:
        let pkgs = nixpkgs.legacyPackages.${system}; in
        {
          default = import ./default.nix { inherit pkgs; };
          dockerImage = import ./docker.nix { inherit pkgs; };
        }
      );

      devShells = forAllSystems (system:
        let pkgs = nixpkgs.legacyPackages.${system}; in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.python313
              pkgs.python313Packages.flask
              pkgs.python313Packages.prometheus-client
            ];
          };
        }
      );
    };
}
```

### flake.lock — Pinned nixpkgs

```json
{
  "nodes": {
    "nixpkgs": {
      "locked": {
        "narHash": "sha256-16KkgfdYqjaeRGBaYsNrhPRRENs0qzkQVUooNHtoy2w=",
        "owner": "NixOS",
        "repo": "nixpkgs",
        "rev": "ac62194c3917d5f474c1a844b6fd6da2db95077d",
        "type": "github"
      }
    }
  }
}
```

`rev: ac62194` pins all 80,000+ packages in nixpkgs to a single git commit — Python version, Flask, Werkzeug, every transitive dep, and the C compiler used to build them.

Evidence: `bonus-flake-lock.txt`, `bonus-flake-metadata.txt`

### nix develop vs Lab 1 venv

```bash
# Lab 1
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
# Python version: whatever is on the host

# Lab 18
nix develop
# Python 3.13.5, Flask 3.1.0 — locked in flake.lock, same on every machine
```

### Helm values.yaml vs Nix Flakes

| What is locked | Helm values.yaml | Nix flake.lock |
|----------------|-----------------|----------------|
| Container image tag | ✅ | ✅ (via store path hash) |
| Python version | ❌ | ✅ |
| Flask + transitive deps | ❌ | ✅ |
| Build toolchain | ❌ | ✅ |
| Cryptographic proof | ❌ | ✅ narHash |

Helm pins the deployment policy; Nix pins the entire build universe. Combined: build with Nix, deploy the content-hash tag via Helm.

---

## Screenshots

![Nix running and app built](evidence/screenshots/nix-running.png)
![App responding to health check](evidence/screenshots/app-running.png)
