#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Prevent errors in a pipeline from being masked.
set -o pipefail

# --- Configuration ---
NAMESPACE="ai-platform"
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

# Agent input data (adjust as needed)
AGENT_INPUT_JSON=$(cat <<EOF
{
  "crew": "sales_personalized_email",
  "inputs": {
    "name": "Joe Eyles",
    "title": "Vice Principal",
    "company": "Park Lane International School",
    "industry": "Education",
    "linkedin_url": "https://www.linkedin.com/in/joe-eyles-93b66b265",
    "our_product": "AI and DAta Platform for Education"
  }
}
EOF
)

# Timeouts (in seconds)
POD_TIMEOUT=120
RUN_TIMEOUT=300

# Variable to store the dynamically generated pod name
AGENT_POD_NAME=""

# --- Functions ---
log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO - $1"
}

error() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR - $1" >&2
  exit 1
}

# Load environment variables from .env file
if [ -f .env ]; then
  source .env
  log "Loaded environment variables from .env file"
else
  error "Could not find .env file"
fi

check_cluster_ready() {
  local max_retries=5
  local attempt=1
  local cluster_ready=false
  log "Checking Kubernetes cluster connection..."

  while [[ $attempt -le $max_retries ]]; do
    # Try connecting, capture stderr on failure
    if kubectl cluster-info > /dev/null 2> /tmp/kubectl_error.log; then
      cluster_ready=true
      break # Success
    fi

    # Check stderr content for connection refused error
    if grep -q -E 'connection refused|Unable to connect|refused.*did you specify the right host or port' /tmp/kubectl_error.log; then
      log "kubectl check failed. Cluster seems unavailable (connection refused). Attempt $attempt/$max_retries."
      echo "-------------------------------------------------------------------"
      echo "Please ensure your Kubernetes cluster is running."
      read -t 30 -r -p "Select platform to attempt start: (d)ocker, (r)ancher, (m)anual start? [m] " platform_choice
      platform_choice=${platform_choice:-m} # Default to manual

      case "$platform_choice" in
        d|D|r|R)
          app_name="Docker"
          if [[ "$platform_choice" == "r" || "$platform_choice" == "R" ]]; then
            app_name="Rancher Desktop"
          fi

          log "Attempting to start $app_name via 'open -a \"$app_name\"'..."
          if ! open -a "$app_name"; then
            log "WARN: Failed to execute 'open -a \"$app_name\"'. Please start it manually and press Enter when ready."
            # Fallback to manual wait
            if read -t 300 -p "Press Enter when the cluster is ready to retry, or wait 5 minutes... "; then
                log "Retrying cluster connection..."
            else
                log "Timeout waiting for user input."
            fi
          else
            log "INFO: Please monitor $app_name application for startup progress."
            log "INFO: Now polling cluster status for up to 5 minutes..."
            local poll_start_time=$(date +%s)
            local poll_timeout=300 # 5 minutes
            local poll_cluster_ready=false
            while true; do
                log "Polling cluster status..."
                if kubectl cluster-info > /dev/null 2> /tmp/kubectl_poll_error.log; then
                   log "Cluster became ready after starting $app_name."
                   poll_cluster_ready=true
                   cluster_ready=true # Set outer loop flag
                   break # Exit inner poll loop
                fi

                # Check error during polling
                if grep -q -E 'connection refused|Unable to connect|refused.*did you specify the right host or port' /tmp/kubectl_poll_error.log; then
                   log "Cluster still not ready (connection refused). Waiting 10s..."
                else
                    log "kubectl poll failed with an unexpected error:"
                    cat /tmp/kubectl_poll_error.log >&2
                    rm -f /tmp/kubectl_poll_error.log
                    # Exit entire script on unexpected error during polling
                    error "Aborting due to unexpected kubectl error while polling after app start."
                fi

                local current_time=$(date +%s)
                local elapsed_time=$((current_time - poll_start_time))
                if [[ $elapsed_time -ge $poll_timeout ]]; then
                    log "WARN: Timeout reached. Cluster did not become ready within $poll_timeout seconds after attempting to start $app_name."
                    break # Exit inner poll loop, outer loop will retry
                fi
                sleep 10
            done
            rm -f /tmp/kubectl_poll_error.log # Clean up poll error log
            # If inner loop finished and cluster is ready, break outer loop too
            if [[ "$poll_cluster_ready" == "true" ]]; then
                break
            fi
          fi
          ;;
        *)
          log "Proceeding with manual start. Please start your K8s cluster."
          # Use timeout for read in case script is run non-interactively later
          if read -t 300 -p "Press Enter when the cluster is ready to retry, or wait 5 minutes... "; then
              log "Retrying cluster connection..."
          else
              log "Timeout waiting for user input."
              # Optionally break or exit here if non-interactive timeout is critical
          fi
          ;;
      esac
    else
      # Different kubectl error
      log "kubectl check failed with an unexpected error:"
      cat /tmp/kubectl_error.log >&2
      rm -f /tmp/kubectl_error.log
      error "Aborting due to unexpected kubectl error."
    fi
    # If cluster became ready in the inner loop, this ensures outer loop exits
    if [[ "$cluster_ready" == "true" ]]; then
        break
    fi
    ((attempt++))
  done

  rm -f /tmp/kubectl_error.log # Clean up temp file

  if [[ "$cluster_ready" == "false" ]]; then
      error "Maximum retries reached or failed to connect. Please ensure your Kubernetes cluster is running and accessible."
  fi

  log "Kubernetes cluster connection successful."
}

