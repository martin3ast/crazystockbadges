#!/bin/bash

# VPN DNS/Routing Monitor
# Tracks DNS resolution and routing changes over time
# Detects and reports VPN failures without auto-reconnect

LOG_FILE="vpn_monitor_$(date +%Y%m%d_%H%M%S).log"
AUTO_RECONNECT=false  # Auto-reconnect disabled

echo "Starting VPN monitoring at $(date)" | tee -a "$LOG_FILE"
echo "Auto-reconnect: $AUTO_RECONNECT" | tee -a "$LOG_FILE"
echo "Press Ctrl+C to stop monitoring" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"

# Function to test DNS resolution
test_dns() {
    local domain="$1"
    local result=$(dig +short +time=3 +tries=1 "$domain" 2>/dev/null)
    if [[ -n "$result" ]]; then
        echo "✓ $domain resolved to: $result"
    else
        echo "✗ $domain failed to resolve"
    fi
}

# Function to test connectivity
test_connectivity() {
    local target="$1"
    local result=$(ping -c 1 -W 2000 "$target" 2>/dev/null | grep "1 packets transmitted")
    if [[ "$result" == *"1 packets received"* ]]; then
        echo "✓ $target reachable"
    else
        echo "✗ $target unreachable"
    fi
}

# Function to check current DNS servers
check_dns_servers() {
    echo "Current DNS servers:"
    scutil --dns | grep -A 2 "resolver #1" | grep nameserver | head -2
}

# Function to check default route
check_default_route() {
    echo "Default route:"
    route -n get default | grep -E "(gateway|interface)"
}

# Function to check GlobalProtect status
check_globalprotect_status() {
    echo "GlobalProtect Status:"
    local vpn_interface=$(ifconfig | grep -A 2 "utun" | grep "inet " | grep -v "inet6" | head -1)
    if [[ -n "$vpn_interface" ]]; then
        echo "Connected - VPN interface found: $vpn_interface"
        return 0
    else
        echo "Disconnected - No VPN interface found"
        return 1
    fi
}

# Function to detect VPN failure
detect_vpn_failure() {
    local dns_output=$(scutil --dns | grep -A 2 "resolver #1" | grep nameserver | head -1)
    local vpn_interface=$(ifconfig | grep -A 2 "utun" | grep "inet " | grep -v "inet6" | head -1)
    
    # If VPN interface is not found, that's a failure
    if [[ -z "$vpn_interface" ]]; then
        return 0  # VPN failure detected
    fi
    
    # Check if DNS is pointing to local servers when VPN should be connected
    if [[ "$dns_output" == *"192.168."* || "$dns_output" == *"10."* || "$dns_output" == *"172."* ]]; then
        return 0  # VPN failure detected (local DNS when VPN connected)
    fi
    
    # Check if Kent DNS server is unreachable when VPN should be connected
    local kent_ping=$(ping -c 1 -W 2000 "129.12.28.6" 2>/dev/null | grep "1 packets transmitted")
    if [[ "$kent_ping" != *"1 packets received"* ]]; then
        return 0  # VPN failure detected (can't reach university DNS)
    fi
    
    return 1  # No failure detected
}


# Function to log system sleep/wake events
log_sleep_wake_events() {
    local last_wake=$(pmset -g log | grep -E "Wake from|Sleep" | tail -1)
    if [[ -n "$last_wake" ]]; then
        echo "Recent sleep/wake: $last_wake"
    fi
}

# Monitor continuously
counter=0
while true; do
    counter=$((counter + 1))
    echo "" | tee -a "$LOG_FILE"
    echo "=== Check #$counter at $(date) ===" | tee -a "$LOG_FILE"
    
    {
        check_dns_servers
        echo ""
        check_default_route
        echo ""
        check_globalprotect_status
        echo ""
        log_sleep_wake_events
        echo ""
        
        echo "DNS Resolution Tests:"
        test_dns "google.com"
        test_dns "github.com"
        test_dns "kent.ac.uk"
        
        echo ""
        echo "Connectivity Tests:"
        test_connectivity "8.8.8.8"
        test_connectivity "google.com"
        test_connectivity "129.12.28.6"  # University DNS
        
        # Check for VPN failure and report status
        if detect_vpn_failure; then
            echo ""
            echo "⚠️  VPN failure detected!" | tee -a "$LOG_FILE"
        else
            echo ""
            echo "✓ VPN connection appears healthy" | tee -a "$LOG_FILE"
        fi
        
    } | tee -a "$LOG_FILE"
    
    echo "----------------------------------------" | tee -a "$LOG_FILE"
    sleep 60  # Check every minute
done