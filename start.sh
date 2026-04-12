#!/bin/bash
# Anamnesis — start the API server and dashboard
#
# Usage:
#   ./start.sh          # Start both API + dashboard
#   ./start.sh api      # Start API only
#   ./start.sh dash     # Start dashboard only
#
# Prerequisites:
#   uv sync --extra api --extra dev
#   cd dashboard && npm install

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Initialize if no config exists
if [ ! -f "$ROOT/anamnesis.yaml" ]; then
    echo "No anamnesis.yaml found. Initializing..."
    cd "$ROOT" && uv run anamnesis init
fi

start_api() {
    echo "Starting Anamnesis API on http://localhost:8741"
    cd "$ROOT" && uv run anamnesis serve &
    API_PID=$!
    echo "API PID: $API_PID"
}

start_dashboard() {
    echo "Starting dashboard on http://localhost:5175"
    cd "$ROOT/dashboard" && npm run dev &
    DASH_PID=$!
    echo "Dashboard PID: $DASH_PID"
}

cleanup() {
    echo ""
    echo "Shutting down..."
    [ -n "$API_PID" ] && kill $API_PID 2>/dev/null
    [ -n "$DASH_PID" ] && kill $DASH_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

case "${1:-all}" in
    api)
        start_api
        wait $API_PID
        ;;
    dash|dashboard)
        start_dashboard
        wait $DASH_PID
        ;;
    all|*)
        start_api
        sleep 1
        start_dashboard
        echo ""
        echo "─────────────────────────────────────────"
        echo "  API:       http://localhost:8741"
        echo "  Dashboard: http://localhost:5175"
        echo "  API docs:  http://localhost:8741/docs"
        echo "─────────────────────────────────────────"
        echo "  Press Ctrl+C to stop both."
        echo ""
        wait
        ;;
esac
