#!/bin/bash

# Inter-Agent Communication Setup Script
# Installs Redis and configures the communication layer
# Billionaire-speed execution setup

set -e

echo "🚀 INTER-AGENT COMMUNICATION SETUP"
echo "=================================="
echo "Time estimate: 5 minutes"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        print_error "Unsupported OS: $OSTYPE"
        exit 1
    fi
    print_status "Detected OS: $OS"
}

# Check if Docker is available
check_docker() {
    if command -v docker &> /dev/null; then
        print_status "Docker is installed"
        return 0
    else
        print_warning "Docker not found"
        return 1
    fi
}

# Install Redis via Docker
install_redis_docker() {
    print_status "Installing Redis via Docker..."
    
    # Create Redis configuration
    cat > redis.conf << EOF
# Redis Configuration for Agent Communication
bind 0.0.0.0
port 6379
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
EOF
    
    # Run Redis container
    docker run -d \
        --name agent-redis \
        -p 6379:6379 \
        -v $(pwd)/redis.conf:/usr/local/etc/redis/redis.conf \
        -v $(pwd)/redis-data:/data \
        redis:7-alpine \
        redis-server /usr/local/etc/redis/redis.conf
    
    print_status "Redis container started"
}

# Install Redis natively on macOS
install_redis_macos() {
    print_status "Installing Redis on macOS..."
    
    if command -v brew &> /dev/null; then
        brew install redis
        brew services start redis
        print_status "Redis installed and started via Homebrew"
    else
        print_error "Homebrew not found. Please install Homebrew first:"
        echo "       /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
}

# Install Redis natively on Linux
install_redis_linux() {
    print_status "Installing Redis on Linux..."
    
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y redis-server
        sudo systemctl start redis-server
        sudo systemctl enable redis-server
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS
        sudo yum install -y epel-release
        sudo yum install -y redis
        sudo systemctl start redis
        sudo systemctl enable redis
    else
        print_error "Unsupported Linux distribution"
        exit 1
    fi
    
    print_status "Redis installed and started"
}

# Test Redis connection
test_redis() {
    print_status "Testing Redis connection..."
    
    if redis-cli ping > /dev/null 2>&1; then
        print_status "Redis is responding"
        
        # Get Redis info
        REDIS_VERSION=$(redis-cli INFO server | grep redis_version | cut -d: -f2 | tr -d '\r')
        print_status "Redis version: $REDIS_VERSION"
    else
        print_error "Redis is not responding"
        exit 1
    fi
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 not found. Please install Python 3 and pip"
        exit 1
    fi
    
    # Create requirements file
    cat > requirements.txt << EOF
redis==5.0.1
asyncio
dataclasses
typing
EOF
    
    # Install dependencies
    pip3 install -r requirements.txt
    
    print_status "Python dependencies installed"
}

# Configure Redis for production
configure_redis_production() {
    print_status "Configuring Redis for production..."
    
    # Set Redis configuration via CLI
    redis-cli CONFIG SET maxmemory 2gb
    redis-cli CONFIG SET maxmemory-policy allkeys-lru
    redis-cli CONFIG SET save "900 1 300 10 60 10000"
    redis-cli CONFIG SET appendonly yes
    redis-cli CONFIG REWRITE
    
    print_status "Redis configured for production"
}

# Create systemd service (Linux only)
create_systemd_service() {
    if [[ "$OS" == "linux" ]]; then
        print_status "Creating systemd service..."
        
        sudo cat > /etc/systemd/system/agent-communicator.service << EOF
[Unit]
Description=Multi-Agent Communication Service
After=redis.service
Requires=redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/inter_agent_communication.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        print_status "Systemd service created"
    fi
}

