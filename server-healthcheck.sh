#!/bin/sh
set -e

MASTER_WALLET_ADDRESS="${MASTER_WALLET_ADDRESS:-0xYourMasterWalletAddressHere}"
MIN_BALANCE_THRESHOLD="${MIN_BALANCE_THRESHOLD:-0.001}"
RPC_URL="${RPC_URL:-https://api.etherscan.io/api?module=account&action=balance&address=${MASTER_WALLET_ADDRESS}&tag=latest}"

if ! command -v curl >/dev/null 2>&1 || ! command -v jq >/dev/null 2>&1 || ! command -v bc >/dev/null 2>&1; then
  echo "Missing dependency: curl, jq, or bc"
  exit 1
fi

balance_wei=$(curl -s "$RPC_URL" | jq -r '.result')
if [ -z "$balance_wei" ] || [ "$balance_wei" = "null" ]; then
  echo "Unable to fetch balance"
  exit 1
fi

balance_eth=$(echo "scale=6; $balance_wei / 10^18" | bc)
if [ "$(echo "$balance_eth >= $MIN_BALANCE_THRESHOLD" | bc -l)" -eq 1 ]; then
  echo "Health check passed: $balance_eth ETH"
  exit 0
fi

echo "Health check failed: $balance_eth ETH (< $MIN_BALANCE_THRESHOLD)"
exit 1
