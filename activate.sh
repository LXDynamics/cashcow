#!/bin/bash
# CashCow Poetry Environment Activation Script
# This script provides the activation command for the poetry virtual environment

echo "🐄 To activate the CashCow environment, run:"
echo ""
poetry env info --path | xargs -I {} echo "source {}/bin/activate"
echo ""
echo "Or simply copy and run:"
source $(poetry env info --path)/bin/activate 2>/dev/null && echo "✅ CashCow environment activated! You can now use 'cashcow' directly." || echo "Run the command above to activate the environment."