#!/bin/bash

echo "🚀 Starting Automation Pipeline..."

source venv/bin/activate
export PYTHONPATH=$(pwd)

python validate.py

if [ $? -eq 0 ]; then
    echo "✅ FULL SYSTEM HEALTHY"
else
    echo "❌ SYSTEM FAILURE"
fi