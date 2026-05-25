import sys
import os
import json
import io
import importlib.metadata
import tempfile
import contextlib
from pathlib import Path
from typing import Dict, Any
import multiprocessing

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QGroupBox, QFrame, QListWidget, QTabWidget
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

# --- Constants ---
# Reverted: store settings next to the script (original behavior)
SETTINGS_FILE = Path(__file__).resolve().parent / "settings.json"

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
KEY_INPUT_FILES = 'input_files'
KEY_VIDEO_FILE = 'video_file'
KEY_AUDIO_FILE = 'audio_file'
KEY_EXTRACT_AUDIO = 'extract_audio'
KEY_QUIET_MODE = 'quiet_mode'
KEY_RESUME = 'resume'
KEY_CONTEXT_FILES_VISIBLE = 'context_files_visible'
KEY_ISOLATE_VOICE = 'isolate_voice'
KEY_AUDIO_CHUNK_SIZE = 'audio_chunk_size'
KEY_THINKING_LEVEL = 'thinking_level'
KEY_TOKEN_STATS = 'token_stats'
KEY_PRESERVE_CONTEXT = 'preserve_context'

# Deprecated key for migration
KEY_INPUT_FILE = 'input_file'

DEFAULT_SETTINGS = {
    KEY_API_KEY: '',
    KEY_API_KEY2: '',
    KEY_DESCRIPTION: '',
    KEY_BATCH_SIZE: '300',
    KEY_TARGET_LANGUAGE: 'Estonian',
    KEY_MODEL_NAME: 'gemini-2.5-flash',
    KEY_START_LINE: '1',
    KEY_TEMPERATURE: '0.7',
    KEY_TOP_P: '0.95',
    KEY_THINKING_BUDGET: '4096',
    KEY_THINKING: True,
    KEY_TOP_K: '20',
    KEY_SKIP_UPGRADE: False,
    KEY_STREAMING: True,
    KEY_PROGRESS_LOG: False,
    KEY_THOUGHTS_LOG: False,
    KEY_USE_COLORS: True,
    KEY_FREE_QUOTA: True,
    KEY_INPUT_FILES: [],
    KEY_VIDEO_FILE: '',
    KEY_AUDIO_FILE: '',
    KEY_EXTRACT_AUDIO: False,
    KEY_QUIET_MODE: False,
    KEY_RESUME: True,
    KEY_CONTEXT_FILES_VISIBLE: False,
    KEY_ISOLATE_VOICE: True,
    KEY_AUDIO_CHUNK_SIZE: '600',
    KEY_THINKING_LEVEL: 'medium',
    KEY_TOKEN_STATS: False,
    KEY_PRESERVE_CONTEXT: True,
}

# UI Literals
APP_TITLE = "Gemini SRT Translator v3 GUI"
MODEL_NAME_COMBO_WIDTH = 280
NUMERIC_INPUT_FIXED_WIDTH = 70
BATCH_LINE_INPUT_FIXED_WIDTH = 70
DESCRIPTION_MAX_HEIGHT = 90
SUPPORTED_LANGUAGES = [
    "Albanian", "Belarusian", "Bosnian", "Bulgarian", "Catalan", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Finnish", "French", "Galician", "German", "Greek", "Hungarian", "Icelandic", "Irish", "Italian", "Latvian", "Lithuanian", "Luxembourgish", "Macedonian", "Maltese", "Norwegian", "Polish", "Portuguese", "Romanian", "Russian", "Scots Gaelic", "Serbian", "Slovak", "Slovenian", "Spanish", "Swedish", "Ukrainian", "Welsh", "Yiddish"
]

# Function to save settings to a file (atomic)
def save_settings(settings: Dict[str, Any]):
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Write to a temp file first then atomically replace
        with tempfile.NamedTemporaryFile('w', delete=False, dir=str(SETTINGS_FILE.parent), encoding='utf-8') as tf:
            json.dump(settings, tf, indent=4, ensure_ascii=False)
            tempname = tf.name
        os.replace(tempname, SETTINGS_FILE)
    except Exception as e:
        raise

