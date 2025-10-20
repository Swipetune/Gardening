#!/bin/bash
# macOS launcher for the Crosslister automation suite.
# Provides a guided, colourised wizard so non-technical users can
# prepare all inputs before delegating to ``python -m crosslister.main``.

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
DEFAULT_PLATFORMS=(marktplaats tweedehands facebook vinted)

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: $PYTHON_BIN is niet gevonden. Installeer Python 3 en probeer opnieuw." >&2
  exit 1
fi

if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
  COLOR_BLUE="$(tput setaf 4)"
  COLOR_GREEN="$(tput setaf 2)"
  COLOR_YELLOW="$(tput setaf 3)"
  COLOR_RED="$(tput setaf 1)"
  COLOR_CYAN="$(tput setaf 6)"
  COLOR_RESET="$(tput sgr0)"
  STYLE_BOLD="$(tput bold)"
  tput clear
else
  COLOR_BLUE=""
  COLOR_GREEN=""
  COLOR_YELLOW=""
  COLOR_RED=""
  COLOR_CYAN=""
  COLOR_RESET=""
  STYLE_BOLD=""
fi

STEP=1

headline() {
  printf "\n%s%s==============================%s\n" "$COLOR_BLUE" "$STYLE_BOLD" "$COLOR_RESET"
  printf "%s%s%s\n" "$COLOR_BLUE" "   $1" "$COLOR_RESET"
  printf "%s==============================%s\n" "$COLOR_BLUE" "$COLOR_RESET"
}

step_heading() {
  local title="$1"
  printf "\n%s%sStap %d:%s %s%s\n" "$COLOR_GREEN" "$STYLE_BOLD" "$STEP" "$COLOR_RESET" "$STYLE_BOLD" "$title"
  printf "%s------------------------------%s\n" "$COLOR_GREEN" "$COLOR_RESET"
  STEP=$((STEP + 1))
}

info_line() {
  printf "  %s•%s %s\n" "$COLOR_CYAN" "$COLOR_RESET" "$1"
}

