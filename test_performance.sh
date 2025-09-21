#!/bin/bash

# Performance Testing Script for Lookbook-MPC
# Tests chat response times and verifies speed improvements

echo "🚀 Lookbook-MPC Performance Testing"
echo "=================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
API_BASE="http://localhost:8000"
TEST_QUERIES=(
    "I want to go dancing tonight"
    "I need party outfits"
    "Show me something elegant"
    "I want casual clothes"
)

# Function to test response time
test_response_time() {
    local query="$1"
    local session_id="perf_test_$(date +%s)"
    
    echo -n "Testing: \"$query\"... "
    
    # Measure response time
    start_time=$(date +%s.%N)
    
    response=$(curl -s -X POST "$API_BASE/v1/chat" \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$session_id\", \"message\": \"$query\"}" \
        2>/dev/null)
    
    end_time=$(date +%s.%N)
    response_time=$(echo "$end_time - $start_time" | bc)
    
    # Check if response is valid
    if echo "$response" | jq -e '.session_id' >/dev/null 2>&1; then
        outfit_count=$(echo "$response" | jq '.outfits | length' 2>/dev/null || echo "0")
        
        # Color code based on response time
        if (( $(echo "$response_time < 5.0" | bc -l) )); then
            color=$GREEN
            status="FAST"
        elif (( $(echo "$response_time < 10.0" | bc -l) )); then
            color=$YELLOW
            status="OK"
        else
            color=$RED
            status="SLOW"
        fi
        
        printf "${color}%.2fs${NC} [$status] - Found $outfit_count outfits\n" "$response_time"
        return 0
    else
        printf "${RED}FAILED${NC} - Invalid response\n"
        return 1
    fi
}

# Function to test system health
test_health() {
    echo -n "Checking system health... "
    
    start_time=$(date +%s.%N)
    health_response=$(curl -s "$API_BASE/health" 2>/dev/null)
    end_time=$(date +%s.%N)
    health_time=$(echo "$end_time - $start_time" | bc)
    
    if echo "$health_response" | jq -e '.status' >/dev/null 2>&1; then
        status=$(echo "$health_response" | jq -r '.status')
        if [ "$status" = "healthy" ]; then
            printf "${GREEN}%.3fs${NC} - System healthy\n" "$health_time"
            return 0
        else
            printf "${RED}%.3fs${NC} - System unhealthy: $status\n" "$health_time"
            return 1
        fi
    else
        printf "${RED}FAILED${NC} - Cannot reach service\n"
        return 1
    fi
}

# Function to test Ollama direct performance
test_ollama_direct() {
    echo -n "Testing direct Ollama performance... "
    
    if command -v ollama >/dev/null 2>&1; then
        start_time=$(date +%s.%N)
        ollama_response=$(timeout 10 ollama run llama3.2:1b-instruct-q4_K_M "What should I wear for dancing?" 2>/dev/null)
        end_time=$(date +%s.%N)
        ollama_time=$(echo "$end_time - $start_time" | bc)
        
        if [ $? -eq 0 ] && [ -n "$ollama_response" ]; then
            printf "${GREEN}%.2fs${NC} - Direct Ollama working\n" "$ollama_time"
            return 0
        else
            printf "${YELLOW}TIMEOUT${NC} - Ollama may not have fast model\n"
            return 1
        fi
    else
        printf "${YELLOW}SKIP${NC} - Ollama command not available\n"
        return 0
    fi
}

# Function to show performance summary
show_summary() {
    echo
    echo "📊 Performance Summary"
    echo "====================="
    echo
    echo "Expected Performance (with fast model):"
    echo "  • Health check: < 0.5 seconds"
    echo "  • Chat response: 3-8 seconds"
    echo "  • Direct Ollama: 1-3 seconds"
    echo
    echo "Performance Indicators:"
    printf "  • ${GREEN}FAST${NC}: < 5 seconds (Excellent)\n"
    printf "  • ${YELLOW}OK${NC}:   5-10 seconds (Acceptable)\n"
    printf "  • ${RED}SLOW${NC}: > 10 seconds (Needs optimization)\n"
    echo
}

# Function to show optimization tips
show_optimization_tips() {
    echo "🔧 Performance Optimization Tips"
    echo "================================="
    echo
    echo "If responses are slow (> 10 seconds):"
    echo "  1. Restart server with fast model:"
    echo "     ./start_server.sh"
    echo
    echo "  2. Verify fast model is downloaded:"
    echo "     ollama list | grep llama3.2"
    echo "     # If missing: ollama pull llama3.2:1b-instruct-q4_K_M"
    echo
    echo "  3. Check system resources:"
    echo "     htop  # Look for high CPU/memory usage"
    echo
    echo "  4. Test direct Ollama speed:"
    echo "     time ollama run llama3.2:1b-instruct-q4_K_M \"Hello\""
    echo
    echo "For detailed optimization guide:"
    echo "  cat PERFORMANCE_TUNING.md"
    echo
}

# Main testing sequence
main() {
    # Check dependencies
    if ! command -v curl >/dev/null 2>&1; then
        echo "❌ Error: curl is required but not installed"
        exit 1
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        echo "❌ Error: jq is required but not installed"
        echo "Install with: brew install jq (macOS) or apt install jq (Ubuntu)"
        exit 1
    fi
    
    if ! command -v bc >/dev/null 2>&1; then
        echo "❌ Error: bc is required but not installed"
        exit 1
    fi
    
    # Show summary first
    show_summary
    
    echo "🧪 Running Performance Tests"
    echo "============================="
    echo
    
    # Test system health first
    if ! test_health; then
        echo
        echo "❌ System health check failed. Please start the server:"
        echo "   ./start_server.sh"
        exit 1
    fi
    
    echo
    echo "Testing chat response times:"
    echo "----------------------------"
    
    total_tests=0
    passed_tests=0
    total_time=0
    
    # Test each query
    for query in "${TEST_QUERIES[@]}"; do
        if test_response_time "$query"; then
            ((passed_tests++))
        fi
        ((total_tests++))
    done
    
    echo
    echo "Additional tests:"
    echo "----------------"
    test_ollama_direct
    
    echo
    echo "📈 Results Summary"
    echo "=================="
    echo "Tests passed: $passed_tests/$total_tests"
    
    if [ $passed_tests -eq $total_tests ]; then
        printf "Overall status: ${GREEN}EXCELLENT${NC} ✅\n"
    elif [ $passed_tests -gt 0 ]; then
        printf "Overall status: ${YELLOW}PARTIAL${NC} ⚠️\n"
    else
        printf "Overall status: ${RED}NEEDS WORK${NC} ❌\n"
    fi
    
    echo
    
    # Show optimization tips if needed
    if [ $passed_tests -lt $total_tests ]; then
        show_optimization_tips
    else
        echo "🎉 System performance is optimal!"
        echo
        echo "Your chat interface should now respond quickly."
        echo "Visit: http://localhost:8000/ to test interactively."
    fi
}

# Help function
show_help() {
    echo "Performance Testing Script for Lookbook-MPC"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -q, --quick    Run quick health check only"
    echo "  -v, --verbose  Show detailed output"
    echo
    echo "Examples:"
    echo "  $0              # Run full performance test"
    echo "  $0 --quick      # Quick health check"
    echo
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -q|--quick)
        echo "🚀 Quick Health Check"
        echo "===================="
        test_health
        exit $?
        ;;
    -v|--verbose)
        set -x
        main
        ;;
    "")
        main
        ;;
    *)
        echo "❌ Unknown option: $1"
        show_help
        exit 1
        ;;
esac