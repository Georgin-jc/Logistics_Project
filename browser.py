import os
from PyQt5 import QtWidgets
from PyQt5.QtCore import QUrl
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    WEB_AVAILABLE = True
except Exception:
    QWebEngineView = None
    WEB_AVAILABLE = False


def build_browser(parent: QtWidgets.QWidget):
    # Use the layout already created by MainWindow
    #layout = parent.layout()
    layout = QtWidgets.QHBoxLayout(parent)
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(10)

    if not WEB_AVAILABLE:
        label = QtWidgets.QLabel("QWebEngine is not available. Install PyQtWebEngine to enable the browser.")
        layout.addWidget(label)
        return

    browser = QWebEngineView()
    layout.addWidget(browser)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "del_track.html")
    browser.load(QUrl.fromLocalFile(file_path))
    



