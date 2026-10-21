#!/usr/bin/env bash
# ==============================================================================
# MANAS Automated Production Deployment Script
# Supports: Ubuntu, Debian, RedHat, macOS, AWS EC2, GCP Compute Engine
# ==============================================================================

set -euo pipefail

echo "======================================================================"
echo "MANAS — मनस्: Deploying Production Environment"
echo "======================================================================"

# 1. Preflight Dependency Checks
echo -e "\n[1/6] Checking system prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "ERROR: docker is not installed. Please install Docker first."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1 || {
    echo "ERROR: docker compose is required."; exit 1;
}

# Determine docker compose syntax
if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# 2. Check Environment Configuration
echo -e "\n[2/6] Verifying environment configuration..."
if [ ! -f .env.production ] && [ ! -f .env ]; then
    echo "WARNING: No .env.production or .env file found."
    echo "Copying .env.production.example to .env..."
    cp .env.production.example .env
    echo "NOTICE: Please update passwords and secret keys in .env for production!"
fi

# 3. Pull & Build Docker Images
echo -e "\n[3/6] Building production container images (Multi-stage build)..."
$DOCKER_COMPOSE -f docker-compose.prod.yml build --pull

# 4. Stop Previous Instances and Deploy
echo -e "\n[4/6] Launching services with rolling restart..."
$DOCKER_COMPOSE -f docker-compose.prod.yml up -d --remove-orphans

# 5. Wait for Health Checks
echo -e "\n[5/6] Awaiting service health checks..."
MAX_RETRIES=30
RETRY_COUNT=0

until [ $RETRY_COUNT -ge $MAX_RETRIES ]; do
    if curl -s -f http://localhost/api/health >/dev/null 2>&1; then
        echo "✓ Gateway and Backend are healthy!"
        break
    fi
    echo "  Waiting for services to become healthy ($((RETRY_COUNT+1))/$MAX_RETRIES)..."
    sleep 3
    RETRY_COUNT=$((RETRY_COUNT+1))
done

if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    echo "ERROR: Health check timed out after 90 seconds. Checking container logs:"
    $DOCKER_COMPOSE -f docker-compose.prod.yml logs --tail=40
    exit 1
fi

# 6. Verify Deployment
echo -e "\n[6/6] Production Deployment Verified Successfully!"
echo "======================================================================"
echo "  Web Interface:      http://localhost/"
echo "  API Documentation:  http://localhost/api/docs"
echo "  Health Check:       http://localhost/api/health"
echo "======================================================================"
