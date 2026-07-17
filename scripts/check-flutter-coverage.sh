#!/bin/sh
set -eu

LCOV_FILE=${1:-mobile/coverage/lcov.info}
MINIMUM_PERCENT=${2:-75}

if [ ! -f "$LCOV_FILE" ]; then
  printf 'Flutter coverage report not found: %s\n' "$LCOV_FILE" >&2
  exit 1
fi

awk -F: -v minimum="$MINIMUM_PERCENT" '
  /^LF:/ { found += $2 }
  /^LH:/ { hit += $2 }
  END {
    if (found <= 0) {
      print "Flutter coverage report contains no executable lines." > "/dev/stderr"
      exit 2
    }

    percent = (100 * hit) / found
    printf "Flutter line coverage: %d/%d (%.2f%%); required: %.2f%%\n", \
      hit, found, percent, minimum

    if (percent + 0.000001 < minimum) {
      print "Flutter coverage gate failed." > "/dev/stderr"
      exit 3
    }
  }
' "$LCOV_FILE"
