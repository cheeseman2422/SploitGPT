#!/bin/bash
set -e

echo '
 ███████╗██████╗ ██╗      ██████╗ ██╗████████╗ ██████╗ ██████╗ ████████╗
 ██╔════╝██╔══██╗██║     ██╔═══██╗██║╚══██╔══╝██╔════╝ ██╔══██╗╚══██╔══╝
 ███████╗██████╔╝██║     ██║   ██║██║   ██║   ██║  ███╗██████╔╝   ██║   
 ╚════██║██╔═══╝ ██║     ██║   ██║██║   ██║   ██║   ██║██╔═══╝    ██║   
 ███████║██║     ███████╗╚██████╔╝██║   ██║   ╚██████╔╝██║        ██║   
 ╚══════╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝   ╚═╝    ╚═════╝ ╚═╝        ╚═╝   
                                                                         
                        [ INSTALLER ]
'

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${CYAN}[*]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check prerequisites
log_info "Checking prerequisites..."

# Docker
if command -v docker &> /dev/null; then
    log_success "Docker found"
else
    log_error "Docker not found. Please install Docker first."
    exit 1
fi

# Check for NVIDIA GPU (optional)
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "")
    if [ -n "$GPU_INFO" ]; then
        log_success "NVIDIA GPU detected: $GPU_INFO"
        HAS_GPU=true
    else
        log_warn "nvidia-smi found but no GPU detected"
        HAS_GPU=false
    fi
else
    log_warn "No NVIDIA GPU detected - will use CPU inference (slower)"
    HAS_GPU=false
fi

# Check for Ollama
if command -v ollama &> /dev/null; then
    log_success "Ollama found"
    OLLAMA_INSTALLED=true
else
    log_warn "Ollama not found - will install"
    OLLAMA_INSTALLED=false
fi

echo ""
log_info "Installation Options:"
echo ""
echo "  1) Full install (Ollama + Model + Docker image)"
echo "  2) Docker only (assumes Ollama already running)"
echo "  3) Development install (local Python, no Docker)"
echo ""
read -p "Select option [1]: " INSTALL_OPTION
INSTALL_OPTION=${INSTALL_OPTION:-1}

case $INSTALL_OPTION in
    1)
        # Install Ollama if needed
        if [ "$OLLAMA_INSTALLED" = false ]; then
            log_info "Installing Ollama..."
            curl -fsSL https://ollama.ai/install.sh | sh
            log_success "Ollama installed"
        fi
        
        # Start Ollama
        log_info "Starting Ollama..."
        ollama serve &>/dev/null &
        sleep 3
        
        # Pull model based on GPU
        if [ "$HAS_GPU" = true ]; then
            # Check VRAM
            VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
            if [ "$VRAM" -ge 24000 ]; then
                MODEL="qwen2.5:32b"
                log_info "24GB+ VRAM detected - using Qwen2.5-32B"
            elif [ "$VRAM" -ge 12000 ]; then
                MODEL="qwen2.5:14b"
                log_info "12GB+ VRAM detected - using Qwen2.5-14B"
            else
                MODEL="qwen2.5:7b"
                log_info "<12GB VRAM detected - using Qwen2.5-7B"
            fi
        else
            MODEL="qwen2.5:7b"
            log_info "No GPU - using Qwen2.5-7B (CPU mode will be slow)"
        fi
        
        log_info "Pulling model: $MODEL (this may take a while)..."
        ollama pull $MODEL
        log_success "Model ready: $MODEL"
        
        # Save model choice
        echo "SPLOITGPT_MODEL=$MODEL" >> .env
        echo "OLLAMA_HOST=http://host.docker.internal:11434" >> .env
        ;;
    2)
        log_info "Docker-only install"
        echo "OLLAMA_HOST=http://host.docker.internal:11434" >> .env
        ;;
    3)
        log_info "Development install"
        python3 -m pip install -e .
        log_success "Installed in development mode"
        echo ""
        log_info "Run with: python -m sploitgpt"
        exit 0
        ;;
esac

# Build Docker image
log_info "Building Docker image (this may take 10-15 minutes)..."
docker build -t sploitgpt:latest .
log_success "Docker image built"

# Create directories
mkdir -p loot sessions data

# Done
echo ""
log_success "Installation complete!"
echo ""
echo "To start SploitGPT:"
echo ""
echo "  docker compose up -d"
echo "  docker compose exec sploitgpt sploitgpt"
echo ""
echo "Or for interactive mode:"
echo ""
echo "  docker compose run --rm sploitgpt"
echo ""