cleanup() {
  log "Cleaning up background port-forward processes..."
  pkill -f "kubectl port-forward service/$PLATFORM_API_SERVICE -n $NAMESPACE $PLATFORM_PORT:80" || true
  pkill -f "kubectl port-forward service/$AGENT_SERVICE -n $NAMESPACE $AGENT_PORT:80" || true
  log "Cleanup complete."
}

# --- Main Script ---

# Set up trap to ensure cleanup runs on exit
trap cleanup EXIT

log "Starting AI Agent deployment and kickoff script..."

# Check K8s cluster readiness first
check_cluster_ready

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

# 3. Delete Existing Agent Runtime (ignore errors if not found)
log "Deleting existing AIAgentRuntime: $AGENT_NAME..."
kubectl delete aiagentruntime "$AGENT_NAME" -n "$NAMESPACE" --ignore-not-found

# --- PAUSE ADDED ---
#read -p "Existing runtime deleted (if any). Press Enter to continue creating the new runtime..."
# --- END PAUSE ---

# 4. Create Agent Runtime YAML
log "Creating agent runtime YAML at $YAML_PATH..."
cat <<EOF > "$YAML_PATH"
apiVersion: agentic.keboola.io/v1alpha1
kind: AIAgentRuntime
metadata:
  name: $AGENT_NAME
  namespace: $NAMESPACE
spec:
  entrypoint: "$AGENT_ENTRYPOINT"
  codeSource:
    type: git
    gitRepo:
      url: "$GITHUB_URL"
      branch: "$GITHUB_BRANCH"
  envVars:
    - name: OPENAI_API_KEY
      value: "${OPENROUTER_API_KEY}"
    - name: OPENAI_API_BASE
      value: "https://openrouter.ai/api/v1"
    - name: OPENROUTER_MODEL
      value: "openai/gpt-4o-mini"
  replicas: 1
EOF
log "YAML file created."

# 5. Deploy Agent Runtime
log "Applying agent runtime YAML..."
if ! kubectl apply -f "$YAML_PATH"; then
  error "Failed to apply agent runtime YAML."
fi
log "Agent runtime deployment initiated."

