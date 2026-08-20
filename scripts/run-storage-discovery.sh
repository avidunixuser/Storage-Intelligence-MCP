#!/usr/bin/env sh
set -eu

output="${DISCOVERY_OUTPUT_PATH:-data/discovered-storage-accounts.json}"
python -m storage_intelligence.discovery --output "$output"
