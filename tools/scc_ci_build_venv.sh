#!/bin/bash
# Build one cached CI venv inside an SGE job (submitted by scc_ci_status.py submit).
# Env: PROJECT_ROOT (worktree of the tested SHA), VENV_DIR (cache path .../venvs/<repo>/<hash12>),
#      LOCKFILE (path relative to PROJECT_ROOT, default requirements-dev.lock).
# Mirrors EnzymeFinder scripts/build_project_venv.sh step for step (that script hardcodes
# VENV_DIR=$PROJECT_ROOT/.venv, so it cannot target the cache), then writes VENV_DIR/.scc_ci_ok.
# flock serialises concurrent builds of the same hash; the second one sees the marker and exits.
set -euo pipefail
: "${PROJECT_ROOT:?}" "${VENV_DIR:?}"
LOCKFILE="${LOCKFILE:-requirements-dev.lock}"
PY311="${PY311:-/usr/bin/python3.11}"
MARKER="${VENV_DIR}/.scc_ci_ok"

mkdir -p "$(dirname "$VENV_DIR")"
exec 9>"${VENV_DIR}.lock"
flock 9
if [[ -f "$MARKER" ]]; then echo "venv ${VENV_DIR} already built"; exit 0; fi

echo "Building ${VENV_DIR} from ${LOCKFILE} using $($PY311 --version)"
rm -rf "$VENV_DIR"
"$PY311" -m venv "$VENV_DIR"
"${VENV_DIR}/bin/python" -m pip install --quiet --upgrade pip
"${VENV_DIR}/bin/python" -m pip install --quiet -r "${PROJECT_ROOT}/${LOCKFILE}"
"${VENV_DIR}/bin/python" -m pip install --quiet -e "${PROJECT_ROOT}" --no-deps
PYTHON_BIN="${VENV_DIR}/bin/python" VENV_DIR="$VENV_DIR" PROJECT_ROOT="$PROJECT_ROOT" \
  bash "${PROJECT_ROOT}/scripts/ensure_polars_compat.sh"
"${VENV_DIR}/bin/python" "${PROJECT_ROOT}/scripts/env_lock_hash.py" --check --python "${VENV_DIR}/bin/python"
touch "$MARKER"
echo "OK: ${VENV_DIR} built and verified"
