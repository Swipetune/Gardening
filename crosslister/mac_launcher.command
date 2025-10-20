#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
PYTHON_BIN="${PYTHON_BIN:-python3}"

DEFAULT_CSV="$PROJECT_ROOT/data/listings.csv"
DEFAULT_IMAGES="$PROJECT_ROOT/data/images"
DEFAULT_CREDENTIALS="$PROJECT_ROOT/config/credentials.json"
DEFAULT_COOKIES="$HOME/Library/Application Support/Crosslister/cookies"
DEFAULT_CATEGORY_MAP="$PROJECT_ROOT/data/category_map.json"
DEFAULT_DELAY_MIN=12
DEFAULT_DELAY_MAX=18
DEFAULT_MAX_PARALLEL=1
DEFAULT_PLATFORMS="marktplaats, tweedehands, facebook, vinted"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: $PYTHON_BIN is not installed or not on PATH." >&2
  exit 1
fi

prompt() {
  local label="$1"
  local default_value="$2"
  local input
  read -r -p "$label [$default_value]: " input || exit 1
  if [ -z "$input" ]; then
    echo "$default_value"
  else
    echo "$input"
  fi
}

CSV_PATH=$(prompt "CSV-bestand" "$DEFAULT_CSV")
IMAGES_DIR=$(prompt "Map met afbeeldingen" "$DEFAULT_IMAGES")
CREDENTIALS_PATH=$(prompt "Credentials-bestand" "$DEFAULT_CREDENTIALS")
COOKIES_DIR=$(prompt "Cookies-map" "$DEFAULT_COOKIES")
CATEGORY_MAP_PATH=$(prompt "Category-map (JSON)" "$DEFAULT_CATEGORY_MAP")
PLATFORM_INPUT=$(prompt "Platforms (comma separated)" "$DEFAULT_PLATFORMS")
DELAY_MIN=$(prompt "Minimale vertraging (s)" "$DEFAULT_DELAY_MIN")
DELAY_MAX=$(prompt "Maximale vertraging (s)" "$DEFAULT_DELAY_MAX")
MAX_PARALLEL=$(prompt "Max. aantal gelijktijdige browser-tabs" "$DEFAULT_MAX_PARALLEL")
HEADLESS_INPUT=$(prompt "Headless mode? (yes/no)" "no")

HEADLESS_FLAG=()
case "${HEADLESS_INPUT,,}" in
  y|yes)
    HEADLESS_FLAG=(--headless)
    ;;
  *)
    HEADLESS_FLAG=()
    ;;
esac

IFS=',' read -r -a PLATFORM_ARRAY <<< "$PLATFORM_INPUT"
TRIMMED_PLATFORMS=()
for item in "${PLATFORM_ARRAY[@]}"; do
  value="${item//[^[:alnum:]_ -]/}"
  value="$(echo "$value" | sed -e 's/^ *//' -e 's/ *$//')"
  value="${value,,}"
  if [ -n "$value" ]; then
    TRIMMED_PLATFORMS+=("$value")
  fi
done

if [ "${#TRIMMED_PLATFORMS[@]}" -eq 0 ]; then
  echo "Geen platforms gekozen; gebruik standaard." >&2
  read -r -a TRIMMED_PLATFORMS <<< "${DEFAULT_PLATFORMS//,/ }"
fi

mkdir -p "$COOKIES_DIR"

number_re='^[0-9]+([.][0-9]+)?$'
if ! [[ $DELAY_MIN =~ $number_re ]]; then
  echo "Ongeldige minimale vertraging: $DELAY_MIN" >&2
  exit 1
fi
if ! [[ $DELAY_MAX =~ $number_re ]]; then
  echo "Ongeldige maximale vertraging: $DELAY_MAX" >&2
  exit 1
fi
if ! [[ $MAX_PARALLEL =~ ^[0-9]+$ ]]; then
  echo "Ongeldig aantal tabs: $MAX_PARALLEL" >&2
  exit 1
fi

if command -v bc >/dev/null 2>&1; then
  if (( $(echo "$DELAY_MIN > $DELAY_MAX" | bc -l) )); then
    tmp="$DELAY_MIN"
    DELAY_MIN="$DELAY_MAX"
    DELAY_MAX="$tmp"
  fi
else
  awk "BEGIN{exit !($DELAY_MIN > $DELAY_MAX)}" >/dev/null 2>&1 && {
    tmp="$DELAY_MIN"
    DELAY_MIN="$DELAY_MAX"
    DELAY_MAX="$tmp"
  }
fi

COMMAND=("$PYTHON_BIN" -m crosslister.main "$CSV_PATH" \
  --images-dir "$IMAGES_DIR" \
  --credentials "$CREDENTIALS_PATH" \
  --cookies-dir "$COOKIES_DIR" \
  --category-map "$CATEGORY_MAP_PATH" \
  --delay "$DELAY_MIN" "$DELAY_MAX" \
  --max-parallel "$MAX_PARALLEL" \
  --platforms)

for platform in "${TRIMMED_PLATFORMS[@]}"; do
  COMMAND+=("$platform")
done

if [ "${#HEADLESS_FLAG[@]}" -gt 0 ]; then
  COMMAND+=("${HEADLESS_FLAG[@]}")
fi

cd "$PROJECT_ROOT"

echo "Running: ${COMMAND[*]}"
"${COMMAND[@]}"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ Crosslister voltooid."
else
  echo "❌ Crosslister eindigde met foutcode $EXIT_CODE"
fi

echo "Resultaten in: $(cd "$PROJECT_ROOT" && pwd)/crosslister_output.json"

echo "Druk op Enter om af te sluiten..."
read -r _ || true