expand_path() {
  # Expand a leading ~ and collapse duplicated slashes without executing arbitrary code.
  local raw="$1"
  if [ -z "$raw" ]; then
    echo ""
    return
  fi
  case "$raw" in
    ~)
      echo "$HOME"
      ;;
    ~/*)
      echo "$HOME/${raw#~/}"
      ;;
    *)
      printf '%s
' "$raw"
      ;;
  esac
}

pause_for_user() {
  printf "\n%sDruk op Enter om verder te gaan (of typ 'q' om te stoppen).%s\n" "$COLOR_YELLOW" "$COLOR_RESET"
  if ! IFS= read -r response; then
    printf "%sGeen invoer gedetecteerd – ga automatisch verder.%s\n" "$COLOR_YELLOW" "$COLOR_RESET"
    return
  fi

  if [ -n "$response" ]; then
    local normalised
    normalised=$(printf '%s' "$response" | tr '[:upper:]' '[:lower:]')
    if [ "$normalised" = "q" ]; then
      printf "%sProces handmatig afgebroken.%s\n" "$COLOR_RED" "$COLOR_RESET"
      exit 0
    fi
  fi
}

choose_from_menu() {
  # Generic helper returning the user's choice number (defaulting to 1).
  local prompt_text="$1"
  local default_choice="${2:-1}"
  local choice
  printf "%s" "$prompt_text"
  read -r choice
  if [ -z "$choice" ]; then
    echo "$default_choice"
  else
    echo "$choice"
  fi
}

choose_path() {
  local label="$1"
  local default_value="$2"
  local choice
  local custom
  while true; do
    printf "\n%s%s%s\n" "$STYLE_BOLD" "$label" "$COLOR_RESET"
    info_line "1) Standaard gebruiken (${default_value})"
    info_line "2) Eigen pad ingeven"
    choice=$(choose_from_menu "Kies optie [1]: " 1)
    case "$choice" in
      1)
        echo "$default_value"
        return 0
        ;;
      2)
        printf "%sPad: %s" "$COLOR_GREEN" "$COLOR_RESET"
        read -r custom
        custom=$(expand_path "$custom")
        if [ -n "$custom" ]; then
          echo "$custom"
          return 0
        fi
        printf "%sGeen pad opgegeven, probeer opnieuw.%s\n" "$COLOR_RED" "$COLOR_RESET"
        ;;
      *)
        printf "%sOngeldige keuze.%s\n" "$COLOR_RED" "$COLOR_RESET"
        ;;
    esac
  done
}

choose_delay() {
  local default_min="$1"
  local default_max="$2"
  local choice
  local min_val
  local max_val

  printf "\n%sVertragingsinstellingen%s\n" "$STYLE_BOLD" "$COLOR_RESET"
  info_line "1) Rustig tempo (${default_min}-${default_max} seconden)"
  info_line "2) Extra voorzichtig (18-25 seconden)"
  info_line "3) Eigen bereik instellen"

  choice=$(choose_from_menu "Kies optie [1]: " 1)
  case "$choice" in
    1)
      echo "$default_min $default_max"
      return 0
      ;;
    2)
      echo "18 25"
      return 0
      ;;
    3)
      printf "%sMinimum (seconden): %s" "$COLOR_GREEN" "$COLOR_RESET"
      read -r min_val
      printf "%sMaximum (seconden): %s" "$COLOR_GREEN" "$COLOR_RESET"
      read -r max_val
      if [ -z "$min_val" ] || [ -z "$max_val" ]; then
        printf "%sBeide waarden zijn verplicht.%s\n" "$COLOR_RED" "$COLOR_RESET"
        choose_delay "$default_min" "$default_max"
        return 0
      fi
      echo "$min_val $max_val"
      return 0
      ;;
    *)
      printf "%sOngeldige keuze, probeer opnieuw.%s\n" "$COLOR_RED" "$COLOR_RESET"
      choose_delay "$default_min" "$default_max"
      ;;
  esac
}

choose_max_parallel() {
  local default_value="$1"
  local choice
  local custom
  printf "\n%sGelijktijdige browsers%s\n" "$STYLE_BOLD" "$COLOR_RESET"
  info_line "1) Eén browser tegelijk (veiligste optie)"
  info_line "2) Twee browsers tegelijk"
  info_line "3) Eigen aantal instellen"
  choice=$(choose_from_menu "Kies optie [1]: " 1)
  case "$choice" in
    1)
      echo "$default_value"
      ;;
    2)
      echo "2"
      ;;
    3)
      printf "%sAantal browsers: %s" "$COLOR_GREEN" "$COLOR_RESET"
      read -r custom
      if [ -n "$custom" ]; then
        echo "$custom"
      else
        echo "$default_value"
      fi
      ;;
    *)
      printf "%sOngeldige keuze. Gebruik standaard.%s\n" "$COLOR_RED" "$COLOR_RESET"
      echo "$default_value"
      ;;
  esac
}

choose_headless() {
  local choice
  printf "\n%sBrowserweergave%s\n" "$STYLE_BOLD" "$COLOR_RESET"
  info_line "1) Toon de browservensters (aanbevolen)"
  info_line "2) Verberg de browser (headless)"
  choice=$(choose_from_menu "Kies optie [1]: " 1)
  case "$choice" in
    2)
      echo "yes"
      ;;
    *)
      echo "no"
      ;;
  esac
}

contains_value() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    if [ "$needle" = "$item" ]; then
      return 0
    fi
  done
  return 1
}

choose_platforms() {
  local raw_selection
  local selected=()
  local token
  local idx
  local option

  printf "\n%sPlatformselectie%s\n" "$STYLE_BOLD" "$COLOR_RESET"
  info_line "Druk Enter voor alle platforms (${DEFAULT_PLATFORMS[*]})"
  for idx in "${!DEFAULT_PLATFORMS[@]}"; do
    option="${DEFAULT_PLATFORMS[$idx]}"
    printf "  %s%d)%s %s\n" "$COLOR_GREEN" $((idx + 1)) "$COLOR_RESET" "$option"
  done
  printf "%sGeef nummers of namen (bv. 1 3 of facebook): %s" "$COLOR_GREEN" "$COLOR_RESET"
  read -r raw_selection

  if [ -z "$raw_selection" ]; then
    printf '%s
' "${DEFAULT_PLATFORMS[*]}"
    return 0
  fi

  raw_selection="$(echo "$raw_selection" | tr ',;' '  ')"
  for token in $raw_selection; do
    if [[ "$token" =~ ^[0-9]+$ ]]; then
      if [ "$token" -ge 1 ] && [ "$token" -le "${#DEFAULT_PLATFORMS[@]}" ]; then
        option="${DEFAULT_PLATFORMS[$((token - 1))]}"
        if ! contains_value "$option" "${selected[@]}"; then
          selected+=("$option")
        fi
      fi
    else
      option="$(printf '%s' "$token" | tr '[:upper:]' '[:lower:]')"
      for idx in "${!DEFAULT_PLATFORMS[@]}"; do
        if [ "$option" = "${DEFAULT_PLATFORMS[$idx]}" ]; then
          if ! contains_value "$option" "${selected[@]}"; then
            selected+=("$option")
          fi
        fi
      done
    fi
  done

  if [ "${#selected[@]}" -eq 0 ]; then
    printf "%sGeen geldige platforms gekozen; gebruik standaard.%s\n" "$COLOR_YELLOW" "$COLOR_RESET"
    printf '%s
' "${DEFAULT_PLATFORMS[*]}"
  else
    printf '%s
' "${selected[*]}"
  fi
}

headline "Crosslister macOS launcher"
info_line "Dit script begeleidt je stap voor stap."
info_line "Alle instellingen zijn later opnieuw te wijzigen."

pause_for_user

step_heading "Bestanden kiezen"
CSV_PATH=$(choose_path "CSV-bestand" "$DEFAULT_CSV")
IMAGES_DIR=$(choose_path "Map met afbeeldingen" "$DEFAULT_IMAGES")
CREDENTIALS_PATH=$(choose_path "Credentials-bestand" "$DEFAULT_CREDENTIALS")
COOKIES_DIR=$(choose_path "Cookies-map" "$DEFAULT_COOKIES")
CATEGORY_MAP_PATH=$(choose_path "Category-map (JSON)" "$DEFAULT_CATEGORY_MAP")

step_heading "Vertraging instellen"
DELAY_VALUES=$(choose_delay "$DEFAULT_DELAY_MIN" "$DEFAULT_DELAY_MAX")
read -r DELAY_MIN DELAY_MAX <<< "$DELAY_VALUES"

step_heading "Gelijktijdige browsers"
MAX_PARALLEL=$(choose_max_parallel "$DEFAULT_MAX_PARALLEL")

step_heading "Browserweergave"
HEADLESS_INPUT=$(choose_headless)

step_heading "Platforms kiezen"
PLATFORM_SELECTION=$(choose_platforms)
IFS=' ' read -r -a TRIMMED_PLATFORMS <<< "$PLATFORM_SELECTION"

# Normalise numeric inputs
number_re='^[0-9]+([.][0-9]+)?$'
if ! [[ $DELAY_MIN =~ $number_re ]]; then
  printf "%sOngeldige minimale vertraging: %s%s\n" "$COLOR_RED" "$DELAY_MIN" "$COLOR_RESET"
  exit 1
fi
if ! [[ $DELAY_MAX =~ $number_re ]]; then
  printf "%sOngeldige maximale vertraging: %s%s\n" "$COLOR_RED" "$DELAY_MAX" "$COLOR_RESET"
  exit 1
fi
if ! [[ $MAX_PARALLEL =~ ^[0-9]+$ ]]; then
  printf "%sOngeldig aantal browsers: %s%s\n" "$COLOR_RED" "$MAX_PARALLEL" "$COLOR_RESET"
  exit 1
fi

# Ensure min <= max without relying on bash 4 `${var,,}` or arithmetic on floats.
if command -v bc >/dev/null 2>&1; then
  if [ "$(echo "$DELAY_MIN > $DELAY_MAX" | bc)" = "1" ]; then
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

CSV_PATH=$(expand_path "$CSV_PATH")
IMAGES_DIR=$(expand_path "$IMAGES_DIR")
CREDENTIALS_PATH=$(expand_path "$CREDENTIALS_PATH")
COOKIES_DIR=$(expand_path "$COOKIES_DIR")
CATEGORY_MAP_PATH=$(expand_path "$CATEGORY_MAP_PATH")

mkdir -p "$COOKIES_DIR"

HEADLESS_FLAG=()
case "$HEADLESS_INPUT" in
  yes|Yes|YES)
    HEADLESS_FLAG=(--headless)
    ;;
  *)
    HEADLESS_FLAG=()
    ;;
esac

step_heading "Samenvatting"
info_line "CSV: $CSV_PATH"
info_line "Afbeeldingen: $IMAGES_DIR"
info_line "Credentials: $CREDENTIALS_PATH"
info_line "Cookies: $COOKIES_DIR"
info_line "Categorieën: $CATEGORY_MAP_PATH"
info_line "Vertraging: ${DELAY_MIN}-${DELAY_MAX} s"
info_line "Browsers tegelijk: $MAX_PARALLEL"
info_line "Headless: ${HEADLESS_INPUT}"
info_line "Platforms: ${TRIMMED_PLATFORMS[*]}"

pause_for_user

step_heading "Automatisering starten"
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

printf "\n%sCommando:%s %s\n\n" "$COLOR_YELLOW" "$COLOR_RESET" "${COMMAND[*]}"
"${COMMAND[@]}"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  printf "%s✅ Crosslister voltooid.%s\n" "$COLOR_GREEN" "$COLOR_RESET"
else
  printf "%s❌ Crosslister eindigde met foutcode %s.%s\n" "$COLOR_RED" "$EXIT_CODE" "$COLOR_RESET"
fi

printf "\n%sResultaten in:%s %s/crosslister_output.json\n" "$COLOR_CYAN" "$COLOR_RESET" "$PROJECT_ROOT"

pause_for_user