# Function to load settings from a file
def load_settings() -> Dict[str, Any]:
    if SETTINGS_FILE.exists():
        try:
            with SETTINGS_FILE.open('r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
            # --- Migration from old settings format ---
            if isinstance(loaded_settings, dict):
                if KEY_INPUT_FILE in loaded_settings and loaded_settings.get(KEY_INPUT_FILE):
                    if KEY_INPUT_FILES not in loaded_settings or not isinstance(loaded_settings.get(KEY_INPUT_FILES), list):
                        loaded_settings[KEY_INPUT_FILES] = []
                    # Add the old file to the list if it's not already there
                    if loaded_settings[KEY_INPUT_FILE] not in loaded_settings[KEY_INPUT_FILES]:
                        loaded_settings[KEY_INPUT_FILES].insert(0, loaded_settings[KEY_INPUT_FILE])
                # Remove deprecated key
                loaded_settings.pop(KEY_INPUT_FILE, None)
            else:
                return DEFAULT_SETTINGS.copy()
            # Merge with defaults to ensure all keys present
            settings = DEFAULT_SETTINGS.copy()
            settings.update(loaded_settings)
            # Ensure mutable defaults are copies
            settings[KEY_INPUT_FILES] = list(settings.get(KEY_INPUT_FILES) or [])
            # Enforce types for common boolean fields (in case JSON saved strings)
            for bool_key in [KEY_THINKING, KEY_SKIP_UPGRADE, KEY_STREAMING, KEY_PROGRESS_LOG, KEY_THOUGHTS_LOG, KEY_USE_COLORS, KEY_FREE_QUOTA, KEY_EXTRACT_AUDIO, KEY_QUIET_MODE, KEY_RESUME, KEY_CONTEXT_FILES_VISIBLE, KEY_ISOLATE_VOICE, KEY_TOKEN_STATS, KEY_PRESERVE_CONTEXT]:
                if isinstance(settings.get(bool_key), str):
                    settings[bool_key] = settings[bool_key].lower() in ('1', 'true', 'yes', 'on')
            return settings
        except json.JSONDecodeError:
            return DEFAULT_SETTINGS.copy()
        except Exception:
            return DEFAULT_SETTINGS.copy()
    else:
        return DEFAULT_SETTINGS.copy()

class TranslatorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = load_settings() # Load settings first
        self.initUI()
        self.populate_ui_from_settings() # Then populate UI

    def _create_line_separator(self):
        line_separator = QFrame()
        line_separator.setFrameShape(QFrame.Shape.HLine)
        line_separator.setFrameShadow(QFrame.Shadow.Sunken)
        return line_separator

    def _create_model_context_settings_group(self):
        # Create main layout
        settings_group = QGroupBox("Model & Context Settings")
        translation_layout = QVBoxLayout(settings_group)
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

        self.top_p_label = QLabel('Top P:')
        self.top_p_input = QLineEdit()
        self.top_p_input.setPlaceholderText("0.0-1.0")
        self.top_p_input.setFixedWidth(NUMERIC_INPUT_FIXED_WIDTH)
        model_tuning1_layout.addWidget(self.top_p_label)
        model_tuning1_layout.addWidget(self.top_p_input)

        self.temperature_label = QLabel('Temperature:')
        self.temperature_input = QLineEdit()
        self.temperature_input.setPlaceholderText("0.0-2.0")
        self.temperature_input.setFixedWidth(NUMERIC_INPUT_FIXED_WIDTH)
        model_tuning1_layout.addStretch(1)
        model_tuning1_layout.addWidget(self.temperature_label)
        model_tuning1_layout.addWidget(self.temperature_input)

        translation_layout.addLayout(model_tuning1_layout)

        model_tuning2_layout = QHBoxLayout()
        model_tuning2_layout.setSpacing(5)
        model_tuning2_layout.setContentsMargins(0, 5, 0, 5)

        self.top_k_label = QLabel('Top K:')
        self.top_k_input = QLineEdit()
        self.top_k_input.setPlaceholderText("≥0")
        self.top_k_input.setFixedWidth(NUMERIC_INPUT_FIXED_WIDTH)
        model_tuning2_layout.addWidget(self.top_k_label)
        model_tuning2_layout.addWidget(self.top_k_input)
        
        self.thinking_budget_label = QLabel('Thinking budget:')
        self.thinking_budget_input = QLineEdit()
        self.thinking_budget_input.setPlaceholderText("0-24576")
        self.thinking_budget_input.setFixedWidth(NUMERIC_INPUT_FIXED_WIDTH)
        model_tuning2_layout.addStretch(1)
        model_tuning2_layout.addWidget(self.thinking_budget_label)
        model_tuning2_layout.addWidget(self.thinking_budget_input)
        
        translation_layout.addLayout(model_tuning2_layout)

        tuning_checkbox1_layout = QHBoxLayout()
        tuning_checkbox1_layout.setSpacing(5)
        tuning_checkbox1_layout.setContentsMargins(0, 5, 0, 5)

        self.thinking_level_label = QLabel('Thinking Level:')
        self.thinking_level_combo = QComboBox()
        self.thinking_level_combo.addItems(["minimal", "low", "medium", "high"])
        self.thinking_level_combo.setFixedWidth(100)
        self.thinking_level_combo.setToolTip("Only available for Gemini 3 models")
        self.thinking_level_label.setToolTip("Only available for Gemini 3 models")
        tuning_checkbox1_layout.addWidget(self.thinking_level_label)
        tuning_checkbox1_layout.addWidget(self.thinking_level_combo)

        self.thinking_checkbox = QCheckBox('Enable thinking')
        tuning_checkbox1_layout.addStretch(1)
        tuning_checkbox1_layout.addWidget(self.thinking_checkbox)
        translation_layout.addLayout(tuning_checkbox1_layout)

        return settings_group

    def _create_input_file_controls_group(self):
        input_file_group = QGroupBox("Translation Queue")
        input_file_main_layout = QVBoxLayout()
        input_file_main_layout.setSpacing(5)
        input_file_main_layout.setContentsMargins(10, 5, 10, 5)

        # Use custom FileListWidget that accepts drag & drop of .srt files
        self.file_list_widget = FileListWidget()

        buttons_layout = QHBoxLayout()
        self.add_files_button = QPushButton("Add Files")
        self.add_files_button.clicked.connect(self.addFiles)
        self.remove_files_button = QPushButton("Remove Selected")
        self.remove_files_button.clicked.connect(self.removeSelectedFiles)
        self.clear_files_button = QPushButton("Clear All")
        self.clear_files_button.clicked.connect(self.clearFiles)

        buttons_layout.addWidget(self.add_files_button)
        buttons_layout.addWidget(self.remove_files_button)
        buttons_layout.addWidget(self.clear_files_button)

        input_file_main_layout.addWidget(self.file_list_widget)
        input_file_main_layout.addLayout(buttons_layout)
        input_file_group.setLayout(input_file_main_layout)
        return input_file_group

    def _create_contextual_input_files_group(self):
        self.contextual_input_files_group = QGroupBox("Contextual Input Files (Optional)")
        self.contextual_input_files_group.setCheckable(True) # Make it checkable/collapsible

        # Make the checkbox indicator bigger using style sheet
        self.contextual_input_files_group.setStyleSheet("QGroupBox::indicator { width: 20px; height: 20px; }")
        # Create a container widget for all the actual content elements
        self.context_content_area_widget = QWidget()

        # Layout for the container widget (self.context_content_area_widget)
        content_elements_layout = QVBoxLayout(self.context_content_area_widget)
        content_elements_layout.setSpacing(5)
        # These margins are for the elements within the content_content_area_widget.
        content_elements_layout.setContentsMargins(10, 5, 10, 5) # Original content margins

        extract_audio_layout = QHBoxLayout()
        extract_audio_layout.setSpacing(15)
        extract_audio_layout.setContentsMargins(0, 5, 0, 5)
        
        self.audio_chunk_size_label = QLabel('Audio Chunk (s):')
        self.audio_chunk_size_input = QLineEdit()
        self.audio_chunk_size_input.setFixedWidth(NUMERIC_INPUT_FIXED_WIDTH)
        self.audio_chunk_size_input.setPlaceholderText("600")
        extract_audio_layout.addWidget(self.audio_chunk_size_label)
        extract_audio_layout.addWidget(self.audio_chunk_size_input)

        extract_audio_layout.addStretch(1) # Add stretch to push checkbox to the right
        self.isolate_voice_checkbox = QCheckBox('Isolate Voice')
        extract_audio_layout.addWidget(self.isolate_voice_checkbox)
        self.extract_audio_checkbox = QCheckBox('Extract audio from video')
        extract_audio_layout.addWidget(self.extract_audio_checkbox)
        content_elements_layout.addLayout(extract_audio_layout)

        # Video File
        self.video_file_label = QLabel('Video File (for context):')
        video_file_layout = QHBoxLayout()
        video_file_layout.setSpacing(5)
        video_file_layout.setContentsMargins(0, 5, 0, 5)
        self.video_file_display = QLineEdit()
        self.video_file_display.setReadOnly(True)
        self.browse_video_button = QPushButton('Browse Video')
        self.browse_video_button.clicked.connect(self.browseVideoFile)
        video_file_layout.addWidget(self.video_file_display)
        video_file_layout.addWidget(self.browse_video_button)
        content_elements_layout.addWidget(self.video_file_label)
        content_elements_layout.addLayout(video_file_layout)

        # Extraction Buttons (SRT/Audio from Video)
        extraction_layout = QHBoxLayout()
        self.extract_srt_button = QPushButton("Extract SRT")
        self.extract_srt_button.clicked.connect(lambda: self.runExtraction("srt"))
        self.extract_audio_button = QPushButton("Extract Audio")
        self.extract_audio_button.clicked.connect(lambda: self.runExtraction("audio"))
        extraction_layout.addWidget(self.extract_srt_button)
        extraction_layout.addWidget(self.extract_audio_button)
        content_elements_layout.addLayout(extraction_layout)

        # Audio File
        self.audio_file_label = QLabel('Audio File (for context):')
        audio_file_layout = QHBoxLayout()
        audio_file_layout.setSpacing(5)
        audio_file_layout.setContentsMargins(0, 5, 0, 5)
        self.audio_file_display = QLineEdit()
        self.audio_file_display.setReadOnly(True)
        self.browse_audio_button = QPushButton('Browse Audio')
        self.browse_audio_button.clicked.connect(self.browseAudioFile)
        audio_file_layout.addWidget(self.audio_file_display)
        audio_file_layout.addWidget(self.browse_audio_button)
        content_elements_layout.addWidget(self.audio_file_label)
        content_elements_layout.addLayout(audio_file_layout)

        # Layout for the QGroupBox itself, to hold the context_content_area_widget
        qgroupbox_layout = QVBoxLayout()
        qgroupbox_layout.setContentsMargins(0,0,0,0) # Let QGroupBox style provide outer padding
        qgroupbox_layout.addWidget(self.context_content_area_widget)
        self.contextual_input_files_group.setLayout(qgroupbox_layout)

        self.contextual_input_files_group.toggled.connect(self._toggle_contextual_group_and_resize)
        return self.contextual_input_files_group

    def _toggle_contextual_group_and_resize(self, checked):
        """Handles visibility of contextual group content and resizes the main window."""
        self.context_content_area_widget.setVisible(checked)

        def do_resize_logic():
            # Force the main layout to recalculate its size hints
            self.layout().activate()

            if not checked:  # Collapsed
                self.resize(self.minimumSizeHint())
            else:  # Expanded
                self.adjustSize() # Resize to preferred sizeHint

        QTimer.singleShot(0, do_resize_logic)

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
        self.start_line_input.setPlaceholderText("1")
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

        checkbox4_layout = QHBoxLayout()
        checkbox4_layout.setSpacing(5)
        checkbox4_layout.setContentsMargins(0, 5, 0, 5)

        self.quiet_mode_checkbox = QCheckBox('Quiet Mode')
        checkbox4_layout.addWidget(self.quiet_mode_checkbox)

        self.resume_checkbox = QCheckBox('Auto Resume')
        checkbox4_layout.addWidget(self.resume_checkbox)
        advanced_layout.addLayout(checkbox4_layout)

        checkbox5_layout = QHBoxLayout()
        checkbox5_layout.setSpacing(5)
        checkbox5_layout.setContentsMargins(0, 5, 0, 5)

        self.token_stats_checkbox = QCheckBox('Token Stats')
        self.token_stats_checkbox.setToolTip("Show token usage information after each translation")
        checkbox5_layout.addWidget(self.token_stats_checkbox)

        self.preserve_context_checkbox = QCheckBox('Preserve Context')
        self.preserve_context_checkbox.setToolTip("Preserve context between batches")
        checkbox5_layout.addWidget(self.preserve_context_checkbox)
        advanced_layout.addLayout(checkbox5_layout)

        advanced_group.setLayout(advanced_layout)
        return advanced_group

    def _create_action_buttons_layout(self):
        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.saveSettings)
        
        self.run_button = QPushButton('Run')
        self.run_button.clicked.connect(self.runTranslation)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(10, 10, 10, 0)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.run_button)
        return button_layout

    def _create_footer(self):
        try:
            # Dynamically get the version of the translator package
            gst_version = importlib.metadata.version('gemini-srt-translator')
        except importlib.metadata.PackageNotFoundError:
            gst_version = "N/A" # Fallback if not found

        footer_text = f"gemini-srt-translator v{gst_version}  |  GUI by e6on & AI, 2025"
        footer_label = QLabel(footer_text)
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

        # --- Create Tab Widget ---
        tab_widget = QTabWidget()

        # --- Translation Tab ---
        translation_tab = QWidget()
        translation_layout = QVBoxLayout(translation_tab)
        translation_layout.setSpacing(10)
        translation_layout.setContentsMargins(5, 10, 5, 10)

        translation_layout.addWidget(self._create_input_file_controls_group())
        translation_layout.addWidget(self._create_contextual_input_files_group())
        translation_layout.addStretch(1)

        # --- Settings Tab ---
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_columns_layout = QHBoxLayout()

        # Left column for settings
        settings_left_layout = QVBoxLayout()
        settings_left_layout.setSpacing(0)
        settings_left_layout.setContentsMargins(5, 10, 5, 10)
        settings_left_layout.addWidget(self._create_model_context_settings_group())
        settings_left_layout.addStretch(1)

        # Right column for settings
        settings_right_layout = QVBoxLayout()
        settings_right_layout.setSpacing(0)
        settings_right_layout.setContentsMargins(5, 10, 5, 10)
        settings_right_layout.addWidget(self._create_api_key_group())
        settings_right_layout.addSpacing(10)
        settings_right_layout.addWidget(self._create_advanced_settings_group())
        settings_right_layout.addStretch(1)

        settings_columns_layout.addLayout(settings_left_layout)
        settings_columns_layout.addLayout(settings_right_layout)
        settings_layout.addLayout(settings_columns_layout)

        # --- Add tabs to widget ---
        tab_widget.addTab(translation_tab, "Translation")
        tab_widget.addTab(settings_tab, "Settings")

        # --- Add Tab Widget and global elements to main layout ---
        main_layout.addWidget(tab_widget)
        main_layout.addLayout(self._create_action_buttons_layout())
        main_layout.addWidget(self._create_line_separator())
        main_layout.addWidget(self._create_footer())

        # Set main layout
        self.setLayout(main_layout)

    def addFiles(self):
        file_names, _ = QFileDialog.getOpenFileNames(self, "Select Input File(s)", "", "SRT Files (*.srt);;All Files (*)")
        if file_names:
            current_files = [self.file_list_widget.item(i).text() for i in range(self.file_list_widget.count())]
            for file_name in file_names:
                if file_name not in current_files:
                    self.file_list_widget.addItem(file_name)

    def removeSelectedFiles(self):
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.file_list_widget.takeItem(self.file_list_widget.row(item))

    def clearFiles(self):
        self.file_list_widget.clear()

    def browseVideoFile(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.avi *.mov);;All Files (*)")
        if file_name:
            self.video_file_display.setText(file_name)

    def browseAudioFile(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.mp3 *.wav *.aac *.ogg);;All Files (*)")
        if file_name:
            self.audio_file_display.setText(file_name)

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

        buffer = io.StringIO()
        models = []
        try:
            with contextlib.redirect_stdout(buffer):
                gst.listmodels()
            models_output = buffer.getvalue().strip()
            if models_output:
                models = [model.strip() for model in models_output.split('\n') if model.strip()]
        except Exception as e:
            QMessageBox.critical(self, "Error Listing Models", f"An error occurred while listing models: {e}")
            return

        if models:
            self.model_name_combo.clear()
            self.model_name_combo.addItems(models)
            # Try to set the previously selected/default model
            desired_model = self.settings.get(KEY_MODEL_NAME, DEFAULT_SETTINGS[KEY_MODEL_NAME])
            if desired_model in models:
                self.model_name_combo.setCurrentText(desired_model)
            else:
                # preserve saved model by adding it if not present
                if desired_model:
                    self.model_name_combo.insertItem(0, desired_model)
                    self.model_name_combo.setCurrentIndex(0)
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
            KEY_INPUT_FILES: [self.file_list_widget.item(i).text() for i in range(self.file_list_widget.count())],
            KEY_VIDEO_FILE: self.video_file_display.text(),
            KEY_AUDIO_FILE: self.audio_file_display.text(),
            KEY_EXTRACT_AUDIO: self.extract_audio_checkbox.isChecked(),
            KEY_QUIET_MODE: self.quiet_mode_checkbox.isChecked(),
            KEY_RESUME: self.resume_checkbox.isChecked(),
            KEY_CONTEXT_FILES_VISIBLE: self.contextual_input_files_group.isChecked(),
            KEY_ISOLATE_VOICE: self.isolate_voice_checkbox.isChecked(),
            KEY_AUDIO_CHUNK_SIZE: self.audio_chunk_size_input.text(),
            KEY_THINKING_LEVEL: self.thinking_level_combo.currentText(),
            KEY_TOKEN_STATS: self.token_stats_checkbox.isChecked(),
            KEY_PRESERVE_CONTEXT: self.preserve_context_checkbox.isChecked(),
        }
        try:
            save_settings(current_settings)
            self.settings = current_settings # Update in-memory settings
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save settings: {e}")

    def populate_ui_from_settings(self):
        self.api_key_input.setText(self.settings.get(KEY_API_KEY, ''))
        self.api_key2_input.setText(self.settings.get(KEY_API_KEY2, ''))
        self.description_input.setPlainText(self.settings.get(KEY_DESCRIPTION, ''))
        self.batch_size_input.setText(self.settings.get(KEY_BATCH_SIZE, ''))

        # Set target language, ensuring it's a valid choice
        target_lang = self.settings.get(KEY_TARGET_LANGUAGE, DEFAULT_SETTINGS[KEY_TARGET_LANGUAGE])
        if self.target_language_combo.findText(target_lang) != -1:
            self.target_language_combo.setCurrentText(target_lang)
        elif self.target_language_combo.count() > 0: # Fallback to first item if saved one not found
            self.target_language_combo.setCurrentIndex(0)

        self.start_line_input.setText(self.settings.get(KEY_START_LINE, '1'))
        self.temperature_input.setText(self.settings.get(KEY_TEMPERATURE, '0.7'))
        self.top_p_input.setText(self.settings.get(KEY_TOP_P, '0.95'))
        self.thinking_budget_input.setText(self.settings.get(KEY_THINKING_BUDGET, '4096'))
        self.thinking_checkbox.setChecked(bool(self.settings.get(KEY_THINKING, True)))
        self.top_k_input.setText(self.settings.get(KEY_TOP_K, '20'))
        self.skip_upgrade_checkbox.setChecked(bool(self.settings.get(KEY_SKIP_UPGRADE, False)))
        self.streaming_checkbox.setChecked(bool(self.settings.get(KEY_STREAMING, True)))
        self.progress_log_checkbox.setChecked(bool(self.settings.get(KEY_PROGRESS_LOG, False)))
        self.thoughts_log_checkbox.setChecked(bool(self.settings.get(KEY_THOUGHTS_LOG, False)))
        self.use_colors_checkbox.setChecked(bool(self.settings.get(KEY_USE_COLORS, True)))
        self.free_quota_checkbox.setChecked(bool(self.settings.get(KEY_FREE_QUOTA, True)))
        self.file_list_widget.clear()
        self.file_list_widget.addItems(list(self.settings.get(KEY_INPUT_FILES, [])))
        self.video_file_display.setText(self.settings.get(KEY_VIDEO_FILE, ''))
        self.audio_file_display.setText(self.settings.get(KEY_AUDIO_FILE, ''))
        self.extract_audio_checkbox.setChecked(bool(self.settings.get(KEY_EXTRACT_AUDIO, False)))
        self.quiet_mode_checkbox.setChecked(bool(self.settings.get(KEY_QUIET_MODE, False)))
        self.resume_checkbox.setChecked(bool(self.settings.get(KEY_RESUME, True)))
        self.isolate_voice_checkbox.setChecked(bool(self.settings.get(KEY_ISOLATE_VOICE, True)))
        self.audio_chunk_size_input.setText(self.settings.get(KEY_AUDIO_CHUNK_SIZE, '600'))

        thinking_level = self.settings.get(KEY_THINKING_LEVEL, 'medium')
        if self.thinking_level_combo.findText(thinking_level) != -1:
            self.thinking_level_combo.setCurrentText(thinking_level)
        self.token_stats_checkbox.setChecked(bool(self.settings.get(KEY_TOKEN_STATS, False)))
        self.preserve_context_checkbox.setChecked(bool(self.settings.get(KEY_PRESERVE_CONTEXT, True)))
        
        self.contextual_input_files_group.setChecked(bool(self.settings.get(KEY_CONTEXT_FILES_VISIBLE, False)))
        # Call the toggle method to set visibility and adjust size
        self._toggle_contextual_group_and_resize(bool(self.settings.get(KEY_CONTEXT_FILES_VISIBLE, False)))

        # Automatically populate models on startup if API key is present
        if self.api_key_input.text():
            self.populateModels()

    def runTranslation(self):
        # --- Validation of required fields ---
        required_fields_map = {
            self.api_key_input: "Gemini API Key",
            self.batch_size_input: "Batch Size",
        }
        for widget, name in required_fields_map.items():
            if not widget.text().strip():
                QMessageBox.warning(self, "Input Error", f"{name} is required.")
                return

        if self.file_list_widget.count() == 0:
            QMessageBox.warning(self, "Input Error", "At least one Input File is required in the queue.")
            return
        if not self.target_language_combo.currentText():
            QMessageBox.warning(self, "Input Error", "Target Language must be selected.")
            return
        if not self.model_name_combo.currentText(): # Model might not be in list if not populated yet
            QMessageBox.warning(self, "Input Error", "Model Name must be selected. Try 'List Models' first.")
            return
        # --- End Validation ---

        # Prepare module parameters (same keys as before)
        gst_params = {
            'gemini_api_key': self.api_key_input.text(),
            'gemini_api_key2': self.api_key2_input.text(),
            'target_language': self.target_language_combo.currentText(),
            'description': self.description_input.toPlainText(),
            'model_name': self.model_name_combo.currentText(),
        }

        # Numeric parsing with validation (keeping original behavior)
        try:
            gst_params['batch_size'] = int(self.batch_size_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", f"Batch Size must be a valid integer. You entered: '{self.batch_size_input.text()}'")
            return

        start_line_text = self.start_line_input.text()
        if start_line_text:
            try:
                gst_params['start_line'] = int(start_line_text)
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"Start Line must be a valid integer. You entered: '{start_line_text}'")
                return
        temperature_text = self.temperature_input.text()
        if temperature_text:
            try:
                value = float(temperature_text)
                if not (0.0 <= value <= 2.0):
                    QMessageBox.warning(self, "Input Error", f"Temperature must be between 0.0 and 2.0. You entered: '{value}'")
                    return
                gst_params['temperature'] = value
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
                gst_params['top_p'] = value
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
                gst_params['thinking_budget'] = value
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
                gst_params['top_k'] = value
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"Top-K sampling must be a valid integer (e.g., 40). You entered: '{top_k_text}'")
                return
        
        audio_chunk_size_text = self.audio_chunk_size_input.text()
        if audio_chunk_size_text:
            try:
                value = int(audio_chunk_size_text)
                if value <= 0:
                    QMessageBox.warning(self, "Input Error", f"Audio Chunk Size must be > 0. You entered: '{value}'")
                    return
                gst_params['audio_chunk_size'] = value
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"Audio Chunk Size must be a valid integer. You entered: '{audio_chunk_size_text}'")
                return

        # Booleans and file params
        gst_params['thinking'] = self.thinking_checkbox.isChecked()
        gst_params['skip_upgrade'] = self.skip_upgrade_checkbox.isChecked()
        gst_params['streaming'] = self.streaming_checkbox.isChecked()
        gst_params['progress_log'] = self.progress_log_checkbox.isChecked()
        gst_params['thoughts_log'] = self.thoughts_log_checkbox.isChecked()
        gst_params['use_colors'] = self.use_colors_checkbox.isChecked()
        gst_params['free_quota'] = self.free_quota_checkbox.isChecked()
        gst_params['video_file'] = self.video_file_display.text()
        gst_params['audio_file'] = self.audio_file_display.text()
        gst_params['extract_audio'] = self.extract_audio_checkbox.isChecked()
        gst_params['quiet_mode'] = self.quiet_mode_checkbox.isChecked()
        gst_params['resume'] = self.resume_checkbox.isChecked()
        gst_params['isolate_voice'] = self.isolate_voice_checkbox.isChecked()
        gst_params['thinking_level'] = self.thinking_level_combo.currentText()
        gst_params['token_stats'] = self.token_stats_checkbox.isChecked()
        gst_params['preserve_context'] = self.preserve_context_checkbox.isChecked()

        files_to_translate = [self.file_list_widget.item(i).text() for i in range(self.file_list_widget.count())]
        total_files = len(files_to_translate)
        if total_files == 0:
            QMessageBox.warning(self, "Input Error", "No files to translate.")
            return

        # Disable UI controls while running
        self.run_button.setEnabled(False)
        self.save_button.setEnabled(False)

        # Create and start background thread
        self._translation_thread = TranslationThread(files_to_translate, gst_params)
        self._translation_thread.progress.connect(self._on_translation_progress)
        self._translation_thread.finished_signal.connect(self._on_translation_finished)
        self._translation_thread.start()

    def _on_translation_progress(self, index: int, total: int, filename: str):
        self.setWindowTitle(f"{APP_TITLE} - Translating {index}/{total}: {filename}")
        QApplication.processEvents()

    def _on_translation_finished(self, completed_count: int, total_files: int, errors):
        self.run_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.setWindowTitle(APP_TITLE)

        if not errors:
            QMessageBox.information(self, "Success", f"Translation completed successfully for all {total_files} files!")
        else:
            error_summary = "\n".join(errors)
            QMessageBox.warning(self, "Translation Finished", f"{completed_count} of {total_files} files were processed.\n\nErrors occurred:\n{error_summary}")

    def runExtraction(self, mode):
        video_file = self.video_file_display.text()
        if not video_file or not os.path.exists(video_file):
             QMessageBox.warning(self, "Input Error", "Please select a valid video file first.")
             return
        
        isolate_voice = self.isolate_voice_checkbox.isChecked()
        
        self.extract_srt_button.setEnabled(False)
        self.extract_audio_button.setEnabled(False)
        self.setWindowTitle(f"{APP_TITLE} - Extracting {mode}...")
        
        self._extraction_thread = ExtractionThread(video_file, mode, isolate_voice)
        self._extraction_thread.finished_signal.connect(self._on_extraction_finished)
        self._extraction_thread.start()

    def _on_extraction_finished(self, status, msg):
        self.extract_srt_button.setEnabled(True)
        self.extract_audio_button.setEnabled(True)
        self.setWindowTitle(APP_TITLE)
        
        if status == "ok":
            QMessageBox.information(self, "Extraction Complete", msg)
        else:
            QMessageBox.critical(self, "Extraction Error", msg)

