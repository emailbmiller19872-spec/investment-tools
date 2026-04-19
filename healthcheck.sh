#!/bin/bash

# Simple wallet-based health check for coinbot container.
# Update MASTER_WALLET_ADDRESS and RPC_URL to match your network.

MASTER_WALLET_ADDRESS="0xYourMasterWalletAddressHere"
MIN_BALANCE_THRESHOLD="0.001"
RPC_URL="https://api.etherscan.io/api?module=account&action=balance&address=${MASTER_WALLET_ADDRESS}&tag=latest"

if ! command -v curl >/dev/null 2>&1 || ! command -v jq >/dev/null 2>&1 || ! command -v bc >/dev/null 2>&1; then
  echo "Required tools missing: curl, jq, bc"
  exit 1
fi

balance_wei=$(curl -s "$RPC_URL" | jq -r '.result')
if [[ "$balance_wei" == "null" || -z "$balance_wei" ]]; then
  echo "Failed to fetch wallet balance"
  exit 1
fi

balance_eth=$(echo "scale=6; $balance_wei / 10^18" | bc)

if (( $(echo "$balance_eth >= $MIN_BALANCE_THRESHOLD" | bc -l) )); then
  echo "Health check passed. Balance: $balance_eth ETH"
  exit 0
else
  echo "Health check failed. Balance: $balance_eth ETH (need $MIN_BALANCE_THRESHOLD)"
  exit 1
fi
