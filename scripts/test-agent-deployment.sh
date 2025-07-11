#!/bin/bash

# Test script for agent deployment with crash detection
# This script deploys the agent and monitors for crashes, failures, and errors

set -e
set -u
set -o pipefail

# Configuration
NAMESPACE="ai-agent-platform"
AGENT_NAME="sales-personalized-email-agent"
TIMEOUT=300  # 5 minutes timeout
CHECK_INTERVAL=10  # Check every 10 seconds

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] INFO${NC} - $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN${NC} - $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR${NC} - $1"
    exit 1
}

check_pod_status() {
    local pod_name=$1
    local status=$(kubectl get pod "$pod_name" -n "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null || echo "NOT_FOUND")
    echo "$status"
}

check_pod_restarts() {
    local pod_name=$1
    local restarts=$(kubectl get pod "$pod_name" -n "$NAMESPACE" -o jsonpath='{.status.containerStatuses[0].restartCount}' 2>/dev/null || echo "0")
    echo "$restarts"
}

check_for_errors() {
    local pod_name=$1
    local error_count=$(kubectl logs "$pod_name" -n "$NAMESPACE" 2>/dev/null | grep -i "error\|exception\|crash\|fail" | wc -l)
    echo "$error_count"
}

check_for_git_error() {
    local pod_name=$1
    local git_error=$(kubectl logs "$pod_name" -n "$NAMESPACE" 2>/dev/null | grep -i "ModuleNotFoundError.*git\|No module named 'git'" | wc -l)
    echo "$git_error"
}

# Load environment variables
if [ -f .env ]; then
    source .env
    log "Loaded environment variables from .env file"
else
    error "Could not find .env file"
fi

log "Starting agent deployment test with crash detection..."

# 1. Clean up any existing deployment
log "Cleaning up any existing deployment..."
kubectl delete aiagentruntime "$AGENT_NAME" -n "$NAMESPACE" --ignore-not-found

# 2. Create deployment YAML
log "Creating deployment YAML..."
cat <<EOF > /tmp/test-agent-runtime.yaml
apiVersion: agentic.keboola.io/v1alpha1
kind: AIAgentRuntime
metadata:
  name: $AGENT_NAME
  namespace: $NAMESPACE
spec:
  entrypoint: "src/sales_personalized_email/main.py"
  codeSource:
    type: git
    gitRepo:
      url: "https://github.com/manana2520/ai-agent-outreach-email"
      branch: "main"
  envVars:
    - name: OPENAI_API_KEY
      value: "${OPENROUTER_API_KEY}"
    - name: OPENAI_API_BASE
      value: "https://openrouter.ai/api/v1"
    - name: OPENROUTER_MODEL
      value: "openai/gpt-4o-mini"
  replicas: 1
EOF

# 3. Deploy the agent
log "Deploying agent..."
kubectl apply -f /tmp/test-agent-runtime.yaml

# 4. Wait for pod to be created
log "Waiting for pod to be created..."
sleep 10

# 5. Get pod name
POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l "app=$AGENT_NAME" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -z "$POD_NAME" ]; then
    error "Failed to get pod name. Deployment may have failed."
fi

log "Monitoring pod: $POD_NAME"

# 6. Monitor deployment with crash detection
start_time=$(date +%s)
last_restart_count=0

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    if [ $elapsed -gt $TIMEOUT ]; then
        error "Timeout reached ($TIMEOUT seconds). Deployment may be stuck."
    fi
    
    # Check pod status
    status=$(check_pod_status "$POD_NAME")
    restarts=$(check_pod_restarts "$POD_NAME")
    error_count=$(check_for_errors "$POD_NAME")
    git_error_count=$(check_for_git_error "$POD_NAME")
    
    log "Status: $status, Restarts: $restarts, Errors: $error_count, Git Errors: $git_error_count"
    
    # Check for crashes
    if [ "$status" = "CrashLoopBackOff" ]; then
        error "CRASH DETECTED: Pod is in CrashLoopBackOff status"
    fi
    
    if [ "$status" = "Error" ]; then
        error "CRASH DETECTED: Pod is in Error status"
    fi
    
    if [ "$status" = "Failed" ]; then
        error "CRASH DETECTED: Pod is in Failed status"
    fi
    
    # Check for restart increase
    if [ "$restarts" -gt "$last_restart_count" ]; then
        warn "RESTART DETECTED: Pod restarted (was $last_restart_count, now $restarts)"
        last_restart_count=$restarts
        
        # Show recent logs after restart
        log "Recent logs after restart:"
        kubectl logs "$POD_NAME" -n "$NAMESPACE" --tail=20
    fi
    
    # Check for git error specifically
    if [ "$git_error_count" -gt 0 ]; then
        error "CRITICAL ERROR DETECTED: Missing git module in runtime"
    fi
    
    # Check for success
    if [ "$status" = "Running" ] && [ "$restarts" -eq 0 ]; then
        log "SUCCESS: Pod is running successfully"
        break
    fi
    
    # Check for completion (if it's a job-style pod)
    if [ "$status" = "Succeeded" ]; then
        log "SUCCESS: Pod completed successfully"
        break
    fi
    
    sleep $CHECK_INTERVAL
done

log "Deployment test completed successfully!"
log "Pod $POD_NAME is running without crashes"

# 7. Test connectivity (optional)
log "Testing agent connectivity..."
if kubectl port-forward pod/"$POD_NAME" -n "$NAMESPACE" 8082:8000 --timeout=5s &>/dev/null; then
    sleep 2
    if curl -f -s http://localhost:8082/health &>/dev/null; then
        log "SUCCESS: Agent is responding to health checks"
    else
        warn "Agent is not responding to health checks yet"
    fi
    pkill -f "kubectl port-forward.*$POD_NAME" || true
else
    warn "Could not establish port-forward (agent may still be starting)"
fi

log "Test completed. Agent deployment is working correctly." 