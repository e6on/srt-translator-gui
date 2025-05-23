import sys
import os
import json
import io
import importlib
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QGroupBox, QFrame
from PyQt6.QtCore import Qt

# --- Constants ---
SETTINGS_FILE = 'settings.json'

# Settings Keys
KEY_API_KEY = 'api_key'
KEY_API_KEY2 = 'api_key2'
KEY_DESCRIPTION = 'description'
KEY_BATCH_SIZE = 'batch_size'
KEY_TARGET_LANGUAGE = 'target_language'
KEY_MODEL_NAME = 'model_name'
KEY_START_LINE = 'start_line'
KEY_TEMPERATURE = 'temperature'
KEY_TOP_P = 'top_p'
KEY_THINKING_BUDGET = 'thinking_budget'
KEY_THINKING = 'thinking'
KEY_TOP_K = 'top_k'
KEY_SKIP_UPGRADE = 'skip_upgrade'
KEY_STREAMING = 'streaming'
KEY_PROGRESS_LOG = 'progress_log'
KEY_THOUGHTS_LOG = 'thoughts_log'
KEY_USE_COLORS = 'use_colors'
KEY_FREE_QUOTA = 'free_quota'
KEY_INPUT_FILE = 'input_file'

DEFAULT_SETTINGS = {
    KEY_API_KEY: '',
    KEY_API_KEY2: '',
    KEY_DESCRIPTION: '',
    KEY_BATCH_SIZE: '300',
    KEY_TARGET_LANGUAGE: 'Estonian',
    KEY_MODEL_NAME: 'gemini-2.5-flash-preview-05-20',
    KEY_START_LINE: '1',
    KEY_TEMPERATURE: '',
    KEY_TOP_P: '',
    KEY_THINKING_BUDGET: '2048',
    KEY_THINKING: True,
    KEY_TOP_K: '',
    KEY_SKIP_UPGRADE: False,
    KEY_STREAMING: True,
    KEY_PROGRESS_LOG: False,
    KEY_THOUGHTS_LOG: False,
    KEY_USE_COLORS: True,
    KEY_FREE_QUOTA: True,
    KEY_INPUT_FILE: ''
}

# UI Literals
APP_TITLE = "Gemini SRT Translator v2.0.0 GUI"
FOOTER_TEXT = "Made by e6on & Gemini AI, 2025"
MODEL_NAME_COMBO_WIDTH = 280
NUMERIC_INPUT_FIXED_WIDTH = 60
BATCH_LINE_INPUT_FIXED_WIDTH = 70
DESCRIPTION_MAX_HEIGHT = 90
SUPPORTED_LANGUAGES = [
    "Albanian", "Belarusian", "Bosnian", "Bulgarian", "Catalan", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Finnish", "French", "Galician", "German", "Greek", "Hungarian", "Icelandic", "Irish", "Italian", "Latvian", "Lithuanian", "Luxembourgish", "Macedonian", "Maltese", "Norwegian", "Polish", "Portuguese", "Romanian", "Russian", "Scots Gaelic", "Serbian", "Slovak", "Slovenian", "Spanish", "Swedish", "Ukrainian", "Welsh", "Yiddish"
]

# Function to save settings to a file
def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

# Function to load settings from a file
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                loaded_settings = json.load(f)
                # Merge with defaults to ensure all keys are present
                settings = DEFAULT_SETTINGS.copy()
                settings.update(loaded_settings)
                return settings
            except json.JSONDecodeError:
                # Corrupted file, return defaults
                return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

class TranslatorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = load_settings() # Load settings first
        self.initUI()
        self.populate_ui_from_settings() # Then populate UI

    def _create_header(self):
        header_label = QLabel(APP_TITLE)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = header_label.font()
        font.setPointSize(14)
        font.setBold(True)
        header_label.setFont(font)
        return header_label

    def _create_line_separator(self):
        line_separator = QFrame()
        line_separator.setFrameShape(QFrame.Shape.HLine)
        line_separator.setFrameShadow(QFrame.Shadow.Sunken)
        return line_separator

    def _create_translation_settings_group(self):
        # Create main layout
        translation_group = QGroupBox("Translation Settings")
        translation_layout = QVBoxLayout()
        translation_layout.setSpacing(5)
        translation_layout.setContentsMargins(10, 5, 10, 5)

        self.description_label = QLabel('Context:')
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter additional context about the subtitle content (optional)...")
        self.description_input.setMaximumHeight(DESCRIPTION_MAX_HEIGHT)
        translation_layout.addWidget(self.description_label)
        translation_layout.addWidget(self.description_input)

        self.target_language_label = QLabel('Target Language:')
        language_layout = QHBoxLayout()
        language_layout.setSpacing(5)
        language_layout.setContentsMargins(0, 5, 0, 5)
        self.target_language_combo = QComboBox()
        self.target_language_combo.addItems(SUPPORTED_LANGUAGES)
        language_layout.addWidget(self.target_language_label)
        language_layout.addWidget(self.target_language_combo)
        translation_layout.addLayout(language_layout)

        self.model_name_label = QLabel('Model:')
        model_layout = QHBoxLayout()
        model_layout.setSpacing(5)
        model_layout.setContentsMargins(0, 5, 0, 5)
        self.model_name_combo = QComboBox()
        self.model_name_combo.setFixedWidth(MODEL_NAME_COMBO_WIDTH)
        self.populate_models_button = QPushButton('List Models')
        self.populate_models_button.clicked.connect(self.populateModels)
        model_layout.addWidget(self.model_name_label)
        model_layout.addWidget(self.model_name_combo)
        model_layout.addWidget(self.populate_models_button)
        translation_layout.addLayout(model_layout)

        model_tuning1_layout = QHBoxLayout()
        model_tuning1_layout.setSpacing(5)
        model_tuning1_layout.setContentsMargins(0, 5, 0, 5)

        self.top_p_label = QLabel('Nucleus sampling (0.0-1.0):')
        self.top_p_input = QLineEdit()
        self.top_p_input.setFixedWidth(NUMERIC_INPUT_FIXED_WIDTH)
        model_tuning1_layout.addWidget(self.top_p_label)
        model_tuning1_layout.addWidget(self.top_p_input)

        self.temperature_label = QLabel('Randomness (0.0-2.0):')
        self.temperature_input = QLineEdit()
        self.temperature_input.setFixedWidth(NUMERIC_INPUT_FIXED_WIDTH)
        model_tuning1_layout.addWidget(self.temperature_label)
        model_tuning1_layout.addWidget(self.temperature_input)
        
        translation_layout.addLayout(model_tuning1_layout)

        model_tuning2_layout = QHBoxLayout()
        model_tuning2_layout.setSpacing(5)
        model_tuning2_layout.setContentsMargins(0, 5, 0, 5)
        
        self.thinking_budget_label = QLabel('Thinking budget (0-24576):')
        self.thinking_budget_input = QLineEdit()
        self.thinking_budget_input.setFixedWidth(NUMERIC_INPUT_FIXED_WIDTH)
        model_tuning2_layout.addWidget(self.thinking_budget_label)
        model_tuning2_layout.addWidget(self.thinking_budget_input)

        self.top_k_label = QLabel('Top-k sampling (≥0):')
        self.top_k_input = QLineEdit()
        self.top_k_input.setFixedWidth(NUMERIC_INPUT_FIXED_WIDTH)
        model_tuning2_layout.addWidget(self.top_k_label)
        model_tuning2_layout.addWidget(self.top_k_input)
        
        translation_layout.addLayout(model_tuning2_layout)

        tuning_checkbox1_layout = QHBoxLayout()
        tuning_checkbox1_layout.setSpacing(5)
        tuning_checkbox1_layout.setContentsMargins(0, 5, 0, 5)

        self.thinking_checkbox = QCheckBox('Enable thinking')
        tuning_checkbox1_layout.addWidget(self.thinking_checkbox)
        translation_layout.addLayout(tuning_checkbox1_layout)

        translation_group.setLayout(translation_layout)
        return translation_group

    def _create_input_file_controls_layout(self):
        input_file_main_layout = QVBoxLayout()
        self.input_file_label = QLabel('Input File:')
        input_file_layout = QHBoxLayout()
        self.input_file_display = QLineEdit()
        self.input_file_display.setReadOnly(True)
        self.browse_button = QPushButton('Browse')
        self.browse_button.clicked.connect(self.browseFile)
        input_file_layout.addWidget(self.input_file_display)
        input_file_layout.addWidget(self.browse_button)
        input_file_main_layout.addWidget(self.input_file_label)
        input_file_main_layout.addLayout(input_file_layout)
        return input_file_main_layout

    def _create_api_key_group(self):
        api_key_group = QGroupBox("API Key Management")
        api_key_layout = QVBoxLayout()
        api_key_layout.setSpacing(5)
        api_key_layout.setContentsMargins(10, 5, 10, 5)
        
        self.api_key_label = QLabel('Gemini API Key:')
        self.api_key_input = QLineEdit()
        api_key_layout.addWidget(self.api_key_label)
        api_key_layout.addWidget(self.api_key_input)

        self.api_key2_label = QLabel('Second Gemini API Key:')
        self.api_key2_input = QLineEdit()
        api_key_layout.addWidget(self.api_key2_label)
        api_key_layout.addWidget(self.api_key2_input)

        api_key_group.setLayout(api_key_layout)
        return api_key_group

    def _create_advanced_settings_group(self):
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QVBoxLayout()
        advanced_layout.setSpacing(5)
        advanced_layout.setContentsMargins(10, 5, 10, 5)
        
        lines_input_layout = QHBoxLayout()
        lines_input_layout.setSpacing(5)
        lines_input_layout.setContentsMargins(0, 5, 0, 5)
        
        self.batch_size_label = QLabel('Lines per Batch:')
        self.batch_size_input = QLineEdit()
        self.batch_size_input.setFixedWidth(BATCH_LINE_INPUT_FIXED_WIDTH)
        lines_input_layout.addWidget(self.batch_size_label)
        lines_input_layout.addWidget(self.batch_size_input)

        self.start_line_label = QLabel('Start Line:')
        self.start_line_input = QLineEdit()
        self.start_line_input.setFixedWidth(BATCH_LINE_INPUT_FIXED_WIDTH)
        lines_input_layout.addWidget(self.start_line_label)
        lines_input_layout.addWidget(self.start_line_input)
        
        advanced_layout.addLayout(lines_input_layout)
        
        checkbox1_layout = QHBoxLayout()
        checkbox1_layout.setSpacing(5)
        checkbox1_layout.setContentsMargins(0, 5, 0, 5)
        
        self.skip_upgrade_checkbox = QCheckBox('Skip Upgrade')
        checkbox1_layout.addWidget(self.skip_upgrade_checkbox)

        self.use_colors_checkbox = QCheckBox('Use Colors')
        checkbox1_layout.addWidget(self.use_colors_checkbox)
        
        advanced_layout.addLayout(checkbox1_layout)
        
        checkbox2_layout = QHBoxLayout()
        checkbox2_layout.setSpacing(5)
        checkbox2_layout.setContentsMargins(0, 5, 0, 5)

        self.free_quota_checkbox = QCheckBox('Free Quota')
        checkbox2_layout.addWidget(self.free_quota_checkbox)
        
        self.progress_log_checkbox = QCheckBox('Progress log')
        checkbox2_layout.addWidget(self.progress_log_checkbox)
        
        advanced_layout.addLayout(checkbox2_layout)
        
        checkbox3_layout = QHBoxLayout()
        checkbox3_layout.setSpacing(5)
        checkbox3_layout.setContentsMargins(0, 5, 0, 5)

        self.streaming_checkbox = QCheckBox('Enable streaming')
        checkbox3_layout.addWidget(self.streaming_checkbox)

        self.thoughts_log_checkbox = QCheckBox('Thoughts log')
        checkbox3_layout.addWidget(self.thoughts_log_checkbox)
        
        advanced_layout.addLayout(checkbox3_layout)

        advanced_group.setLayout(advanced_layout)
        return advanced_group

    def _create_action_buttons_layout(self):
        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.saveSettings)
        
        self.run_button = QPushButton('Run')
        self.run_button.clicked.connect(self.runTranslation)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.run_button)
        return button_layout

    def _create_footer(self):
        footer_label = QLabel(FOOTER_TEXT)
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = footer_label.font()
        font.setPointSize(8)
        footer_label.setFont(font)
        return footer_label

    def initUI(self):
        self.setWindowTitle(APP_TITLE)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(10, 10, 10, 5)

        main_layout.addWidget(self._create_header())
        main_layout.addWidget(self._create_line_separator())

        columns_layout = QHBoxLayout()

        # Left column
        left_layout = QVBoxLayout()
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(5, 10, 5, 10)
        left_layout.addWidget(self._create_translation_settings_group())
        left_layout.addLayout(self._create_input_file_controls_layout())
        left_layout.addStretch(1) # Add stretch to push content up

        # Right column
        right_layout = QVBoxLayout()
        right_layout.setSpacing(5)
        right_layout.setContentsMargins(5, 10, 5, 10)
        right_layout.addWidget(self._create_api_key_group())
        right_layout.addWidget(self._create_advanced_settings_group())
        right_layout.addStretch(1) # Add stretch to push content up
        right_layout.addLayout(self._create_action_buttons_layout())

        # Add left and right layouts to columns layout
        columns_layout.addLayout(left_layout)
        columns_layout.addLayout(right_layout)
        main_layout.addLayout(columns_layout)
        
        main_layout.addWidget(self._create_line_separator())
        main_layout.addWidget(self._create_footer())

        # Set main layout
        self.setLayout(main_layout)

    def browseFile(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Input File", "", "SRT Files (*.srt);;All Files (*)")
        if file_name:
            self.input_file_display.setText(file_name)
    
    def populateModels(self):
        if not self.api_key_input.text():
            QMessageBox.warning(self, "API Key Missing", "Please enter the Gemini API Key to list models.")
            return

        try:
            import gemini_srt_translator as gst
        except ImportError:
            QMessageBox.critical(self, "Module Error", "Module 'gemini_srt_translator' not found. Please ensure it is installed.")
            return

        gst.gemini_api_key = self.api_key_input.text()

        original_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        models = []
        try:
            gst.listmodels()
            models_output = buffer.getvalue().strip()
            if models_output:
                models = [model.strip() for model in models_output.split('\n') if model.strip()]
        except Exception as e:
            QMessageBox.critical(self, "Error Listing Models", f"An error occurred while listing models: {e}")
            return
        finally:
            sys.stdout = original_stdout # Ensure stdout is always restored

        if models:
            self.model_name_combo.clear()
            self.model_name_combo.addItems(models)
            # Try to set the previously selected/default model
            desired_model = self.settings.get(KEY_MODEL_NAME, DEFAULT_SETTINGS[KEY_MODEL_NAME])
            if desired_model in models:
                self.model_name_combo.setCurrentText(desired_model)
            elif self.model_name_combo.count() > 0:
                self.model_name_combo.setCurrentIndex(0)
        else:
            QMessageBox.warning(self, "No Models Found", "Failed to retrieve models or no models available. Check API key and network.")

    def saveSettings(self):
        current_settings = {
            KEY_API_KEY: self.api_key_input.text(),
            KEY_API_KEY2: self.api_key2_input.text(),
            KEY_DESCRIPTION: self.description_input.toPlainText(),
            KEY_BATCH_SIZE: self.batch_size_input.text(),
            KEY_TARGET_LANGUAGE: self.target_language_combo.currentText(),
            KEY_MODEL_NAME: self.model_name_combo.currentText(),
            KEY_START_LINE: self.start_line_input.text(),
            KEY_TEMPERATURE: self.temperature_input.text(),
            KEY_TOP_P: self.top_p_input.text(),
            KEY_THINKING_BUDGET: self.thinking_budget_input.text(),
            KEY_THINKING: self.thinking_checkbox.isChecked(),
            KEY_TOP_K: self.top_k_input.text(),
            KEY_SKIP_UPGRADE: self.skip_upgrade_checkbox.isChecked(),
            KEY_STREAMING: self.streaming_checkbox.isChecked(),
            KEY_PROGRESS_LOG: self.progress_log_checkbox.isChecked(),
            KEY_THOUGHTS_LOG: self.thoughts_log_checkbox.isChecked(),
            KEY_USE_COLORS: self.use_colors_checkbox.isChecked(),
            KEY_FREE_QUOTA: self.free_quota_checkbox.isChecked(),
            KEY_INPUT_FILE: self.input_file_display.text()
        }
        save_settings(current_settings)
        self.settings = current_settings # Update in-memory settings
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")

    def populate_ui_from_settings(self):
        self.api_key_input.setText(self.settings[KEY_API_KEY])
        self.api_key2_input.setText(self.settings[KEY_API_KEY2])
        self.description_input.setPlainText(self.settings[KEY_DESCRIPTION])
        self.batch_size_input.setText(self.settings[KEY_BATCH_SIZE])
        
        # Set target language, ensuring it's a valid choice
        target_lang = self.settings[KEY_TARGET_LANGUAGE]
        if self.target_language_combo.findText(target_lang) != -1:
            self.target_language_combo.setCurrentText(target_lang)
        elif self.target_language_combo.count() > 0: # Fallback to first item if saved one not found
            self.target_language_combo.setCurrentIndex(0)

        # Model name will be set if it exists after populateModels, or user selects.
        # We store the desired model name from settings; populateModels will try to use it.
        self.model_name_combo.setCurrentText(self.settings[KEY_MODEL_NAME]) # Initial attempt

        self.start_line_input.setText(self.settings[KEY_START_LINE])
        self.temperature_input.setText(self.settings[KEY_TEMPERATURE])
        self.top_p_input.setText(self.settings[KEY_TOP_P])
        self.thinking_budget_input.setText(self.settings[KEY_THINKING_BUDGET])
        self.thinking_checkbox.setChecked(self.settings[KEY_THINKING])
        self.top_k_input.setText(self.settings[KEY_TOP_K])
        self.skip_upgrade_checkbox.setChecked(self.settings[KEY_SKIP_UPGRADE])
        self.streaming_checkbox.setChecked(self.settings[KEY_STREAMING])
        self.progress_log_checkbox.setChecked(self.settings[KEY_PROGRESS_LOG])
        self.thoughts_log_checkbox.setChecked(self.settings[KEY_THOUGHTS_LOG])
        self.use_colors_checkbox.setChecked(self.settings[KEY_USE_COLORS])
        self.free_quota_checkbox.setChecked(self.settings[KEY_FREE_QUOTA])
        self.input_file_display.setText(self.settings[KEY_INPUT_FILE])

    def runTranslation(self):
        # --- Validation of required fields ---
        required_fields_map = {
            self.api_key_input: "Gemini API Key",
            self.batch_size_input: "Batch Size",
            self.start_line_input: "Start Line",
            self.input_file_display: "Input File",
        }
        for widget, name in required_fields_map.items():
            if not widget.text().strip():
                QMessageBox.warning(self, "Input Error", f"{name} is required.")
                return

        if not self.target_language_combo.currentText():
            QMessageBox.warning(self, "Input Error", "Target Language must be selected.")
            return
        if not self.model_name_combo.currentText(): # Model might not be in list if not populated yet
            QMessageBox.warning(self, "Input Error", "Model Name must be selected. Try 'List Models' first.")
            return
        # --- End Validation ---

        import gemini_srt_translator as gst
        importlib.reload(gst) # Reload to ensure fresh defaults for optional params
        
        gst.gemini_api_key = self.api_key_input.text()
        gst.gemini_api_key2 = self.api_key2_input.text()
        gst.target_language = self.target_language_combo.currentText()
        input_file = self.input_file_display.text()
        gst.input_file = input_file
        gst.output_file = f"{os.path.splitext(input_file)[0]}_translated.srt"
        gst.description = self.description_input.toPlainText()
        gst.model_name = self.model_name_combo.currentText()

        # Numeric field parsing with specific error messages
        try:
            gst.batch_size = int(self.batch_size_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", f"Batch Size must be a valid integer. You entered: '{self.batch_size_input.text()}'")
            return
        try:
            gst.start_line = int(self.start_line_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", f"Start Line must be a valid integer. You entered: '{self.start_line_input.text()}'")
            return

        temperature_text = self.temperature_input.text()
        if temperature_text:
            try:
                value = float(temperature_text)
                if not (0.0 <= value <= 2.0):
                    QMessageBox.warning(self, "Input Error", f"Temperature must be between 0.0 and 2.0. You entered: '{value}'")
                    return
                gst.temperature = value
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"Temperature must be a valid number (e.g., 0.7). You entered: '{temperature_text}'")
                return

        top_p_text = self.top_p_input.text()
        if top_p_text:
            try:
                value = float(top_p_text)
                if not (0.0 <= value <= 1.0):
                    QMessageBox.warning(self, "Input Error", f"Nucleus sampling (Top P) must be between 0.0 and 1.0. You entered: '{value}'")
                    return
                gst.top_p = value
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"Nucleus sampling (Top P) must be a valid number (e.g., 0.9). You entered: '{top_p_text}'")
                return

        thinking_budget_text = self.thinking_budget_input.text()
        if thinking_budget_text:
            try:
                value = int(thinking_budget_text)
                if not (0 <= value <= 24576):
                    QMessageBox.warning(self, "Input Error", f"Thinking budget must be between 0 and 24576. You entered: '{value}'")
                    return
                gst.thinking_budget = value
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"Thinking budget must be a valid integer. You entered: '{thinking_budget_text}'")
                return

        top_k_text = self.top_k_input.text()
        if top_k_text:
            try:
                value = int(top_k_text)
                if not (value >= 0):
                    QMessageBox.warning(self, "Input Error", f"Top-K sampling must be >= 0. You entered: '{value}'")
                    return
                gst.top_k = value
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"Top-K sampling must be a valid integer (e.g., 40). You entered: '{top_k_text}'")
                return

        gst.thinking = self.thinking_checkbox.isChecked()
        gst.skip_upgrade = self.skip_upgrade_checkbox.isChecked()
        gst.streaming = self.streaming_checkbox.isChecked()
        gst.progress_log = self.progress_log_checkbox.isChecked()
        gst.thoughts_log = self.thoughts_log_checkbox.isChecked()
        gst.use_colors = self.use_colors_checkbox.isChecked()
        gst.free_quota = self.free_quota_checkbox.isChecked()
        
        try:
            gst.translate()
            QMessageBox.information(self, "Success", "Translation completed successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Translation Error", f"An error occurred during translation: {e}\n\nPlease check your settings and the console output if available.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = TranslatorGUI()
    # gui.resize(700, 600) # Optional: set a default size
    gui.show()
    sys.exit(app.exec())