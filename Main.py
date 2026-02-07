import sys
import threading
import uvicorn
import os

def start_api():
    print("Starting FastAPI backend...")
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=False)

from datetime import datetime
from PyQt5 import QtWidgets, QtGui, QtCore




# Try importing WebEngine for HTML/Leaflet map tabs
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
    WEB_ENGINE_AVAILABLE = True
except Exception:
    QWebEngineView = None
    QWebEngineProfile = None
    WEB_ENGINE_AVAILABLE = False

# Import tab builders
from Calcu import calculator_page
from Team_vis import tile_page
from Adressen import adressen_tab
from browser import build_browser
from GIS_Viewer import gis_tab
from weather import get_weather
from Import_Adressen import update_adressen
from Import_Abo import update_Abonents
from abonenten import abonenten_tab
from Import_Structure import update_Structure
from Structure import Structure_tab
from route_optimizer_tab import RouteOptimizerTab


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("G-Star Logistics")
        self.resize(800, 600)  # Best behavior on Windows DPI

        # =========================
        # CENTRAL WIDGET + MAIN LAYOUT
        # =========================
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central.setLayout(main_layout)

        # =========================
        # HEADER
        # =========================
        header = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(15, 15, 15, 15)
        header_layout.setSpacing(20)
        header.setLayout(header_layout)

        logo = QtWidgets.QLabel()
        pix = QtGui.QPixmap("logo.png")
        if not pix.isNull():
            logo.setPixmap(pix.scaledToHeight(64, QtCore.Qt.SmoothTransformation))
        header_layout.addWidget(logo)

        header_layout.addStretch()

        date_label = QtWidgets.QLabel(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        header_layout.addWidget(date_label)

        weather_label = QtWidgets.QLabel("Weather: Loading...")
        self.weather_timer = QtCore.QTimer()
        self.weather_timer.timeout.connect(
        lambda: weather_label.setText(
                "Weather: " + (get_weather(53.556, 13.261) or "unavailable")
            )
        )
        self.weather_timer.start(600000)  # 10 minutes
        header_layout.addWidget(weather_label)
        # Neubrandenburg coordinates
        weather_text = get_weather(53.556, 13.261)

        if weather_text:
            weather_label.setText(f"Weather: {weather_text}")
        else:
            weather_label.setText("Weather: unavailable")


        main_layout.addWidget(header)

        # =========================
        # TAB WIDGET
        # =========================
        self.notebook = QtWidgets.QTabWidget()
        self.notebook.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # Enable close buttons ONCE here
        self.notebook.setTabsClosable(True)
        self.notebook.tabCloseRequested.connect(self.close_tab_by_index)

        main_layout.addWidget(self.notebook, 1)

        self.open_tabs = {}


        # =========================
        # STATUS BAR
        # =========================
        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

        # =========================
        # MENU BAR
        # =========================
        menubar = self.menuBar()

        logistics_menu = menubar.addMenu("Logistics")
        tools_menu = menubar.addMenu("Tools")
        gis_menu = menubar.addMenu("GIS")
        admin_menu = menubar.addMenu("Admin")
        help_menu = menubar.addMenu("Help")



        logistics_menu.addAction("Plannung", lambda: self.open_tab("Plannung", tile_page))
        logistics_menu.addAction("Adressen", lambda: self.open_tab("Adressen", adressen_tab))
        logistics_menu.addAction("Abonenten", lambda: self.open_tab("Abonenten", abonenten_tab))
        logistics_menu.addAction("Structure", lambda: self.open_tab("Structure", Structure_tab))

        def build_route_optimizer_tab(content, main_window=None):
            layout = QtWidgets.QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(RouteOptimizerTab(main_window))
            content.setLayout(layout)



        logistics_menu.addAction("Route Optimizer", lambda: self.open_tab("Route Optimizer", build_route_optimizer_tab))
        
        tools_menu.addAction("Calculator", lambda: self.open_tab("Calculator", calculator_page))

        gis_menu.addAction("Adressen GIS Viewer", lambda: self.open_tab("GIS Viewer", gis_tab))

        admin_menu.addAction("Update Adressen", lambda: update_adressen(self))
        admin_menu.addAction("Update Abonenten", lambda: update_Abonents(self))
        admin_menu.addAction("Update Structure", lambda: update_Structure(self))

        help_menu.addAction("Close Tab (Ctrl+W)", self.close_current_tab)
        help_menu.addAction("Exit", self.close)

        # Shortcut for closing tabs
        close_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.close_current_tab)

        # =========================
        # DEFAULT TAB
        # =========================
        self.open_tab("Map View", build_browser)

    # ============================================================
    # TAB MANAGEMENT
    # ============================================================
    def open_tab(self, name, builder):
        """Creates a tab where the builder fully controls the content layout."""
        if name in self.open_tabs:
            self.notebook.setCurrentWidget(self.open_tabs[name])
            return

        # Outer page
        page = QtWidgets.QWidget()
        outer_layout = QtWidgets.QVBoxLayout(page)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Content widget (NO LAYOUT HERE!)
        content = QtWidgets.QWidget()
        outer_layout.addWidget(content)

        # Let builder create the layout
        try:
            builder(content)
        except Exception as e:
            error_label = QtWidgets.QLabel(f"Failed to build tab '{name}': {e}")
            error_label.setAlignment(QtCore.Qt.AlignCenter)

            # Create a layout ONLY if builder failed
            fallback_layout = QtWidgets.QVBoxLayout(content)
            fallback_layout.addWidget(error_label)

        # Add tab
        self.notebook.addTab(page, name)
        self.notebook.setCurrentWidget(page)
        self.open_tabs[name] = page


    def close_current_tab(self):
        index = self.notebook.currentIndex()
        if index != -1:
            self.close_tab_by_index(index)

    def close_tab_by_index(self, index):
        name = self.notebook.tabText(index)
        self.notebook.removeTab(index)
        if name in self.open_tabs:
            del self.open_tabs[name]



# ============================================================
# APPLICATION STARTING PHASE
# ============================================================
def main():

    # Enable high DPI scaling
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    # Required for WebEngine
    try:
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    except Exception:
        pass

    # 1) Create QApplication first
    app = QtWidgets.QApplication(sys.argv)

    # 2) Now configure QtWebEngine cache safely
    cache_path = os.path.join(os.getcwd(), "qt_cache")
    os.makedirs(cache_path, exist_ok=True)

    if QWebEngineProfile:
        profile = QWebEngineProfile.defaultProfile()
        profile.setCachePath(cache_path)
        profile.setPersistentStoragePath(cache_path)


if __name__ == "__main__":
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()

    # Now start your PyQt app
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())   # Start the event loop