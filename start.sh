#!/usr/bin/env bash
# Quick launcher script for Smart Inventory & POS Management System

set -e

# Change to the script's directory
cd "$(dirname "$0")"

echo "=========================================================="
echo " Starting SmartStock Pro - Inventory & POS Billing System "
echo "=========================================================="

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Please create one with: python3 -m venv venv && ./venv/bin/pip install django"
    exit 1
fi

# Run migrations
python manage.py migrate --noinput

# Launch development server
echo "Opening server at http://127.0.0.1:8000/"
echo "Press Ctrl+C to stop the server."
python manage.py runserver 127.0.0.1:8000