# Create launch script
create_launch_script() {
    print_status "Creating launch script..."
    
    cat > launch_agents.sh << 'EOF'
#!/bin/bash

# Launch script for multi-agent system
# Starts Redis and agent communication layer

echo "🚀 Launching Multi-Agent System"
echo "==============================="

# Check Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Starting Redis..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start redis
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start redis-server
    fi
    sleep 2
fi

# Launch communication layer
echo "Starting communication layer..."
python3 inter_agent_communication.py &
COMM_PID=$!

echo "✅ System started"
echo "   Communication PID: $COMM_PID"
echo "   Redis: localhost:6379"
echo ""
echo "To stop: kill $COMM_PID && redis-cli shutdown"

# Wait for interrupt
trap "kill $COMM_PID; redis-cli shutdown; exit" INT TERM
wait $COMM_PID
EOF
    
    chmod +x launch_agents.sh
    print_status "Launch script created: ./launch_agents.sh"
}

# Create monitoring dashboard
create_monitoring_dashboard() {
    print_status "Creating monitoring dashboard..."
    
    cat > monitor_agents.py << 'EOF'
#!/usr/bin/env python3
"""
Real-time monitoring dashboard for multi-agent system
"""

import time
import redis
import json
from datetime import datetime

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def clear_screen():
    print('\033[2J\033[H')

def get_metrics():
    info = r.info()
    return {
        'clients': info.get('connected_clients', 0),
        'memory': info.get('used_memory_human', 'N/A'),
        'ops': info.get('instantaneous_ops_per_sec', 0),
        'uptime': info.get('uptime_in_seconds', 0)
    }

def get_active_tasks():
    tasks = []
    for key in r.keys('state:*'):
        state = r.get(key)
        if state:
            task = json.loads(state)
            tasks.append({
                'id': task.get('task_id', 'N/A'),
                'status': task.get('status', 'N/A'),
                'completion': task.get('completion', 0),
                'agent': task.get('agent_id', 'N/A')
            })
    return tasks

def main():
    while True:
        clear_screen()
        metrics = get_metrics()
        tasks = get_active_tasks()
        
        print("=" * 60)
        print(" MULTI-AGENT SYSTEM MONITOR".center(60))
        print("=" * 60)
        print(f"\n📊 METRICS")
        print(f"   Connected Clients: {metrics['clients']}")
        print(f"   Memory Usage: {metrics['memory']}")
        print(f"   Ops/Second: {metrics['ops']}")
        print(f"   Uptime: {metrics['uptime']}s")
        
        print(f"\n📋 ACTIVE TASKS ({len(tasks)})")
        for task in tasks[:10]:  # Show max 10 tasks
            bar = '█' * (task['completion'] // 10) + '░' * (10 - task['completion'] // 10)
            print(f"   {task['id'][:20]:20} [{bar}] {task['completion']}% - {task['status']}")
        
        print(f"\n🕐 Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to exit")
        
        time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
EOF
    
    chmod +x monitor_agents.py
    print_status "Monitoring dashboard created: ./monitor_agents.py"
}

# Main installation flow
main() {
    echo "Starting installation..."
    echo ""
    
    # Detect OS
    detect_os
    
    # Ask installation method
    echo ""
    echo "Choose installation method:"
    echo "1) Docker (recommended)"
    echo "2) Native installation"
    read -p "Enter choice (1 or 2): " choice
    
    case $choice in
        1)
            if check_docker; then
                install_redis_docker
            else
                print_warning "Docker not available, falling back to native installation"
                if [[ "$OS" == "macos" ]]; then
                    install_redis_macos
                else
                    install_redis_linux
                fi
            fi
            ;;
        2)
            if [[ "$OS" == "macos" ]]; then
                install_redis_macos
            else
                install_redis_linux
            fi
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
    
    # Test Redis connection
    test_redis
    
    # Install Python dependencies
    install_python_deps
    
    # Configure Redis
    configure_redis_production
    
    # Create service files
    create_systemd_service
    create_launch_script
    create_monitoring_dashboard
    
    echo ""
    echo "=================================="
    print_status "Installation complete!"
    echo ""
    echo "📚 Next steps:"
    echo "   1. Launch system: ./launch_agents.sh"
    echo "   2. Monitor agents: ./monitor_agents.py"
    echo "   3. Check agent.md for orchestration rules"
    echo ""
    echo "🚀 Ready for billionaire-speed execution!"
}

# Run main installation
main
