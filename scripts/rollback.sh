#!/bin/bash

# Automated rollback script for PantryPal deployments
# This script can rollback to a previous CloudFormation stack version

set -e

STACK_NAME="ppal"
REGION="us-east-1"
DRY_RUN=false
FORCE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -s, --stack-name NAME    Stack name (default: ppal)"
    echo "  -r, --region REGION      AWS region (default: us-east-1)"
    echo "  -d, --dry-run           Show what would be done without executing"
    echo "  -f, --force             Force rollback without confirmation"
    echo "  -h, --help              Show this help message"
    exit 1
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed or not in PATH"
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or invalid"
        exit 1
    fi
}

get_stack_events() {
    local limit=${1:-10}
    aws cloudformation describe-stack-events \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --max-items "$limit" \
        --query 'StackEvents[?ResourceType==`AWS::CloudFormation::Stack`].[Timestamp,ResourceStatus,ResourceStatusReason]' \
        --output table
}

get_previous_template() {
    log_info "Getting previous stack template..."
    
    # Get the current template
    aws cloudformation get-template \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --template-stage Processed \
        --query 'TemplateBody' \
        --output json > current_template.json
    
    if [ $? -eq 0 ]; then
        log_info "Current template saved to current_template.json"
        return 0
    else
        log_error "Failed to get current template"
        return 1
    fi
}

check_stack_status() {
    local status
    status=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null)
    
    echo "$status"
}

cancel_update() {
    log_info "Attempting to cancel current stack update..."
    
    aws cloudformation cancel-update-stack \
        --stack-name "$STACK_NAME" \
        --region "$REGION"
    
    if [ $? -eq 0 ]; then
        log_info "Stack update cancellation initiated"
        
        # Wait for cancellation to complete
        log_info "Waiting for update cancellation to complete..."
        aws cloudformation wait stack-update-complete \
            --stack-name "$STACK_NAME" \
            --region "$REGION"
        
        local final_status
        final_status=$(check_stack_status)
        
        if [[ "$final_status" == "UPDATE_ROLLBACK_COMPLETE" ]]; then
            log_info "Stack successfully rolled back to previous version"
            return 0
        else
            log_warn "Stack is in status: $final_status"
            return 1
        fi
    else
        log_error "Failed to cancel stack update"
        return 1
    fi
}

perform_rollback() {
    local stack_status
    stack_status=$(check_stack_status)
    
    log_info "Current stack status: $stack_status"
    
    case "$stack_status" in
        "UPDATE_IN_PROGRESS")
            log_info "Stack update in progress. Attempting to cancel and rollback..."
            cancel_update
            ;;
        "UPDATE_COMPLETE")
            log_warn "Stack is in UPDATE_COMPLETE state."
            log_warn "CloudFormation doesn't support automatic rollback from this state."
            log_info "You may need to manually deploy a previous version."
            
            # Show recent stack events
            log_info "Recent stack events:"
            get_stack_events 5
            
            return 1
            ;;
        "UPDATE_FAILED"|"UPDATE_ROLLBACK_FAILED")
            log_info "Stack is in a failed state. Attempting to continue rollback..."
            
            aws cloudformation continue-update-rollback \
                --stack-name "$STACK_NAME" \
                --region "$REGION"
            
            if [ $? -eq 0 ]; then
                log_info "Rollback continuation initiated"
                
                # Wait for rollback to complete
                log_info "Waiting for rollback to complete..."
                aws cloudformation wait stack-update-complete \
                    --stack-name "$STACK_NAME" \
                    --region "$REGION"
                
                log_info "Rollback completed"
            else
                log_error "Failed to continue rollback"
                return 1
            fi
            ;;
        "UPDATE_ROLLBACK_IN_PROGRESS")
            log_info "Rollback already in progress. Waiting for completion..."
            aws cloudformation wait stack-update-complete \
                --stack-name "$STACK_NAME" \
                --region "$REGION"
            ;;
        *)
            log_error "Unexpected stack status: $stack_status"
            log_error "Manual intervention may be required"
            return 1
            ;;
    esac
}

run_health_check() {
    log_info "Running post-rollback health check..."
    
    # Get API endpoint from stack outputs
    local api_endpoint
    api_endpoint=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
        --output text 2>/dev/null)
    
    if [ -z "$api_endpoint" ]; then
        api_endpoint="https://bo1uqpm579.execute-api.us-east-1.amazonaws.com/Prod"
        log_warn "Could not get API endpoint from stack, using default: $api_endpoint"
    fi
    
    # Run health check if script exists
    if [ -f "api/health_check.py" ]; then
        python api/health_check.py --url "$api_endpoint" --timeout 30
        if [ $? -eq 0 ]; then
            log_info "Health check passed"
        else
            log_warn "Health check failed, but rollback was successful"
        fi
    else
        # Simple curl test
        if curl -f "$api_endpoint/" --max-time 30 > /dev/null 2>&1; then
            log_info "Basic health check passed"
        else
            log_warn "Basic health check failed"
        fi
    fi
}

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--stack-name)
                STACK_NAME="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -h|--help)
                usage
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                ;;
        esac
    done
    
    log_info "Starting rollback process for stack: $STACK_NAME in region: $REGION"
    
    # Check prerequisites
    check_aws_cli
    
    # Show current stack information
    log_info "Current stack information:"
    get_stack_events 3
    
    if [ "$DRY_RUN" == "true" ]; then
        log_info "DRY RUN MODE - Would perform rollback but not executing"
        local stack_status
        stack_status=$(check_stack_status)
        log_info "Would rollback stack in status: $stack_status"
        exit 0
    fi
    
    # Confirm rollback unless forced
    if [ "$FORCE" != "true" ]; then
        echo -n "Are you sure you want to rollback the stack '$STACK_NAME'? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "Rollback cancelled by user"
            exit 0
        fi
    fi
    
    # Get current template for backup
    get_previous_template
    
    # Perform rollback
    if perform_rollback; then
        log_info "Rollback completed successfully"
        
        # Run health check
        run_health_check
        
        log_info "Rollback process completed"
        exit 0
    else
        log_error "Rollback failed"
        log_error "Check the CloudFormation console for more details"
        exit 1
    fi
}

main "$@"