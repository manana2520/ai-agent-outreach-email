#!/bin/bash

# Monitor agent for specific crash patterns
# This script waits for the agent to finish dependency installation and then checks for crashes

set -e
set -u

NAMESPACE="ai-agent-platform"
AGENT_NAME="sales-personalized-email-agent"
TIMEOUT=600  # 10 minutes
CHECK_INTERVAL=15

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] INFO${NC} - $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN${NC} - $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR${NC} - $1"
}

# Get pod name
POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l "app=$AGENT_NAME" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -z "$POD_NAME" ]; then
    error "No pod found for agent $AGENT_NAME"
    exit 1
fi

log "Monitoring pod: $POD_NAME"

start_time=$(date +%s)
last_log_line=""

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    if [ $elapsed -gt $TIMEOUT ]; then
        error "Timeout reached ($TIMEOUT seconds)"
        break
    fi
    
    # Get current status
    status=$(kubectl get pod "$POD_NAME" -n "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null || echo "NOT_FOUND")
    restarts=$(kubectl get pod "$POD_NAME" -n "$NAMESPACE" -o jsonpath='{.status.containerStatuses[0].restartCount}' 2>/dev/null || echo "0")
    
    log "Status: $status, Restarts: $restarts, Elapsed: ${elapsed}s"
    
    # Check for crashes
    if [ "$status" = "CrashLoopBackOff" ] || [ "$status" = "Error" ] || [ "$status" = "Failed" ]; then
        error "CRASH DETECTED: Pod status is $status"
        log "Full logs:"
        kubectl logs "$POD_NAME" -n "$NAMESPACE"
        break
    fi
    
    # Check for git error in logs
    git_error=$(kubectl logs "$POD_NAME" -n "$NAMESPACE" 2>/dev/null | grep -i "ModuleNotFoundError.*git\|No module named 'git'" | tail -1)
    if [ -n "$git_error" ]; then
        error "GIT ERROR DETECTED: $git_error"
        log "Full logs:"
        kubectl logs "$POD_NAME" -n "$NAMESPACE"
        break
    fi
    
    # Check for dependency installation completion
    deps_complete=$(kubectl logs "$POD_NAME" -n "$NAMESPACE" 2>/dev/null | grep -i "Dependencies installed\|Installed.*packages" | tail -1)
    if [ -n "$deps_complete" ]; then
        log "Dependencies installed: $deps_complete"
        
        # Wait a bit more to see if it crashes after dependency installation
        sleep 10
        
        # Check for runtime startup
        runtime_start=$(kubectl logs "$POD_NAME" -n "$NAMESPACE" 2>/dev/null | grep -i "Starting Runtime API Server\|Running command.*uvicorn" | tail -1)
        if [ -n "$runtime_start" ]; then
            log "Runtime starting: $runtime_start"
            
            # Wait a bit more for potential crash
            sleep 15
            
            # Check for success or crash
            if kubectl logs "$POD_NAME" -n "$NAMESPACE" 2>/dev/null | grep -q "ModuleNotFoundError.*git"; then
                error "CRASH CONFIRMED: Git module error after runtime start"
                log "Full logs:"
                kubectl logs "$POD_NAME" -n "$NAMESPACE"
                break
            else
                log "SUCCESS: Runtime started without git errors"
                break
            fi
        fi
    fi
    
    # Check for new log lines
    current_log_line=$(kubectl logs "$POD_NAME" -n "$NAMESPACE" 2>/dev/null | tail -1)
    if [ "$current_log_line" != "$last_log_line" ] && [ -n "$current_log_line" ]; then
        log "Latest log: $current_log_line"
        last_log_line="$current_log_line"
    fi
    
    sleep $CHECK_INTERVAL
done

log "Monitoring completed" 