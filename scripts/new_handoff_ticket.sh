#!/usr/bin/env bash
set -euo pipefail

FROM=""
TO=""
EPIC=""
PRIORITY="P1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from)
      FROM="$2"
      shift 2
      ;;
    --to)
      TO="$2"
      shift 2
      ;;
    --epic)
      EPIC="$2"
      shift 2
      ;;
    --priority)
      PRIORITY="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: bash scripts/new_handoff_ticket.sh --from <agent> --to <agent> --epic <name> [--priority P0|P1|P2]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "${FROM}" || -z "${TO}" || -z "${EPIC}" ]]; then
  echo "Missing required arguments." >&2
  echo "Usage: bash scripts/new_handoff_ticket.sh --from <agent> --to <agent> --epic <name> [--priority P0|P1|P2]" >&2
  exit 1
fi

if [[ "${PRIORITY}" != "P0" && "${PRIORITY}" != "P1" && "${PRIORITY}" != "P2" ]]; then
  echo "Priority must be one of: P0, P1, P2" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TEMPLATE_PATH="${REPO_ROOT}/templates/handoff-ticket.template.md"
OUT_DIR="${REPO_ROOT}/agents/contracts/tickets"

if [[ ! -f "${TEMPLATE_PATH}" ]]; then
  echo "Template not found at ${TEMPLATE_PATH}" >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"

STAMP="$(date +"%Y%m%d-%H%M%S")"
TICKET_ID="T-${STAMP}"
TO_LOWER="$(echo "${TO}" | tr '[:upper:]' '[:lower:]')"
OUT_PATH="${OUT_DIR}/${TICKET_ID}-${TO_LOWER}.md"
NOW_TS="$(date +"%Y-%m-%d %H:%M:%S")"

python - "${TEMPLATE_PATH}" "${OUT_PATH}" "${TICKET_ID}" "${FROM}" "${TO}" "${PRIORITY}" "${NOW_TS}" "${EPIC}" <<'PY'
import re
import sys

(
    template_path,
    out_path,
    ticket_id,
    from_agent,
    to_agent,
    priority,
    now_ts,
    epic,
) = sys.argv[1:]

with open(template_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("<TICKET_ID>", ticket_id)
content = content.replace("<AGENT_NAME>", from_agent)
content = content.replace("<P0|P1|P2>", priority)
content = content.replace("<DATE/TIME>", now_ts)
content = content.replace("<EPIC_NAME>", epic)
content = re.sub(r"- To: .*", f"- To: {to_agent}", content, count=1)

with open(out_path, "w", encoding="utf-8") as f:
    f.write(content)
PY

echo "Created handoff ticket: ${OUT_PATH}"