# 6. Wait for Agent Pod to be Running
log "Waiting for agent pod ($AGENT_NAME) to be running (Timeout: ${POD_TIMEOUT}s)..."
start_time=$(date +%s)
while true; do
  # Attempt to get the name of the latest pod for the agent
  # Using sort-by creationTimestamp and taking the last one (.items[-1]) might be slightly more robust if old pods linger
  # However, filtering by status.phase=Running or Pending is usually sufficient if cleanup works well.
  # Sticking to the original logic for now, but capturing the name.
  pod_name=$(kubectl get pods -n "$NAMESPACE" -l "app=$AGENT_NAME" -o jsonpath='{.items[?(@.status.phase=="Running")].metadata.name}' 2>/dev/null || \
             kubectl get pods -n "$NAMESPACE" -l "app=$AGENT_NAME" -o jsonpath='{.items[?(@.status.phase=="Pending")].metadata.name}' 2>/dev/null || \
             kubectl get pods -n "$NAMESPACE" -l "app=$AGENT_NAME" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true) # Fallback to first item if no running/pending

  if [[ -n "$pod_name" ]]; then
      # If multiple pods match (e.g., during rollout), pick the first one listed
      # A more robust way might involve sorting by creation time, but this often works.
      AGENT_POD_NAME=$(echo "$pod_name" | awk '{print $1}') # Ensure we only get one name if multiple are returned
      pod_status=$(kubectl get pod "$AGENT_POD_NAME" -n "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
      log "Pod '$AGENT_POD_NAME' status: $pod_status"
      if [[ "$pod_status" == "Running" ]]; then
        log "Agent pod is running ($AGENT_POD_NAME)."
        break
      elif [[ "$pod_status" == "Failed" || "$pod_status" == "Error" || "$pod_status" == "CrashLoopBackOff" ]]; then
        # Fetch logs immediately if pod fails to start
        log "Agent pod $AGENT_POD_NAME entered failed state: $pod_status"
        echo "---BEGIN POD LOGS ($AGENT_POD_NAME)---"
        kubectl logs "$AGENT_POD_NAME" -n "$NAMESPACE" --tail=100 | cat || echo "<< ---ERROR GETTING POD LOGS--- >>"
        echo "---END POD LOGS ($AGENT_POD_NAME)---"
        error "Agent pod failed to start."
      fi
  else
      log "Agent pod not found yet..."
  fi

  current_time=$(date +%s)
  elapsed_time=$((current_time - start_time))
  if [[ $elapsed_time -ge $POD_TIMEOUT ]]; then
    error "Timeout waiting for agent pod to become Running."
  fi
  sleep 5
done

# Add a delay to allow the service to be created/registered AND the app inside the pod to start listening
log "Agent pod is running. Waiting 30s for service and internal app to stabilize..."
sleep 30

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

# Allow some time for the service/proxy to be ready
log "Waiting a few seconds for agent port-forward proxy to stabilize..."
sleep 5

# 8. Kick Off Agent Run
log "Kicking off agent run..."
kickoff_response=$(curl -s -X POST "http://localhost:$AGENT_PORT/kickoff" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AGENT_API_TOKEN" \
  -d "$AGENT_INPUT_JSON")

if ! echo "$kickoff_response" | jq -e .run_id > /dev/null; then
  error "Failed to kick off agent run or parse run_id. Response: $kickoff_response"
fi
RUN_ID=$(echo "$kickoff_response" | jq -r .run_id)
log "Agent run kicked off successfully. Run ID: $RUN_ID"

# 9. Wait for Agent Run Completion
log "Waiting for agent run $RUN_ID to complete (Timeout: ${RUN_TIMEOUT}s)..."
start_time=$(date +%s)
while true; do
  run_status_response=$(curl -s -X GET "http://localhost:$AGENT_PORT/runs/$RUN_ID" -H "Authorization: Bearer $AGENT_API_TOKEN")
  run_status=$(echo "$run_status_response" | jq -r .status)

  log "Run $RUN_ID status: $run_status"

  if [[ "$run_status" == "completed" ]]; then
    log "Agent run completed successfully."
    break
  elif [[ "$run_status" == "error" ]]; then
    log "Agent run failed with status 'error'. Response: $run_status_response"
    # --- BEGIN ADDED LOG FETCH ---
    if [[ -n "${AGENT_POD_NAME:-}" ]]; then
        log "Attempting to fetch logs from failed pod: $AGENT_POD_NAME..."
        echo "---BEGIN POD LOGS ($AGENT_POD_NAME)---"
        # Fetch last 100 lines of logs from the pod
        kubectl logs "$AGENT_POD_NAME" -n "$NAMESPACE" --tail=100 | cat || echo "<< ---ERROR GETTING POD LOGS--- >>"
        echo "---END POD LOGS ($AGENT_POD_NAME)---"
    else
        log "WARN: Agent pod name was not captured, cannot fetch logs."
    fi
    # --- END ADDED LOG FETCH ---
    error "Agent run failed."
  elif [[ "$run_status" == "null" || -z "$run_status" ]]; then
     # Fetch logs if status is invalid/null
     log "Could not retrieve valid status for run $RUN_ID. Response: $run_status_response"
     # --- BEGIN ADDED LOG FETCH ---
     if [[ -n "${AGENT_POD_NAME:-}" ]]; then
         log "Attempting to fetch logs from pod with invalid run status: $AGENT_POD_NAME..."
         echo "---BEGIN POD LOGS ($AGENT_POD_NAME)---"
         kubectl logs "$AGENT_POD_NAME" -n "$NAMESPACE" --tail=100 | cat || echo "<< ---ERROR GETTING POD LOGS--- >>"
         echo "---END POD LOGS ($AGENT_POD_NAME)---"
     else
         log "WARN: Agent pod name was not captured, cannot fetch logs."
     fi
     # --- END ADDED LOG FETCH ---
     error "Could not retrieve valid status for run $RUN_ID."
  fi

  current_time=$(date +%s)
  elapsed_time=$((current_time - start_time))
  if [[ $elapsed_time -ge $RUN_TIMEOUT ]]; then
    log "Timeout waiting for agent run $RUN_ID to complete."
    # --- BEGIN ADDED LOG FETCH ---
    if [[ -n "${AGENT_POD_NAME:-}" ]]; then
        log "Attempting to fetch logs from timed-out pod: $AGENT_POD_NAME..."
        echo "---BEGIN POD LOGS ($AGENT_POD_NAME)---"
        # Fetch last 100 lines of logs from the pod
        kubectl logs "$AGENT_POD_NAME" -n "$NAMESPACE" --tail=100 | cat || echo "<< ---ERROR GETTING POD LOGS--- >>"
        echo "---END POD LOGS ($AGENT_POD_NAME)---"
    else
        log "WARN: Agent pod name was not captured, cannot fetch logs on timeout."
    fi
    # --- END ADDED LOG FETCH ---
    error "Timeout waiting for agent run $RUN_ID."
  fi
  sleep 5
done

# --- ADDED: Fetch and display final run details (including result) ---
log "Fetching final run details for $RUN_ID..."
final_run_details=$(curl -s -X GET "http://localhost:$AGENT_PORT/runs/$RUN_ID" -H "Authorization: Bearer $AGENT_API_TOKEN")

log "Final Run Details (including result):"
echo "---BEGIN FINAL RUN DETAILS--- >>"
echo "$final_run_details" | jq . # Use jq for pretty printing if available, otherwise raw JSON
echo "<< ---END FINAL RUN DETAILS--- >>"

log "Script completed successfully!"

# The trap will handle cleanup on exit

exit 0 