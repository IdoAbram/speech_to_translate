"""A consistent dark desktop theme with readable lyric cards."""

STYLESHEET = """
QLabel#hero { font-size: 36px; font-weight: 600; }
QWidget#textPanel QTextEdit { font-size: 18px; }
QMainWindow, QWidget#workspace {
    background: #101827;
    color: #edf3fc;
    }
QWidget {
    color: #edf3fc;
    font-family: 'Segoe UI';
    font-size: 14px;
    }
QLabel {
    background: transparent;
    }
QLabel#eyebrow {
    color: #77ddc6;
    font-size: 12px;
    font-weight: 700;
    }
QLabel#subtitle, QLabel#elapsed {
    color: #a5b6d0;
    }
QPushButton, QToolButton {
    background: #23344d;
    border: 1px solid #344963;
    border-radius: 10px;
    padding: 10px 18px;
    color: #edf3fc;
}
QPushButton:hover, QToolButton:hover {
    background: #304761;
    border-color: #77ddc6;
    }
QPushButton:pressed {
    background: #395574;
    }
QPushButton:disabled, QComboBox:disabled {
    color: #8291a8;
    border-color: #29364a;
    }
QPushButton:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid #77ddc6;
    }
QPushButton#primary {
    background: #77ddc6;
    color: #102f2a;
    font-weight: 700;
    border: 0;
    }
QPushButton#primary:hover {
    background: #9aebd9;
    }
QPushButton#primary:disabled {
    background: #345851;
    color: #a2b6b1;
    }
QPushButton#dropArea {
    background: #192b3d;
    border: 2px dashed #46627d;
    border-radius: 20px;
    color: #dceaf9;
    font-size: 18px;
    padding: 24px;
}
QPushButton#dropArea:hover {
    background: #20394a;
    border-color: #77ddc6;
    }
QComboBox {
    background: #1b2a40;
    border: 1px solid #3c506a;
    border-radius: 9px;
    padding: 9px 14px;
    min-width: 125px;
}
QComboBox::drop-down {
    border: none;
    width: 26px;
    }
QComboBox QAbstractItemView {
    background: #23344d;
    selection-background-color: #386758;
    }
QWidget#textPanel {
    background: #19253a;
    border: 1px solid #2e405b;
    border-radius: 16px;
    }
QLabel#panelTitle {
    color: #c8d7ed;
    font-weight: 600;
    }
QTextEdit {
    background: #19253a;
    border: 1px solid transparent;
    border-radius: 10px;
    selection-background-color: #316b66;
    padding: 14px;
    color: #f1f5fc;
    }
QProgressBar {
    background: #23344d;
    border: none;
    border-radius: 6px;
    min-height: 12px;
    max-height: 12px;
    }
QProgressBar::chunk {
    background: #77ddc6;
    border-radius: 6px;
    }
QScrollBar:vertical {
    background: #19253a;
    width: 12px;
    border: none;
    }
QScrollBar::handle:vertical {
    background: #46607d;
    border-radius: 6px;
    min-height: 30px;
    }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    }
QSplitter::handle {
    background: #101827;
    width: 16px;
    }
QToolTip {
    background: #23344d;
    color: #edf3fc;
    border: 1px solid #46627d;
    padding: 6px;
    }
"""
