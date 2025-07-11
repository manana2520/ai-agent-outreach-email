#!/bin/bash

# Comprehensive agent deployment test with failure detection
# This script tests for all types of failures: network, crashes, runtime errors, etc.

set -e
set -u
set -o pipefail

# Configuration
NAMESPACE="ai-agent-platform"
AGENT_NAME="sales-personalized-email-agent"
TIMEOUT=900  # 15 minutes timeout
CHECK_INTERVAL=10

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO${NC} - $1"
}

# Test functions
check_network_connectivity() {
    log "Testing network connectivity to Docker Hub..."
    if curl -f -s --connect-timeout 10 "https://registry-1.docker.io/v2/" >/dev/null; then
        log "Network connectivity to Docker Hub: OK"
        return 0
    else
        error "Network connectivity to Docker Hub: FAILED"
        return 1
    fi
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

check_pod_conditions() {
    local pod_name=$1
    kubectl get pod "$pod_name" -n "$NAMESPACE" -o jsonpath='{.status.conditions[*].type}:{.status.conditions[*].status}' 2>/dev/null || echo "UNKNOWN"
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

check_for_network_error() {
    local pod_name=$1
    local network_error=$(kubectl describe pod "$pod_name" -n "$NAMESPACE" 2>/dev/null | grep -i "ImagePullBackOff\|ErrImagePull\|network\|dns" | wc -l)
    echo "$network_error"
}

# Load environment variables
if [ -f .env ]; then
    source .env
    log "Loaded environment variables from .env file"
else
    error "Could not find .env file"
fi

log "Starting comprehensive agent deployment test..."

# 1. Pre-flight checks
info "=== PRE-FLIGHT CHECKS ==="
check_network_connectivity

# Check if Kubernetes is accessible
if ! kubectl cluster-info >/dev/null 2>&1; then
    error "Kubernetes cluster is not accessible"
fi
log "Kubernetes cluster: OK"

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
    error "Namespace $NAMESPACE does not exist"
fi
log "Namespace $NAMESPACE: OK"

# 2. Clean up any existing deployment
info "=== CLEANUP ==="
log "Cleaning up any existing deployment..."
kubectl delete aiagentruntime "$AGENT_NAME" -n "$NAMESPACE" --ignore-not-found
sleep 5

# 3. Create deployment YAML
info "=== DEPLOYMENT ==="
log "Creating deployment YAML..."
cat <<EOF > /tmp/comprehensive-test-runtime.yaml
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

# 4. Deploy the agent
log "Deploying agent..."
kubectl apply -f /tmp/comprehensive-test-runtime.yaml

# 5. Wait for pod to be created
log "Waiting for pod to be created..."
sleep 15

# 6. Get pod name
POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l "app=$AGENT_NAME" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -z "$POD_NAME" ]; then
    error "Failed to get pod name. Deployment may have failed."
fi

log "Monitoring pod: $POD_NAME"

# 7. Comprehensive monitoring
info "=== MONITORING ==="
start_time=$(date +%s)
last_restart_count=0
last_status=""

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    if [ $elapsed -gt $TIMEOUT ]; then
        error "Timeout reached ($TIMEOUT seconds). Deployment may be stuck."
    fi
    
    # Get comprehensive status
    status=$(check_pod_status "$POD_NAME")
    restarts=$(check_pod_restarts "$POD_NAME")
    conditions=$(check_pod_conditions "$POD_NAME")
    error_count=$(check_for_errors "$POD_NAME")
    git_error_count=$(check_for_git_error "$POD_NAME")
    network_error_count=$(check_for_network_error "$POD_NAME")
    
    # Only log if status changed
    if [ "$status" != "$last_status" ]; then
        log "Status: $status, Restarts: $restarts, Elapsed: ${elapsed}s"
        log "Conditions: $conditions"
        log "Errors: $error_count, Git Errors: $git_error_count, Network Errors: $network_error_count"
        last_status="$status"
    fi
    
    # Check for network/image pull failures
    if [ "$network_error_count" -gt 0 ]; then
        error "NETWORK ERROR DETECTED: Image pull failure"
        log "Pod details:"
        kubectl describe pod "$POD_NAME" -n "$NAMESPACE"
        break
    fi
    
    # Check for crashes
    if [ "$status" = "CrashLoopBackOff" ] || [ "$status" = "Error" ] || [ "$status" = "Failed" ]; then
        error "CRASH DETECTED: Pod status is $status"
        log "Full logs:"
        kubectl logs "$POD_NAME" -n "$NAMESPACE"
        break
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
        log "Full logs:"
        kubectl logs "$POD_NAME" -n "$NAMESPACE"
        break
    fi
    
    # Check for success
    if [ "$status" = "Running" ] && [ "$restarts" -eq 0 ]; then
        # Wait a bit more to ensure it's stable
        sleep 30
        
        # Check if it's still running
        final_status=$(check_pod_status "$POD_NAME")
        if [ "$final_status" = "Running" ]; then
            log "SUCCESS: Pod is running stably"
            break
        else
            warn "Pod status changed to $final_status after success check"
        fi
    fi
    
    # Check for completion (if it's a job-style pod)
    if [ "$status" = "Succeeded" ]; then
        log "SUCCESS: Pod completed successfully"
        break
    fi
    
    sleep $CHECK_INTERVAL
done

# 8. Final status check
info "=== FINAL STATUS ==="
final_status=$(check_pod_status "$POD_NAME")
final_restarts=$(check_pod_restarts "$POD_NAME")
final_errors=$(check_for_errors "$POD_NAME")

log "Final Status: $final_status"
log "Final Restarts: $final_restarts"
log "Final Error Count: $final_errors"

if [ "$final_status" = "Running" ] && [ "$final_restarts" -eq 0 ]; then
    log "✅ DEPLOYMENT SUCCESSFUL: Agent is running without issues"
    
    # Test connectivity
    info "=== CONNECTIVITY TEST ==="
    log "Testing agent connectivity..."
    if kubectl port-forward pod/"$POD_NAME" -n "$NAMESPACE" 8082:8000 --timeout=10s &>/dev/null; then
        sleep 3
        if curl -f -s http://localhost:8082/health &>/dev/null; then
            log "✅ SUCCESS: Agent is responding to health checks"
        else
            warn "⚠️  Agent is not responding to health checks yet"
        fi
        pkill -f "kubectl port-forward.*$POD_NAME" || true
    else
        warn "⚠️  Could not establish port-forward (agent may still be starting)"
    fi
else
    error "❌ DEPLOYMENT FAILED: Final status is $final_status with $final_restarts restarts"
fi

log "Comprehensive test completed." 