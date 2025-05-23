import sys
import os
import json
import io
import importlib
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QGroupBox, QFrame
from PyQt6.QtCore import Qt

# Function to save settings to a file
def save_settings(settings):
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

# Function to load settings from a file
def load_settings():
    if os.path.exists('settings.json'):
        with open('settings.json', 'r') as f:
            return json.load(f)
    return {}

class TranslatorGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.loadSettings()

    def initUI(self):
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(10, 10, 10, 5)

        # Add header
        header_label = QLabel("Gemini SRT Translator v2.0.0 GUI")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)

        # Add line separator
        line_separator = QFrame()
        line_separator.setFrameShape(QFrame.Shape.HLine)
        line_separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line_separator)

        # Create columns layout
        columns_layout = QHBoxLayout()

        # Left column layout
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(5, 10, 5, 10)

        # Translation Settings Group
        translation_group = QGroupBox("Translation Settings")
        translation_layout = QVBoxLayout()
        translation_layout.setSpacing(10)
        translation_layout.setContentsMargins(10, 5, 10, 5)
        
        self.description_label = QLabel('Context:')
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter additional context about the subtitle content (optional)...")
        self.description_input.setMaximumHeight(90)
        translation_layout.addWidget(self.description_label)
        translation_layout.addWidget(self.description_input)

        self.target_language_label = QLabel('Target Language:')
        language_layout = QHBoxLayout()
        self.target_language_combo = QComboBox()
        self.target_language_combo.addItems(["Albanian", "Belarusian", "Bosnian", "Bulgarian", "Catalan", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Finnish", "French", "Galician", "German", "Greek", "Hungarian", "Icelandic", "Irish", "Italian", "Latvian", "Lithuanian", "Luxembourgish", "Macedonian", "Maltese", "Norwegian", "Polish", "Portuguese", "Romanian", "Russian", "Scots Gaelic", "Serbian", "Slovak", "Slovenian", "Spanish", "Swedish", "Ukrainian", "Welsh", "Yiddish"])
        self.target_language_combo.setCurrentText('Estonia')
        language_layout.addWidget(self.target_language_label)
        language_layout.addWidget(self.target_language_combo)
        translation_layout.addLayout(language_layout)

        self.model_name_label = QLabel('Model:')
        model_layout = QHBoxLayout()
        self.model_name_combo = QComboBox()
        self.model_name_combo.setFixedWidth(280)
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
        self.top_p_input.setFixedWidth(60)
        # self.top_p_input.setText('1')
        model_tuning1_layout.addWidget(self.top_p_label)
        model_tuning1_layout.addWidget(self.top_p_input)
        
        self.temperature_label = QLabel('Randomness (0.0-2.0):')
        self.temperature_input = QLineEdit()
        self.temperature_input.setFixedWidth(60)
        # self.temperature_input.setText('30')
        model_tuning1_layout.addWidget(self.temperature_label)
        model_tuning1_layout.addWidget(self.temperature_input)
        
        translation_layout.addLayout(model_tuning1_layout)

        model_tuning2_layout = QHBoxLayout()
        model_tuning2_layout.setSpacing(5)
        model_tuning2_layout.setContentsMargins(0, 5, 0, 5)
        
        self.thinking_budget_label = QLabel('Thinking budget (0-24576):')
        self.thinking_budget_input = QLineEdit()
        self.thinking_budget_input.setFixedWidth(60)
        self.thinking_budget_input.setText('2048')
        model_tuning2_layout.addWidget(self.thinking_budget_label)
        model_tuning2_layout.addWidget(self.thinking_budget_input)

        self.top_k_label = QLabel('Top-k sampling (≥0):')
        self.top_k_input = QLineEdit()
        self.top_k_input.setFixedWidth(60)
        # self.top_k_input.setText('1')
        model_tuning2_layout.addWidget(self.top_k_label)
        model_tuning2_layout.addWidget(self.top_k_input)
        
        translation_layout.addLayout(model_tuning2_layout)

        tunung_checkbox1_layout = QHBoxLayout()
        tunung_checkbox1_layout.setSpacing(5)
        tunung_checkbox1_layout.setContentsMargins(0, 5, 0, 5)
        
        self.thinking_checkbox = QCheckBox('Enable thinking')
        self.thinking_checkbox.setChecked(True)
        tunung_checkbox1_layout.addWidget(self.thinking_checkbox)
        
        translation_layout.addLayout(tunung_checkbox1_layout)

        translation_group.setLayout(translation_layout)
        left_layout.addWidget(translation_group)

        # Input File Selection
        self.input_file_label = QLabel('Input File:')
        input_file_layout = QHBoxLayout()
        self.input_file_display = QLineEdit()
        self.input_file_display.setReadOnly(True)
        self.browse_button = QPushButton('Browse')
        self.browse_button.clicked.connect(self.browseFile)
        input_file_layout.addWidget(self.input_file_display)
        input_file_layout.addWidget(self.browse_button)
        left_layout.addWidget(self.input_file_label)
        left_layout.addLayout(input_file_layout)

        # Right column layout
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(5, 10, 5, 10)

        # API Key Management Group
        api_key_group = QGroupBox("API Key Management")
        api_key_layout = QVBoxLayout()
        api_key_layout.setSpacing(10)
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
        right_layout.addWidget(api_key_group)

        # Advanced Settings Group
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QVBoxLayout()
        advanced_layout.setSpacing(5)
        advanced_layout.setContentsMargins(10, 5, 10, 5)
        
        lines_input_layout = QHBoxLayout()
        lines_input_layout.setSpacing(5)
        lines_input_layout.setContentsMargins(0, 5, 0, 5)
        
        self.batch_size_label = QLabel('Lines per Batch:')
        self.batch_size_input = QLineEdit()
        self.batch_size_input.setFixedWidth(70)
        self.batch_size_input.setText('300')
        lines_input_layout.addWidget(self.batch_size_label)
        lines_input_layout.addWidget(self.batch_size_input)

        self.start_line_label = QLabel('Start Line:')
        self.start_line_input = QLineEdit()
        self.start_line_input.setFixedWidth(70)
        self.start_line_input.setText('1')
        lines_input_layout.addWidget(self.start_line_label)
        lines_input_layout.addWidget(self.start_line_input)
        
        advanced_layout.addLayout(lines_input_layout)
        
        checkbox1_layout = QHBoxLayout()
        checkbox1_layout.setSpacing(5)
        checkbox1_layout.setContentsMargins(0, 5, 0, 5)
        
        self.skip_upgrade_checkbox = QCheckBox('Skip Upgrade')
        self.skip_upgrade_checkbox.setChecked(False)
        checkbox1_layout.addWidget(self.skip_upgrade_checkbox)

        self.use_colors_checkbox = QCheckBox('Use Colors')
        self.use_colors_checkbox.setChecked(True)
        checkbox1_layout.addWidget(self.use_colors_checkbox)
        
        advanced_layout.addLayout(checkbox1_layout)
        
        checkbox2_layout = QHBoxLayout()
        checkbox2_layout.setSpacing(5)
        checkbox2_layout.setContentsMargins(0, 5, 0, 5)

        self.free_quota_checkbox = QCheckBox('Free Quota')
        self.free_quota_checkbox.setChecked(True)
        checkbox2_layout.addWidget(self.free_quota_checkbox)
        
        self.progress_log_checkbox = QCheckBox('Progress log')
        self.progress_log_checkbox.setChecked(False)
        checkbox2_layout.addWidget(self.progress_log_checkbox)
        
        advanced_layout.addLayout(checkbox2_layout)
        
        checkbox3_layout = QHBoxLayout()
        checkbox3_layout.setSpacing(5)
        checkbox3_layout.setContentsMargins(0, 5, 0, 5)

        self.streaming_checkbox = QCheckBox('Enable streaming')
        self.streaming_checkbox.setChecked(True)
        checkbox3_layout.addWidget(self.streaming_checkbox)

        self.thoughts_log_checkbox = QCheckBox('Thoughts log')
        self.thoughts_log_checkbox.setChecked(False)
        checkbox3_layout.addWidget(self.thoughts_log_checkbox)
        
        advanced_layout.addLayout(checkbox3_layout)

        advanced_group.setLayout(advanced_layout)
        right_layout.addWidget(advanced_group)

        # Create buttons
        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.saveSettings)
        
        self.run_button = QPushButton('Run')
        self.run_button.clicked.connect(self.runTranslation)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.run_button)
        
        right_layout.addLayout(button_layout)

        # Add left and right layouts to columns layout
        columns_layout.addLayout(left_layout)
        columns_layout.addLayout(right_layout)

        # Add columns layout to main layout
        main_layout.addLayout(columns_layout)
        
        # Add line separator
        line_separator = QFrame()
        line_separator.setFrameShape(QFrame.Shape.HLine)
        line_separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line_separator)

        # Add footer
        footer_label = QLabel("Made by e6on")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer_label)

        # Set main layout
        self.setLayout(main_layout)
        
    def browseFile(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Input File", "", "SRT Files (*.srt);;All Files (*)")
        if file_name:
            self.input_file_display.setText(file_name)
    
    def populateModels(self):
        if not self.api_key_input.text():
            QMessageBox.warning(self, "Error", "Please enter the Gemini API Key.")
            return
        
        import gemini_srt_translator as gst
        
        gst.gemini_api_key = self.api_key_input.text()
        
        # Capture the printed output
        buffer = io.StringIO()
        sys.stdout = buffer
        gst.listmodels()
        sys.stdout = sys.__stdout__
        
        models = buffer.getvalue().strip().split('\n')
        
        if models:
            self.model_name_combo.clear()
            self.model_name_combo.addItems(models)
        else:
            QMessageBox.warning(self, "Error", "Failed to retrieve models. Please check your API key and try again.")
        
    def saveSettings(self):
        settings = {
            'api_key': self.api_key_input.text(),
            'api_key2': self.api_key2_input.text(),
            'description': self.description_input.toPlainText(),
            'batch_size': self.batch_size_input.text(),
            'target_language': self.target_language_combo.currentText(),
            'model_name': self.model_name_combo.currentText(),
            'start_line': self.start_line_input.text(),
            'temperature': self.temperature_input.text(),
            'top_p': self.top_p_input.text(),
            'thinking_budget': self.thinking_budget_input.text(),
            'thinking': self.thinking_checkbox.isChecked(),
            'top_k': self.top_k_input.text(),
            'skip_upgrade': self.skip_upgrade_checkbox.isChecked(),
            'streaming': self.streaming_checkbox.isChecked(),
            'progress_log': self.progress_log_checkbox.isChecked(),
            'thoughts_log': self.thoughts_log_checkbox.isChecked(),
            'use_colors': self.use_colors_checkbox.isChecked(),
            'free_quota': self.free_quota_checkbox.isChecked()
        }
        
        save_settings(settings)
        
    def loadSettings(self):
        settings = load_settings()
        
        if settings:
            self.api_key_input.setText(settings.get('api_key', ''))
            self.api_key2_input.setText(settings.get('api_key2', ''))
            self.description_input.setPlainText(settings.get('description', ''))
            self.batch_size_input.setText(settings.get('batch_size', '300'))
            self.target_language_combo.setCurrentText(settings.get('target_language', 'Estonia'))
            self.model_name_combo.setCurrentText(settings.get('model_name', 'gemini-2.0-flash'))
            self.start_line_input.setText(settings.get('start_line', '1'))
            self.temperature_input.setText(settings.get('temperature', ''))
            self.top_p_input.setText(settings.get('top_p', ''))
            self.thinking_budget_input.setText(settings.get('thinking_budget', '2048'))
            self.thinking_checkbox.setChecked(settings.get('thinking', True))
            self.top_k_input.setText(settings.get('top_k', ''))
            self.skip_upgrade_checkbox.setChecked(settings.get('skip_upgrade', False))
            self.streaming_checkbox.setChecked(settings.get('streaming', True))
            self.progress_log_checkbox.setChecked(settings.get('progress_log', False))
            self.thoughts_log_checkbox.setChecked(settings.get('thoughts_log', False))
            self.use_colors_checkbox.setChecked(settings.get('use_colors', True))
            self.free_quota_checkbox.setChecked(settings.get('free_quota', True))
    
    def runTranslation(self):
        if not self.api_key_input.text():
            QMessageBox.warning(self, "Error", "Please enter the Gemini API Key.")
            return
        if not self.batch_size_input.text():
            QMessageBox.warning(self, "Error", "Please enter the Batch Size.")
            return
        if not self.target_language_combo.currentText():
            QMessageBox.warning(self, "Error", "Please select the Target Language.")
            return
        if not self.input_file_display.text():
            QMessageBox.warning(self, "Error", "Please select the Input File.")
            return
        if not self.model_name_combo.currentText():
            QMessageBox.warning(self, "Error", "Please select the Model Name.")
            return
        if not self.start_line_input.text():
            QMessageBox.warning(self, "Error", "Please enter the Start Line.")
            return

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

        # Mandatory numeric fields (already checked for non-empty)
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
        
        # Optional numeric parameters: only set if input is not empty
        temperature_text = self.temperature_input.text()
        if temperature_text:
            try:
                gst.temperature = float(temperature_text)
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"Temperature must be a valid number (e.g., 0.7). You entered: '{temperature_text}'")
                return
        
        top_p_text = self.top_p_input.text()
        if top_p_text:
            try:
                gst.top_p = float(top_p_text)
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"Nucleus sampling (Top P) must be a valid number (e.g., 0.9). You entered: '{top_p_text}'")
                return

        thinking_budget_text = self.thinking_budget_input.text()
        if thinking_budget_text:
            try:
                gst.thinking_budget = int(thinking_budget_text)
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"Thinking budget must be a valid integer. You entered: '{thinking_budget_text}'")
                return

        top_k_text = self.top_k_input.text()
        if top_k_text:
            try:
                gst.top_k = int(top_k_text)
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"Top-K sampling must be a valid integer (e.g., 40). You entered: '{top_k_text}'")
                return

        # gst.batch_size = int(self.batch_size_input.text())
        # gst.start_line = int(self.start_line_input.text())
        # gst.temperature = float(self.temperature_input.text())
        # gst.top_p = float(self.top_p_input.text())
        # gst.thinking_budget = int(self.thinking_budget_input.text())
        gst.thinking = self.thinking_checkbox.isChecked()
        # gst.top_k = int(self.top_k_input.text())
        gst.skip_upgrade = self.skip_upgrade_checkbox.isChecked()
        gst.streaming = self.streaming_checkbox.isChecked()
        gst.progress_log = self.progress_log_checkbox.isChecked()
        gst.thoughts_log = self.thoughts_log_checkbox.isChecked()
        gst.use_colors = self.use_colors_checkbox.isChecked()
        gst.free_quota = self.free_quota_checkbox.isChecked()
        gst.translate()

        QMessageBox.information(self, "Success", "Translation completed successfully!")
if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = TranslatorGUI()
    gui.show()
    sys.exit(app.exec())