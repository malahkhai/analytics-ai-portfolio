#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

case "${1:-}" in
  red)
    export SIGNAL_GA4_MODEL="fct_daily_ecommerce_red_demo"
    ;;
  original)
    export SIGNAL_GA4_MODEL="fct_daily_ecommerce"
    ;;
  *)
    echo "Usage: ./scripts/run_demo.sh [red|original]"
    exit 1
    ;;
esac

echo "Running Signal Investigator: $SIGNAL_GA4_MODEL"

python -m src.ga4_diagnostics
python -m src.ai_tool_agent
python -m src.ai_investigation_structured
python -m src.ga4_reporting_adapter

echo "Investigation complete. Launching Maxim..."

exec python -m streamlit run streamlit_app.py
