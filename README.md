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

1.  **Install the core translator:**
    ```bash
    pip install gemini-srt-translator
    ```

2.  **Install PyQt6:**
    ```bash
    pip install PyQt6
    ```

3.  **Download and run the GUI:**
    Download the `srt_translator-gui.pyw` file and run it.

4.  **Configure and Translate:**
    *   Go to the "Settings" tab and enter your Gemini API Key. Click "List Models" to populate the model list.
    *   Adjust any other settings as needed and click "Save".
    *   Go to the "Translation" tab, add your SRT files to the queue.
    *   Click "Run" to start the translation process.
