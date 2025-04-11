import sys
import os
import json
import io
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
        header_label = QLabel("Gemini SRT Translator GUI")
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
        self.description_input.setMaximumHeight(80)
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
        self.model_name_combo.setFixedWidth(180)
        self.populate_models_button = QPushButton('List Models')
        self.populate_models_button.clicked.connect(self.populateModels)
        model_layout.addWidget(self.model_name_label)
        model_layout.addWidget(self.model_name_combo)
        model_layout.addWidget(self.populate_models_button)
        translation_layout.addLayout(model_layout)

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
        
        input_layout = QHBoxLayout()
        input_layout.setSpacing(5)
        input_layout.setContentsMargins(0, 5, 0, 5)
        
        self.batch_size_label = QLabel('Lines per Batch:')
        self.batch_size_input = QLineEdit()
        self.batch_size_input.setFixedWidth(70)
        self.batch_size_input.setText('30')
        input_layout.addWidget(self.batch_size_label)
        input_layout.addWidget(self.batch_size_input)

        self.start_line_label = QLabel('Start Line:')
        self.start_line_input = QLineEdit()
        self.start_line_input.setFixedWidth(70)
        self.start_line_input.setText('1')
        input_layout.addWidget(self.start_line_label)
        input_layout.addWidget(self.start_line_input)
        
        advanced_layout.addLayout(input_layout)
        
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setSpacing(5)
        checkbox_layout.setContentsMargins(0, 5, 0, 5)
        
        self.free_quota_checkbox = QCheckBox('Free Quota')
        self.free_quota_checkbox.setChecked(True)
        checkbox_layout.addWidget(self.free_quota_checkbox)

        self.use_colors_checkbox = QCheckBox('Use Colors')
        self.use_colors_checkbox.setChecked(True)
        checkbox_layout.addWidget(self.use_colors_checkbox)

        self.skip_upgrade_checkbox = QCheckBox('Skip Upgrade')
        self.skip_upgrade_checkbox.setChecked(False)
        checkbox_layout.addWidget(self.skip_upgrade_checkbox)
        
        advanced_layout.addLayout(checkbox_layout)

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
        footer_label = QLabel("Made with ❤️ by e6on")
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
            'skip_upgrade': self.skip_upgrade_checkbox.isChecked(),
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
            self.batch_size_input.setText(settings.get('batch_size', '30'))
            self.target_language_combo.setCurrentText(settings.get('target_language', 'Estonia'))
            self.model_name_combo.setCurrentText(settings.get('model_name', 'gemini-2.0-flash'))
            self.start_line_input.setText(settings.get('start_line', '1'))
            self.skip_upgrade_checkbox.setChecked(settings.get('skip_upgrade', False))
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
        
        gst.gemini_api_key = self.api_key_input.text()
        gst.gemini_api_key2 = self.api_key2_input.text()
        
        gst.target_language = self.target_language_combo.currentText()
        
        input_file = self.input_file_display.text()
        
        gst.input_file = input_file
        
        gst.output_file = f"{os.path.splitext(input_file)[0]}_translated.srt"
        
        gst.description = self.description_input.toPlainText()
        
        gst.model_name = self.model_name_combo.currentText()
        
        gst.batch_size = int(self.batch_size_input.text())
        
        gst.start_line = int(self.start_line_input.text())
        
        gst.skip_upgrade = self.skip_upgrade_checkbox.isChecked()
        
        gst.use_colors = self.use_colors_checkbox.isChecked()
        
        gst.free_quota = self.free_quota_checkbox.isChecked()
        
        gst.translate()

        QMessageBox.information(self, "Success", "Translation completed successfully!")
if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = TranslatorGUI()
    gui.show()
    sys.exit(app.exec())