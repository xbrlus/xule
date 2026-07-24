An open-source XBRL processor for business rules, rendering and custom data reporting. See https://xbrl.us/xule for documentation and https://xbrl.us/xule-editor for a VS Code syntax highlighter.

[XULE README](plugin/xule/README.md)

Interactive Example - Running XULE in Arelle  
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/xbrlus/xule/jupyter?filepath=sample.ipynb)  
[![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/xbrlus/xule/blob/jupyter/sample-colab.ipynb)  
[Learn about using XULE and XBRL](https://xbrl.us/online-learning)

## Docker

A [Dockerfile](Dockerfile) is provided that builds a ready-to-run environment with Python, Arelle, and the XULE and EDGAR plugins installed. The [Build XULE Container](.github/workflows/buildcontainer.yml) GitHub Action builds this image and pushes it to `ghcr.io/xbrlus/xule`.

### Using the pre-built image

```
docker pull ghcr.io/xbrlus/xule:latest
docker run --rm -v "$(pwd):/workspace" ghcr.io/xbrlus/xule:latest \
  python -m arelle.CntlrCmdLine --plugin xule --about
```

### Building locally

```
docker build -t xule .
```

Versions can be overridden with build args:

```
docker build \
  --build-arg PYTHON_VERSION=3.14 \
  --build-arg ARELLE_VERSION=2.41.6 \
  --build-arg EDGAR_VERSION=26.1 \
  --build-arg XULE_VERSION=30052 \
  -t xule .
```

- `PYTHON_VERSION` - Python base image version (default `3.14`)
- `ARELLE_VERSION` - `Arelle-release` PyPI package version (default `2.41.6`)

### Building via the GitHub Action

Run the **Build XULE Container** workflow from the Actions tab (`workflow_dispatch`). Leave the inputs blank to build with the latest available release of Python, Arelle, and XULE, or set any of them to pin a specific version:

- `ref` - branch, tag, or SHA of this repo to build XULE from
- `python_version` - Python version for the base image
- `arelle_version` - `Arelle-release` package version

## License and Patent

See [License](https://xbrl.us/dqc-license) for license information.  
See [Patent Notice](https://xbrl.us/dqc-patent) for patent infringement notice.

Copyright 2015 - 2026 XBRL US, Inc. All rights reserved.
