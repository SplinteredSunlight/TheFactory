#!/usr/bin/env python3
"""
Wait for dependencies to be available before starting the application.
"""
import socket
import time
import os
import sys
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def wait_for_port(host, port, timeout=30):
    """Wait for a port to be ready on a host."""
    start_time = time.time()
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                sock.connect((host, port))
                logger.info(f"Port {port} on {host} is available")
                return True
        except (socket.timeout, ConnectionRefusedError):
            if time.time() - start_time >= timeout:
                logger.error(f"Timed out waiting for {host}:{port}")
                return False
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error checking {host}:{port}: {e}")
            return False

def wait_for_database():
    """Wait for the database to be available."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL not set, skipping database check")
        return True

    try:
        result = urlparse(db_url)
        host = result.hostname
        port = result.port or 5432  # Default PostgreSQL port
        
        logger.info(f"Waiting for database at {host}:{port}")
        return wait_for_port(host, port, timeout=60)
    except Exception as e:
        logger.error(f"Error parsing DATABASE_URL: {e}")
        return False

def wait_for_orchestrator():
    """Wait for the orchestrator service to be available."""
    orchestrator_host = os.environ.get("ORCHESTRATOR_HOST", "orchestrator-service")
    orchestrator_port = int(os.environ.get("ORCHESTRATOR_PORT", "8000"))
    
    logger.info(f"Waiting for orchestrator at {orchestrator_host}:{orchestrator_port}")
    return wait_for_port(orchestrator_host, orchestrator_port)

def wait_for_redis():
    """Wait for Redis to be available."""
    redis_host = os.environ.get("REDIS_HOST")
    if not redis_host:
        logger.warning("REDIS_HOST not set, skipping Redis check")
        return True
        
    redis_port = int(os.environ.get("REDIS_PORT", "6379"))
    
    logger.info(f"Waiting for Redis at {redis_host}:{redis_port}")
    return wait_for_port(redis_host, redis_port)

def main():
    """Main function."""
    logger.info("Checking dependencies...")
    
    # Wait for database
    if not wait_for_database():
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    # Wait for Redis if used
    if os.environ.get("USE_REDIS", "false").lower() == "true":
        if not wait_for_redis():
            logger.error("Failed to connect to Redis")
            sys.exit(1)
    
    # Wait for orchestrator if this is not the orchestrator service
    if os.environ.get("IS_ORCHESTRATOR", "true").lower() != "true":
        if not wait_for_orchestrator():
            logger.error("Failed to connect to orchestrator")
            sys.exit(1)
    
    logger.info("All dependencies are available")
    return 0

if __name__ == "__main__":
    sys.exit(main())