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

# 7. Check for and Kill Existing Process on Agent Port, then Start Agent Port Forward
log "Checking if agent port $AGENT_PORT is already in use..."
# Use lsof to find listener on the specific port. -t gives just PID.
# Redirect stderr to /dev/null to avoid errors if port is free.
listening_pid=$(lsof -t -i :$AGENT_PORT -sTCP:LISTEN 2>/dev/null || true)

if [[ -n "$listening_pid" ]]; then
  # Handle potential multiple PIDs/lines from lsof output by taking the first one
  pid_to_kill=$(echo "$listening_pid" | head -n 1)
  log "WARN: Port $AGENT_PORT is currently in use by PID $pid_to_kill. Attempting to terminate..."
  if kill "$pid_to_kill"; then
    log "Sent SIGTERM to PID $pid_to_kill. Waiting 2s..."
    sleep 2
    # Re-check if port is free after SIGTERM
    if lsof -t -i :$AGENT_PORT -sTCP:LISTEN > /dev/null 2>&1; then
       log "WARN: Port $AGENT_PORT still in use after SIGTERM (PID $pid_to_kill). Trying SIGKILL..."
       if kill -9 "$pid_to_kill"; then
           log "Sent SIGKILL to PID $pid_to_kill. Waiting 2s..."
           sleep 2
       else
           log "ERROR: Failed to send SIGKILL to PID $pid_to_kill."
           # Depending on requirements, you might want to error out here:
           # error "Failed to free port $AGENT_PORT occupied by PID $pid_to_kill."
           log "WARN: Could not ensure port $AGENT_PORT is free. Proceeding, but port-forward might fail."
       fi
    else
       log "Port $AGENT_PORT successfully freed after SIGTERM."
    fi
  else
    log "WARN: Failed to send SIGTERM to PID $pid_to_kill. Process might be gone or require sudo."
    # Proceeding, hoping the port-forward will either work or fail clearly later.
  fi
else
  log "Port $AGENT_PORT appears to be free."
fi

# Start Agent Port Forward in Background
log "Starting port-forward for Agent Service ($AGENT_SERVICE) on port $AGENT_PORT..."
kubectl port-forward "service/$AGENT_SERVICE" -n "$NAMESPACE" "$AGENT_PORT:80" &
AGENT_FWD_PID=$!
sleep 2 # Give it a second to start
if ! ps -p $AGENT_FWD_PID > /dev/null; then
   error "Failed to start port-forward for Agent Service."
fi
log "Agent service port-forward started in background (PID: $AGENT_FWD_PID)."
