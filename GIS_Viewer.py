from pathlib import Path
import sqlite3
import os
import folium
import geopandas as gpd

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QUrl

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    WEB_AVAILABLE = True
except Exception:
    QWebEngineView = None
    WEB_AVAILABLE = False


DB_PATH = Path("adressen.db")
MAP_HTML = Path("gis_map.html")


# =========================
# MAP CREATION
# =========================

def build_map(markers=None, bounds=None, zoom_start=6):
    if bounds:
        center = [(bounds[0][0] + bounds[1][0]) / 2,
                  (bounds[0][1] + bounds[1][1]) / 2]
    else:
        center = (51.1657, 10.4515)  # Center of Germany    
    m = folium.Map(location=center, zoom_start=zoom_start)
    if markers:
        for lat, lon, label in markers:
            folium.CircleMarker(
                location=(lat, lon),
                radius=6,
                color="red",
                fill=True,
                fill_opacity=1,
            ).add_to(m)

            folium.Marker(
                location=(lat, lon),
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                        font-size:10pt;
                        font-weight:bold;
                        white-space:nowrap;
                        color:black;
                        padding:2px 4px;
                        border-radius:6px;
                    ">{label}</div>
                    """
                )
            ).add_to(m)
    if bounds:
        m.fit_bounds(bounds)

    folium.LayerControl(collapsed=False).add_to(m)

    m.save(str(MAP_HTML))


# =========================
# GIS TAB
# =========================
def gis_tab(parent: QtWidgets.QWidget):
    #main_layout = parent.layout()
    main_layout = QtWidgets.QHBoxLayout(parent)
    main_layout.setContentsMargins(5, 5, 5, 5)
    main_layout.setSpacing(10)

    # =========================
    # SEARCH PANEL (FLOATING)
    # =========================
    search_widget = QtWidgets.QWidget()
    search_widget.setStyleSheet("""
        QWidget {
            background: rgba(255,255,255,180);
            border-radius: 10px;
        }

        QLabel {
            font-size: 12pt;
            font-weight: 600;
            color: #333;
            padding-bottom: 2px;
        }

        QLineEdit, QComboBox {
            font-size: 12pt;
            font-weight: 300;
            padding: 6px 8px;
            border: 1px solid #bbb;
            border-radius: 6px;
            background: #fafafa;
        }

        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #0078d4;
            background: #ffffff;
        }

        QPushButton {
            font-size: 12pt;
            font-weight: bold;
            padding: 6px 12px;
            border-radius: 6px;
            background-color: #0078d4;
            color: white;
        }

        QPushButton:hover {
            background-color: #006cbe;
        }

        QPushButton:pressed {
            background-color: #005fa8;
        }
    """)


    form = QtWidgets.QFormLayout(search_widget)
    form.setHorizontalSpacing(6)
    form.setVerticalSpacing(6)
    form.setContentsMargins(8, 8, 8, 8)

    def combo(width, placeholder):
        cb = QtWidgets.QComboBox(editable=True)
        cb.setPlaceholderText(placeholder)
        cb.setFixedWidth(width)
        return cb

    plz_cb = combo(180, "PLZ",)
    ort_cb = combo(180, "Ort")
    ot_cb = combo(180, "Ortsteil")
    str_cb = combo(180, "Street")
    hn_cb = combo(180, "Hsnr")
    adz_cb = combo(180, "adz")

    limit_cb = QtWidgets.QComboBox()
    limit_cb.addItems(["10", "25", "50", "100", "250", "500", "1000", "2500", "5000", "10000"])
    limit_cb.setCurrentText("50")
    limit_cb.setFixedWidth(80)

    form.addRow(QtWidgets.QLabel("PLZ"), plz_cb)
    form.addRow(QtWidgets.QLabel("Ort"), ort_cb)
    form.addRow(QtWidgets.QLabel("Ortsteil"), ot_cb)
    form.addRow(QtWidgets.QLabel("Straße"), str_cb)
    form.addRow(QtWidgets.QLabel("HNr"), hn_cb)
    form.addRow(QtWidgets.QLabel("Adrz"), adz_cb)
    form.addRow(QtWidgets.QLabel("Limit"), limit_cb)

    plz_cb.currentTextChanged.connect(lambda: update_filters("PLZ"))
    ort_cb.currentTextChanged.connect(lambda: update_filters("Ort"))
    ot_cb.currentTextChanged.connect(lambda: update_filters("Ortsteil"))
    str_cb.currentTextChanged.connect(lambda: update_filters("Street"))
    hn_cb.currentTextChanged.connect(lambda: update_filters("Hsnr"))
    adz_cb.currentTextChanged.connect(lambda: update_filters("adz"))



    btn_row = QtWidgets.QHBoxLayout()


    search_btn = QtWidgets.QPushButton("Search")
    home_btn = QtWidgets.QPushButton("Home")

    btn_row.addWidget(search_btn)
    btn_row.addWidget(home_btn)
    btn_row.addStretch()
    form.addRow("", btn_row)


    # floating panel styling
    shadow = QtWidgets.QGraphicsDropShadowEffect()
    shadow.setBlurRadius(20)
    shadow.setOffset(0, 2)
    search_widget.setGraphicsEffect(shadow)

    # =========================
    # MAP VIEW
    # =========================
    if not WEB_AVAILABLE:
        main_layout.addWidget(QtWidgets.QLabel("QWebEngine not available"))
        return

    build_map()
    view = QWebEngineView()
    view.load(QUrl.fromLocalFile(os.path.abspath(str(MAP_HTML))))

    # =========================
    # OVERLAY CONTAINER (FIXED)
    # =========================
    map_container = QtWidgets.QWidget()
    stack = QtWidgets.QStackedLayout(map_container)
    stack.setStackingMode(QtWidgets.QStackedLayout.StackAll)
    stack.setContentsMargins(10, 10, 10, 10)

    stack.addWidget(view)
    stack.addWidget(search_widget)

    stack.setAlignment(search_widget, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

    search_widget.setFixedSize(320, 910)
    search_widget.setAttribute(QtCore.Qt.WA_StyledBackground, True)


    shadow = QtWidgets.QGraphicsDropShadowEffect()
    shadow.setBlurRadius(20)
    shadow.setOffset(0, 2)
    search_widget.setGraphicsEffect(shadow)

    main_layout.addWidget(map_container, 1)

    search_widget.raise_()


    # =========================
    # CASCADING FILTERS
    # =========================
    def update_filters(changed=None):
        if not DB_PATH.exists():
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Current selections
        filters = {
            "PLZ": plz_cb.currentText().strip(),
            "Ort": ort_cb.currentText().strip(),
            "Ortsteil": ot_cb.currentText().strip(),
            "Street": str_cb.currentText().strip(),
            "Hsnr": hn_cb.currentText().strip(),
            "adz": adz_cb.currentText().strip(),
        }

        # Build WHERE clause
        where, params = [], []
        for f, v in filters.items():
            if v:
                where.append(f"{f} = ?")
                params.append(v)

        where_sql = " WHERE " + " AND ".join(where) if where else ""

        # Helper: update only dependent combos
        def fill(field, cb):
            if field == changed:
                return  # do NOT touch the combo the user is editing

            cur.execute(
                f"SELECT DISTINCT {field} FROM adressen{where_sql} ORDER BY {field}",
                params
            )
            values = [str(r[0]) for r in cur.fetchall()]

            if not values:
                return  # do NOT clear the combo if no results

            current = cb.currentText()

            cb.blockSignals(True)
            cb.clear()
            cb.addItems(values)

            # restore previous selection if still valid
            if current in values:
                cb.setCurrentText(current)

            cb.blockSignals(False)

        fill("PLZ", plz_cb)
        fill("Ort", ort_cb)
        fill("Ortsteil", ot_cb)
        fill("Street", str_cb)
        fill("Hsnr", hn_cb)
        fill("adz", adz_cb)

        conn.close()

    # =========================
    # SEARCH
    # =========================
    def search():
        if not DB_PATH.exists():
            return

        filters = {
            "PLZ": plz_cb.currentText().strip(),
            "Ort": ort_cb.currentText().strip(),
            "Ortsteil": ot_cb.currentText().strip(),
            "Street": str_cb.currentText().strip(),
            "Hsnr": hn_cb.currentText().strip(),
            "adz": adz_cb.currentText().strip(),
        }

        where, params = [], []
        for f, v in filters.items():
            if v:
                where.append(f"{f} = ?")
                params.append(v)

        if not where:
            return

        query = f"""
            SELECT lat, lon, Hsnr, adz
            FROM adressen
            WHERE {' AND '.join(where)}
              AND lat IS NOT NULL
              AND lon IS NOT NULL
            LIMIT {limit_cb.currentText()}
        """

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        markers, lats, lons = [], [], []
        for lat, lon, h, a in rows:
            lat, lon = float(lat), float(lon)
            markers.append((lat, lon, f"{h} {a}"))
            lats.append(lat)
            lons.append(lon)

        if markers:
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)

            bounds = [[min_lat, min_lon], [max_lat, max_lon]]

            build_map(markers, bounds=bounds)
        else:
            build_map()


        view.load(QUrl.fromLocalFile(os.path.abspath(str(MAP_HTML))))

    def home():
        build_map()
        view.load(QUrl.fromLocalFile(os.path.abspath(str(MAP_HTML))))
        for cb in (plz_cb, ort_cb, ot_cb, str_cb, hn_cb, adz_cb):
            cb.setEditText("")


    update_filters()

    search_btn.clicked.connect(search)
    home_btn.clicked.connect(home)