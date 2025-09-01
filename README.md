# Gemini SRT Translator GUI

A user-friendly graphical interface for the powerful [Gemini SRT Translator](https://github.com/MaKTaiL/gemini-srt-translator) tool.

This GUI simplifies the process of translating subtitle files (`.srt`) by providing an intuitive interface to manage all the features of the underlying command-line tool.

## Features

*   **Tabbed Interface**: A clean layout separating the main translation workflow from detailed settings.
*   **Translation Queue**: Select and manage multiple SRT files to translate them in a single batch.
*   **Full Settings Control**: Access and configure all `gemini-srt-translator` options through the UI:
    *   API Key Management (supports primary and secondary keys).
    *   Dynamic Model Listing (automatically fetches available models with your API key).
    *   Model tuning (Temperature, Top P, Top K, etc.).
    *   Contextual translation with descriptions, video, or audio files.
    *   Advanced options like batch size, auto-resume, and logging.
*   **Persistent Settings**: All your configurations are automatically saved to a `settings.json` file and loaded on startup.
*   **Progress & Error Handling**:
    *   Real-time progress updates in the window title during batch translation.
    *   Clear error messages for invalid inputs or translation failures.
    *   Option to continue with the next file if one fails in the queue.

## Requirements

*   Python 3.x
*   The `gemini-srt-translator` package.
*   PyQt6

## Installation & Usage
 
### Quick Start (Linux / macOS)
 
The `translate.sh` script automates the entire setup.

First, ensure `translate.sh`, `srt_translator-gui.pyw`, and `requirements.txt` are all in the same folder.
 
1.  **Make the script executable (only need to do this once):**
    ```bash
    chmod +x translate.sh
    ```
 
2.  **Run the script:**
    ```bash
    ./translate.sh
    ```
    The first time you run it, the script will automatically create a Python virtual environment, install all required dependencies, and launch the application. Subsequent runs will be much faster.
 
### Manual Installation (Windows / Other)
 
If you are on Windows or prefer a manual setup:
 
1.  **Create and Activate a Virtual Environment:**
    ```bash
    # Create the environment
    python3 -m venv translator_app
 
    # Activate on Windows
    .\translator_app\Scripts\activate
 
    # Activate on Linux/macOS
    source translator_app/bin/activate
    ```
 
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
 
3.  **Run the GUI:**
    ```bash
    python srt_translator-gui.pyw
    ```
 
### How to Use the GUI
 
1.  **Configure:** Go to the "Settings" tab and enter your Gemini API Key. Click "List Models" to populate the model list. Adjust any other settings as needed and click "Save".
2.  **Translate:** Go to the "Translation" tab, add your SRT files to the queue, and click "Run" to start the translation process.
