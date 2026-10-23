"""A calm, light theme: cream background, white cards, one warm accent."""

CREAM = "#FAF9F5"
INK = "#141413"
MUTED = "#5E5D59"
LINE = "#DCD8CB"
BORDER = "#CDC8B9"
ACCENT = "#B4532D"
ACCENT_DARK = "#7A3418"
ACCENT_SOFT = "#F8E9E1"

STYLESHEET = f"""
QMainWindow, QWidget#workspace, QDialog {{
    background: {CREAM};
    }}
QWidget {{
    color: {INK};
    font-family: 'Segoe UI';
    font-size: 18px;
    }}
QLabel {{
    background: transparent;
    }}
QLabel#appName {{
    font-size: 24px;
    font-weight: 700;
    }}
QLabel#muted, QLabel#caption {{
    color: {MUTED};
    }}
QLabel#caption {{
    font-size: 15px;
    }}
QLabel#songName {{
    font-size: 24px;
    font-weight: 700;
    }}
QLabel#songCaption {{
    color: {MUTED};
    font-size: 20px;
    }}
QFrame#divider {{
    background: {LINE};
    border: 0;
    }}
QLabel#bigTitle {{
    font-size: 38px;
    font-weight: 700;
    }}
QLabel#settingsHeading {{
    font-size: 20px;
    font-weight: 700;
    }}
QLabel#hint {{
    color: #3D3D3A;
    font-size: 16px;
    }}
QLabel#musicIcon {{
    background: {ACCENT_SOFT};
    color: {ACCENT};
    border-radius: 18px;
    font-size: 30px;
    }}
QFrame#card {{
    background: #FFFFFF;
    border: 2px solid {LINE};
    border-radius: 20px;
    }}
QPushButton {{
    background: #FFFFFF;
    border: 2px solid {BORDER};
    border-radius: 10px;
    padding: 9px 16px;
    min-height: 26px;
    color: {INK};
    font-size: 16px;
    }}
QPushButton:hover {{
    border-color: {ACCENT};
    }}
QPushButton:pressed {{
    background: {ACCENT_SOFT};
    }}
QPushButton:disabled {{
    color: #A8A69E;
    border-color: #ECEAE2;
    }}
QPushButton#primary {{
    background: {ACCENT};
    border: 0;
    color: #FFFFFF;
    font-size: 20px;
    font-weight: 700;
    padding: 12px 30px;
    border-radius: 12px;
    }}
QPushButton#primary:hover {{
    background: #9E4626;
    }}
QPushButton#primary:disabled {{
    background: #D9B8A6;
    }}
QPushButton#bigPrimary {{
    background: {ACCENT};
    border: 0;
    color: #FFFFFF;
    font-size: 30px;
    font-weight: 700;
    min-height: 56px;
    min-width: 300px;
    padding: 10px 40px;
    border-radius: 18px;
    }}
QPushButton#bigPrimary:hover {{
    background: #9E4626;
    }}
QPushButton#newSong {{
    border: 2px solid {ACCENT};
    color: {ACCENT_DARK};
    font-weight: 700;
    font-size: 18px;
    }}
QPushButton#quiet {{
    background: transparent;
    color: {MUTED};
    }}
QWidget#segment {{
    background: #F0EEE6;
    border: 2px solid {LINE};
    border-radius: 13px;
    }}
QPushButton#segmentButton {{
    background: transparent;
    border: 2px solid transparent;
    border-radius: 9px;
    color: #3D3D3A;
    font-size: 18px;
    padding: 9px 16px;
    }}
QPushButton#segmentButton:checked {{
    background: {ACCENT_SOFT};
    border: 2px solid {ACCENT};
    color: {ACCENT_DARK};
    font-weight: 700;
    }}
QPushButton#segmentButton:hover {{
    color: {ACCENT_DARK};
    border-color: #E2C3B2;
    }}
QPushButton#segmentButton:checked:hover {{
    border-color: {ACCENT};
    }}
QPushButton#dropArea {{
    background: #FFFFFF;
    border: 3px dashed #D9B8A6;
    border-radius: 28px;
    min-height: 340px;
    }}
QPushButton#dropArea:hover {{
    border-color: {ACCENT};
    background: #FFFDFB;
    }}
QLabel#status {{
    border-radius: 12px;
    padding: 10px 16px;
    font-size: 17px;
    background: #F0EEE6;
    color: #3D3D3A;
    }}
QLabel#status {{
    border: 2px solid #E2DED2;
    }}
QLabel#status[kind="success"] {{
    background: #E9F2E3;
    border-color: #BFD7AE;
    color: #2D5016;
    }}
QLabel#status[kind="warning"] {{
    background: #FBF0D9;
    border-color: #EBCF95;
    color: #6B4A0E;
    }}
QLabel#status[kind="error"] {{
    background: #FBE4E1;
    border-color: #EBB4AC;
    color: #8A1F11;
    }}
QProgressBar {{
    background: #F0EEE6;
    border: none;
    border-radius: 14px;
    min-height: 28px;
    max-height: 28px;
    }}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 14px;
    }}
QLabel#stepDone {{
    color: #2D5016;
    font-size: 21px;
    }}
QLabel#stepNow {{
    font-size: 21px;
    font-weight: 700;
    }}
QLabel#stepLater {{
    color: #8C8A82;
    font-size: 21px;
    }}
QTextEdit {{
    background: #FFFFFF;
    border: 2px solid #E6E2D6;
    border-radius: 12px;
    padding: 8px 6px;
    color: {INK};
    selection-background-color: {ACCENT_SOFT};
    selection-color: {INK};
    }}
QTextEdit:focus {{
    border-color: {ACCENT};
    }}
QLineEdit {{
    background: #FFFFFF;
    border: 2px solid {BORDER};
    border-radius: 10px;
    padding: 9px 14px;
    min-width: 360px;
    }}
QCheckBox#switch {{
    font-size: 20px;
    font-weight: 700;
    spacing: 14px;
    }}
QCheckBox#switch::indicator {{
    width: 52px;
    height: 28px;
    border-radius: 14px;
    background: #B9B6AC;
    }}
QCheckBox#switch::indicator:checked {{
    background: #2D7A4F;
    }}
QScrollBar:vertical {{
    background: transparent;
    width: 12px;
    border: none;
    }}
QScrollBar::handle:vertical {{
    background: #D6D3C8;
    border-radius: 6px;
    min-height: 30px;
    }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    }}
QToolTip {{
    background: #FFFFFF;
    color: {INK};
    border: 1px solid {LINE};
    padding: 6px;
    }}
"""
