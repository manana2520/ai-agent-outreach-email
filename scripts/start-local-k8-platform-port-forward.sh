#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Prevent errors in a pipeline from being masked.
set -o pipefail

# --- Configuration ---
NAMESPACE="ai-agent-platform"
AGENT_NAME="sales-personalized-email-agent"
PLATFORM_API_SERVICE="ai-agent-platform-management-api"
AGENT_SERVICE="$AGENT_NAME" # Assuming service name matches agent name
PLATFORM_PORT=8000
AGENT_PORT=8082
YAML_PATH="/tmp/sales-agent-runtime.yaml"
GITHUB_URL="https://github.com/manana2520/ai-agent-outreach-email"
GITHUB_BRANCH="main"
AGENT_ENTRYPOINT="src/sales_personalized_email/main.py"
# Using environment variable from .env file
log() { echo "[INFO] $*"; }
error() { echo "[ERROR] $*" >&2; exit 1; }

# Attempt initial cleanup in case of previous unclean exits
log "Attempting preliminary cleanup of potential lingering port-forwards..."
pkill -f "kubectl port-forward service/$PLATFORM_API_SERVICE -n $NAMESPACE $PLATFORM_PORT:80" || true
pkill -f "kubectl port-forward service/$AGENT_SERVICE -n $NAMESPACE $AGENT_PORT:80" || true
# Give pkill a moment to clean up before the check
sleep 1

# 1. Check if Platform API is already healthy and accessible
log "Checking if Platform API is already accessible via http://localhost:$PLATFORM_PORT/health..."
if curl -f -s --connect-timeout 5 "http://localhost:$PLATFORM_PORT/health"; then
  log "Health check successful. Assuming existing port-forward for Platform API is running."
  # We skip starting a new port-forward process as it seems one is active.
else
  health_check_exit_code=$?
  log "Health check failed (curl exit code: $health_check_exit_code). Attempting to start port-forward for Platform API..."

  # 2. Start Platform Port Forward in Background
  log "Starting port-forward for Platform API ($PLATFORM_API_SERVICE) on port $PLATFORM_PORT..."
  kubectl port-forward "service/$PLATFORM_API_SERVICE" -n "$NAMESPACE" "$PLATFORM_PORT:80" &
  PLATFORM_FWD_PID=$!
  # Give it a second to start up or fail
  sleep 2
  # Check if the process is still running
  if ! ps -p $PLATFORM_FWD_PID > /dev/null; then
     # If the port-forward failed, it might be because the port is *still* in use
     # by something other than the expected service, despite the initial pkill.
     error "Failed to start port-forward for Platform API. The port might still be in use."
  fi
  log "Platform API port-forward started in background (PID: $PLATFORM_FWD_PID)."
fi
