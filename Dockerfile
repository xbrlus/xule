ARG PYTHON_VERSION=3.14
FROM python:${PYTHON_VERSION}-slim

ARG ARELLE_VERSION=2.41.6
ARG XULE_VERSION=30052
ARG XULE_REPO=xbrlus
ARG EDGAR_VERSION=26.1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      git \
      gcc \
      g++ \
      python3-dev \
      libxml2-dev \
      libxslt1-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
      lxml==5.2.2 \
      isodate==0.6.1 \
      aniso8601==9.0.1 \
      holidays==0.52 \
      regex \
      tabulate \
      NumPy==1.26.2 \
      pyparsing==3.1.2 \
      Arelle-release==${ARELLE_VERSION}

RUN SITE_PACKAGES=$(python -c "import sysconfig; print(sysconfig.get_paths()['purelib'])") && \
    git clone --depth=1 --branch ${XULE_VERSION} --single-branch \
      https://github.com/${XULE_REPO}/xule.git /tmp/xule && \
    mkdir -p "$SITE_PACKAGES/arelle/plugin/validate" && \
    mv /tmp/xule/plugin/xule "$SITE_PACKAGES/arelle/plugin/xule" && \
    mv /tmp/xule/plugin/semanticHash.py "$SITE_PACKAGES/arelle/plugin/semanticHash.py" && \
    mv /tmp/xule/plugin/validate/DQC.py "$SITE_PACKAGES/arelle/plugin/validate/DQC.py" && \
    rm -rf /tmp/xule && \
    git clone --depth=1 --branch ${EDGAR_VERSION} --single-branch \
      https://github.com/Arelle/EDGAR.git /tmp/EDGAR && \
    rm -rf /tmp/EDGAR/.git && \
    mv /tmp/EDGAR "$SITE_PACKAGES/arelle/plugin/EDGAR"

WORKDIR /workspace
