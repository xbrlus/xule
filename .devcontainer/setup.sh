#!/usr/bin/env bash
# Sets up the codespace with Python, Arelle, the EDGAR transform/validate
# plugins, and the XULE plugin (linked from this checkout so edits under
# plugin/xule take effect immediately, without reinstalling).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Installing system build dependencies"
if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
else
  SUDO=""
fi
$SUDO apt-get update
$SUDO apt-get install -y --no-install-recommends \
  git gcc g++ python3-dev libxml2-dev libxslt1-dev curl
$SUDO rm -rf /var/lib/apt/lists/*

echo "==> Installing Python dependencies and Arelle"
PYTHON_BIN="$(command -v python)"
$SUDO "$PYTHON_BIN" -m pip install --no-cache-dir \
  lxml==5.2.2 \
  isodate==0.6.1 \
  aniso8601==9.0.1 \
  holidays==0.52 \
  regex \
  tabulate \
  NumPy==1.26.2 \
  pyparsing==3.1.2 \
  pytz \
  Arelle-release

SITE_PACKAGES=$("$PYTHON_BIN" -c "import sysconfig; print(sysconfig.get_paths()['purelib'])")

echo "==> Linking the XULE plugin from this checkout ($REPO_ROOT/plugin)"
$SUDO mkdir -p "$SITE_PACKAGES/arelle/plugin/validate"
$SUDO ln -sfn "$REPO_ROOT/plugin/xule" "$SITE_PACKAGES/arelle/plugin/xule"
$SUDO ln -sfn "$REPO_ROOT/plugin/semanticHash.py" "$SITE_PACKAGES/arelle/plugin/semanticHash.py"
$SUDO ln -sfn "$REPO_ROOT/plugin/validate/DQC.py" "$SITE_PACKAGES/arelle/plugin/validate/DQC.py"

echo "==> Installing the EDGAR transform and validate plugins"
$SUDO rm -rf "$SITE_PACKAGES/arelle/plugin/EDGAR" /tmp/EDGAR
git clone --depth=1 https://github.com/Arelle/EDGAR.git /tmp/EDGAR
rm -rf /tmp/EDGAR/.git
$SUDO mv /tmp/EDGAR "$SITE_PACKAGES/arelle/plugin/EDGAR"
$SUDO chown -R "$(id -u):$(id -g)" "$SITE_PACKAGES/arelle/plugin/EDGAR"

echo "==> Fetching DQC US Rules example resources (latest release)"
DQC_TARGET="$REPO_ROOT/dqc_us_rules"
DQC_TMP=$(mktemp -d)

DQC_TAG=$(curl -fsSL https://api.github.com/repos/DataQualityCommittee/dqc_us_rules/releases/latest \
  | "$PYTHON_BIN" -c "import json,sys; print(json.load(sys.stdin)['tag_name'])")
echo "Latest dqc_us_rules release: $DQC_TAG"
curl -fsSL "https://github.com/DataQualityCommittee/dqc_us_rules/archive/refs/tags/${DQC_TAG}.tar.gz" \
  -o "$DQC_TMP/dqc_us_rules.tar.gz"
tar -xzf "$DQC_TMP/dqc_us_rules.tar.gz" -C "$DQC_TMP"
DQC_SRC_ROOT=$(find "$DQC_TMP" -maxdepth 1 -type d -name "dqc_us_rules-*")

# Everything from dqc_us_rules (resources, source incl. lib, taxonomy) lands under
# <repo root>/dqc_us_rules -- nothing stays under Examples anymore.
mkdir -p "$DQC_TARGET/resources" "$DQC_TARGET/source/us" "$DQC_TARGET/taxonomy/us"
rm -rf "$DQC_TARGET/resources/Effective_Dates" "$DQC_TARGET/resources/rule-form-lookup" "$DQC_TARGET/source/lib"
cp -a "$DQC_SRC_ROOT/dqc_us_rules/resources/Effective_Dates" "$DQC_TARGET/resources/Effective_Dates"
cp -a "$DQC_SRC_ROOT/dqc_us_rules/resources/rule-form-lookup" "$DQC_TARGET/resources/rule-form-lookup"
cp -a "$DQC_SRC_ROOT/dqc_us_rules/source/lib" "$DQC_TARGET/source/lib"

LATEST_YEAR=$(ls "$DQC_SRC_ROOT/dqc_us_rules/source/us" | sort -n | tail -1)
echo "Latest dqc_us_rules/source/us year: $LATEST_YEAR"
rm -rf "$DQC_TARGET/source/us/$LATEST_YEAR"
cp -a "$DQC_SRC_ROOT/dqc_us_rules/source/us/$LATEST_YEAR" "$DQC_TARGET/source/us/$LATEST_YEAR"

if [ -d "$DQC_SRC_ROOT/dqc_us_rules/taxonomy/us/$LATEST_YEAR" ]; then
  rm -rf "$DQC_TARGET/taxonomy/us/$LATEST_YEAR"
  cp -a "$DQC_SRC_ROOT/dqc_us_rules/taxonomy/us/$LATEST_YEAR" "$DQC_TARGET/taxonomy/us/$LATEST_YEAR"
else
  echo "Warning: no dqc_us_rules/taxonomy/us/$LATEST_YEAR folder found; skipping"
fi

rm -rf "$DQC_TMP"

echo "==> Overwriting .vscode config for $LATEST_YEAR from xbrlus/xule-editor"
XULE_EDITOR_TMP=$(mktemp -d)
curl -fsSL "https://github.com/xbrlus/xule-editor/archive/refs/heads/master.tar.gz" \
  -o "$XULE_EDITOR_TMP/xule-editor.tar.gz"
tar -xzf "$XULE_EDITOR_TMP/xule-editor.tar.gz" -C "$XULE_EDITOR_TMP"
XULE_EDITOR_SRC_ROOT=$(find "$XULE_EDITOR_TMP" -maxdepth 1 -type d -name "xule-editor-*")

if [ -d "$XULE_EDITOR_SRC_ROOT/source/us/$LATEST_YEAR/.vscode" ]; then
  rm -rf "$DQC_TARGET/source/us/$LATEST_YEAR/.vscode"
  cp -a "$XULE_EDITOR_SRC_ROOT/source/us/$LATEST_YEAR/.vscode" "$DQC_TARGET/source/us/$LATEST_YEAR/.vscode"
else
  echo "Warning: no .vscode folder found for year $LATEST_YEAR in xule-editor/source/us; skipping"
fi

rm -rf "$XULE_EDITOR_TMP"

echo "==> Writing workspace XULE settings for VS Code"
mkdir -p "$DQC_TARGET/source/us/$LATEST_YEAR/.vscode"
cat > "$DQC_TARGET/source/us/$LATEST_YEAR/.vscode/settings.json" <<EOF
{
  "files.associations": {
    "*.xule": "xule"
  },
  "xule.autoImports": [
    "dqc_us_rules/source/us/$LATEST_YEAR/constant.xule",
    "dqc_us_rules/source/us/$LATEST_YEAR/functions.xule",
    "dqc_us_rules/source/us/$LATEST_YEAR/namespace.xule",
    "dqc_us_rules/source/us/$LATEST_YEAR/version.xule",
    "dqc_us_rules/source/us/$LATEST_YEAR/resources.xule",
    "dqc_us_rules/source/us/$LATEST_YEAR/base-taxonomy-$LATEST_YEAR.xule",
    "dqc_us_rules/source/us/$LATEST_YEAR/base-taxonomy-$LATEST_YEAR-entire.xule",
    "dqc_us_rules/source/us/$LATEST_YEAR/constant-us-gaap.xule"
  ],
  "xule.namespaces.definitions": [
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-us-gaap-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-us-gaap-ebp-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-xbrl-sec-gov-dei-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-srt-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-xbrl-sec-gov-country-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-xbrl-sec-gov-currency-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-us-types-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-srt-types-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-xbrl-sec-gov-ecd-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-www-xbrl-org-dtr-type-2024-01-31.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0001-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0004-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0005-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0006-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0008-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0009-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0015-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0033-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0036-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0041-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0043-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0044-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0048-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0060-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0079-$LATEST_YEAR.json"
  ]
}
EOF

mkdir -p "$REPO_ROOT/.vscode"
cat > "$REPO_ROOT/.vscode/settings.json" <<EOF
{
  "files.associations": {
    "*.xule": "xule"
  },
  "xule.autoImports": [
    "dqc_us_rules/source/us/$LATEST_YEAR/constant.xule",
    "dqc_us_rules/source/us/$LATEST_YEAR/functions.xule",
    "dqc_us_rules/source/us/$LATEST_YEAR/namespace.xule",
    "dqc_us_rules/source/us/$LATEST_YEAR/version.xule",
    "dqc_us_rules/source/us/$LATEST_YEAR/resources.xule",
    "dqc_us_rules/source/us/$LATEST_YEAR/base-taxonomy-$LATEST_YEAR.xule",
    "dqc_us_rules/source/us/$LATEST_YEAR/base-taxonomy-$LATEST_YEAR-entire.xule",
    "dqc_us_rules/source/us/$LATEST_YEAR/constant-us-gaap.xule"
  ],
  "xule.namespaces.definitions": [
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-us-gaap-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-us-gaap-ebp-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-xbrl-sec-gov-dei-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-srt-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-xbrl-sec-gov-country-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-xbrl-sec-gov-currency-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-us-types-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-srt-types-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-xbrl-sec-gov-ecd-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-www-xbrl-org-dtr-type-2024-01-31.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0001-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0004-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0005-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0006-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0008-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0009-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0015-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0033-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0036-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0041-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0043-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0044-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0048-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0060-$LATEST_YEAR.json",
    "dqc_us_rules/taxonomy/us/$LATEST_YEAR/http-fasb-org-dqcrules-0079-$LATEST_YEAR.json"
  ]
}
EOF

echo "==> Verifying plugin activation"
python -m arelle.CntlrCmdLine --plugins "xule|EDGAR/transform|EDGAR/validate" --about

cat <<'EOF'

Setup complete. Run XULE with, e.g.:
  python -m arelle.CntlrCmdLine --plugins "xule|EDGAR/transform|EDGAR/validate" [other options]

The XULE Editor VS Code extension (XBRLUS.xule) is installed for syntax
highlighting of .xule files.
EOF
