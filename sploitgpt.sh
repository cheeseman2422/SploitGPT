#!/bin/bash
# Quick start script for SploitGPT

set -e

# Check if container is running
if docker compose ps | grep -q "sploitgpt.*running"; then
    docker compose exec sploitgpt sploitgpt "$@"
else
    docker compose run --rm sploitgpt sploitgpt "$@"
fi
