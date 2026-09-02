#!/bin/bash

# This script robustly starts the Gemini SRT Translator GUI.
# It ensures it runs from the correct directory and activates the Python virtual environment.

# Exit immediately if a command exits with a non-zero status for robustness.
set -e

# --- Get the script's directory ---
# This makes the script runnable from anywhere on the system.
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# --- Change to the script's directory ---
# All subsequent commands will be relative to this location.
cd "$SCRIPT_DIR"

# --- Define Virtual Environment ---
VENV_NAME="translator_app"

# --- Check for and activate Virtual Environment ---
# If the virtual environment doesn't exist, create it and install dependencies.
if [ ! -d "$VENV_NAME" ]; then
    echo "Virtual environment '$VENV_NAME' not found. Setting it up for the first time..."

    if ! command -v python3 &> /dev/null; then
        echo "Error: python3 is not installed or not in your PATH. Please install Python 3 to continue."
        exit 1
    fi

    echo "-> Creating Python virtual environment..."
    python3 -m venv "$VENV_NAME"

    echo "-> Activating environment and installing dependencies from requirements.txt..."
    source "$VENV_NAME/bin/activate"

    if [ ! -f "requirements.txt" ]; then
        echo "Error: 'requirements.txt' not found in $SCRIPT_DIR. Cannot install dependencies."
        exit 1
    fi

    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    echo "Setup complete."
else
    echo "Activating virtual environment: $VENV_NAME"
    source "$VENV_NAME/bin/activate"
fi

# --- Run the Application ---
echo "Starting Gemini SRT Translator GUI..."
python srt_translator-gui.pyw