class FileListWidget(QListWidget):
    """QListWidget that accepts dragged files/folders (adds .srt files)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        # Keep selection mode consistent with previous behavior
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            return super().dropEvent(event)

        current_files = [self.item(i).text() for i in range(self.count())]
        added = False

        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if not path:
                continue
            # if a directory is dropped, walk and add .srt files
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for f in files:
                        if f.lower().endswith('.srt'):
                            fp = os.path.join(root, f)
                            if fp not in current_files:
                                self.addItem(fp)
                                current_files.append(fp)
                                added = True
            else:
                if path.lower().endswith('.srt'):
                    if path not in current_files:
                        self.addItem(path)
                        current_files.append(path)
                        added = True

        if added:
            event.acceptProposedAction()
        else:
            event.ignore()

# New helper: run a single translation in a separate process
def _run_translate_worker(params: dict, input_file: str, output_file: str, result_queue: multiprocessing.Queue):
    """
    Worker function executed in a separate process. It imports the gemini_srt_translator
    module, applies params, runs translate() and reports status via result_queue.
    """
    try:
        import importlib
        import gemini_srt_translator as gst
        importlib.reload(gst)
        # Apply provided params (ignore failures)
        for k, v in (params or {}).items():
            try:
                setattr(gst, k, v)
            except Exception:
                pass
        gst.input_file = input_file
        gst.output_file = output_file
        gst.translate()
        result_queue.put(("ok", input_file, ""))
    except Exception as e:
        # Return the exception string to the parent
        result_queue.put(("error", input_file, str(e)))

def _run_extract_worker(video_file: str, mode: str, isolate_voice: bool, result_queue: multiprocessing.Queue):
    """
    Worker function for extracting SRT or Audio from video.
    """
    try:
        import importlib
        import gemini_srt_translator as gst
        importlib.reload(gst)
        gst.video_file = video_file
        gst.isolate_voice = isolate_voice
        gst.extract(mode)
        result_queue.put(("ok", f"Extracted {mode} successfully."))
    except Exception as e:
        result_queue.put(("error", str(e)))

# Replace TranslationThread to use multiprocessing per-file worker
class TranslationThread(QThread):
    # emits: current_index, total_files, filename
    progress = pyqtSignal(int, int, str)
    # emits: completed_count, total_files, errors (list)
    finished_signal = pyqtSignal(int, int, object)

    def __init__(self, files_to_translate: list, gst_params: dict):
        super().__init__()
        self.files = files_to_translate
        self.params = gst_params

    def run(self):
        ctx = multiprocessing.get_context('spawn')
        total = len(self.files)
        errors = []
        completed = 0

        for idx, input_file in enumerate(self.files, start=1):
            self.progress.emit(idx, total, os.path.basename(input_file))

            output_file = f"{os.path.splitext(input_file)[0]}_translated.srt"
            result_queue = ctx.Queue()

            p = ctx.Process(target=_run_translate_worker, args=(self.params, input_file, output_file, result_queue))
            p.start()
            p.join()  # wait for process to finish

            # attempt to get result (guarded)
            try:
                status, fname, msg = result_queue.get_nowait()
            except Exception:
                status, fname, msg = ("error", input_file, "No result returned from worker process")

            if status == "ok":
                completed += 1
            else:
                errors.append(f"Failed to translate {os.path.basename(input_file)}: {msg}")

        self.finished_signal.emit(completed, total, errors)

class ExtractionThread(QThread):
    finished_signal = pyqtSignal(str, str) # status, message

    def __init__(self, video_file, mode, isolate_voice):
        super().__init__()
        self.video_file = video_file
        self.mode = mode
        self.isolate_voice = isolate_voice

    def run(self):
        ctx = multiprocessing.get_context('spawn')
        result_queue = ctx.Queue()
        p = ctx.Process(target=_run_extract_worker, args=(self.video_file, self.mode, self.isolate_voice, result_queue))
        p.start()
        p.join()
        
        try:
            status, msg = result_queue.get_nowait()
        except Exception:
            status, msg = ("error", "Process finished without result.")
        
        self.finished_signal.emit(status, msg)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QLineEdit { placeholder-text-color: #c9c9c9; }
        QTextEdit { placeholder-text-color: #c9c9c9; }
    """)
    gui = TranslatorGUI()
    gui.show()
    sys.exit(app.exec())