#!/bin/sh

# Exit cleanly if Docker sends SIGTERM or SIGINT (e.g., `docker stop`)
trap 'echo "Stopping container..."; exit 0' TERM INT

echo "Starting runner loop (executing every 15 seconds)..."

while true; do
    echo "=========================================="
    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Executing main.py..."

    # Run the Python script; '|| true' ensures a transient network error
    # doesn't crash the container loop
    python main.py || echo "Execution exited with a non-zero status."

    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Sleeping for 15 seconds..."

    # Background sleep + wait allows immediate container shutdown on `docker stop`
    sleep 15 &
    wait $!
done
