import sqlite3
from PyQt5 import QtWidgets, QtCore


def abonenten_tab(parent: QtWidgets.QWidget):

    # ============================================================
    # MAIN LAYOUT (HORIZONTAL)
    # ============================================================
    main_layout = QtWidgets.QHBoxLayout(parent)
    main_layout.setContentsMargins(5, 5, 5, 5)
    main_layout.setSpacing(10)

    # ============================================================
    # RIGHT SIDE → ADRESSEN TABLE
    # ============================================================
    adress_table = QtWidgets.QTableWidget()
    adress_table.setColumnCount(9)
    adress_table.setHorizontalHeaderLabels(
        ["oid", "PLZ", "Ort", "Ortsteil", "Straße", "Hsnr", "AdZu", "Xcoord", "Ycoord"]
    )
    adress_table.verticalHeader().setVisible(False)
    adress_table.setAlternatingRowColors(True)
    adress_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

    right_scroll = QtWidgets.QScrollArea()
    right_scroll.setWidgetResizable(True)
    right_scroll.setWidget(adress_table)
    right_scroll.setMinimumWidth(500)

    main_layout.addWidget(right_scroll, stretch=2)

    # ============================================================
    # LEFT SIDE → 3 STACKED BOXES
    # ============================================================
    left_column = QtWidgets.QVBoxLayout()
    left_column.setSpacing(10)
    main_layout.addLayout(left_column, stretch=1)

    # ============================================================
    # LEFT TOP → SEARCH FILTERS
    # ============================================================
    search_box = QtWidgets.QFrame()
    search_box.setFrameShape(QtWidgets.QFrame.Box)
    search_box.setMinimumHeight(200)
    search_layout = QtWidgets.QVBoxLayout(search_box)

    plz_input = QtWidgets.QComboBox()
    ortsteil_input = QtWidgets.QComboBox()
    strasse_input = QtWidgets.QComboBox()
    hausnr_input = QtWidgets.QComboBox()

    # Load PLZ only (others cascade)
    conn = sqlite3.connect("adressen.db")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT plz FROM adressen ORDER BY plz")
    plz_input.addItem("")
    plz_input.addItems([row[0] for row in cur.fetchall()])
    conn.close()

    for label, widget in [
        ("PLZ", plz_input),
        ("Ortsteil", ortsteil_input),
        ("Straße", strasse_input),
        ("Hausnr", hausnr_input),
    ]:
        search_layout.addWidget(QtWidgets.QLabel(label))
        search_layout.addWidget(widget)

    # Buttons
    btn_row = QtWidgets.QHBoxLayout()
    search_btn = QtWidgets.QPushButton("Search")
    #search_btn.setFixedSize(80, 30)
    reset_btn = QtWidgets.QPushButton("Reset")
    #reset_btn.setFixedSize(80, 30)
    btn_row.addWidget(search_btn)
    btn_row.addWidget(reset_btn)
    search_layout.addLayout(btn_row)

    left_column.addWidget(search_box, stretch=1)

    # ============================================================
    # LEFT MIDDLE → ABONNENTEN TABLE
    # ============================================================
    abon_table = QtWidgets.QTableWidget()
    abon_table.setColumnCount(6)
    abon_table.setHorizontalHeaderLabels(
        ["Abonummer", "Bezugsnummer", "Objekt", "Titel", "Name", "Name 2"]
    )
    abon_table.verticalHeader().setVisible(False)
    abon_table.setAlternatingRowColors(True)

    abon_scroll = QtWidgets.QScrollArea()
    abon_scroll.setWidgetResizable(True)
    abon_scroll.setWidget(abon_table)
    abon_scroll.setMinimumHeight(150)

    left_column.addWidget(abon_scroll, stretch=2)

    # ============================================================
    # LEFT BOTTOM → SUGGESTIONS
    # ============================================================

    suggestions_label = QtWidgets.QLabel("Suggestions will appear here…")
    suggestions_label.setWordWrap(True)

    scroll_area = QtWidgets.QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(suggestions_label)

    suggestions_box = QtWidgets.QFrame()
    suggestions_box.setFrameShape(QtWidgets.QFrame.Box)
    suggestions_box.setMinimumHeight(120)

    suggestions_layout = QtWidgets.QVBoxLayout(suggestions_box)
    suggestions_layout.addWidget(scroll_area)

    left_column.addWidget(suggestions_box, stretch=1)


    # ============================================================
    # CASCADING FILTERS
    # ============================================================
    def update_ortsteil():
        ortsteil_input.clear()
        ortsteil_input.addItem("")
        plz = plz_input.currentText().strip()
        if not plz:
            return
        conn = sqlite3.connect("adressen.db")
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT ortsteil FROM adressen WHERE plz=? ORDER BY ortsteil", (plz,))
        ortsteil_input.addItems([row[0] for row in cur.fetchall()])
        conn.close()

    def update_strasse():
        strasse_input.clear()
        strasse_input.addItem("")
        plz = plz_input.currentText().strip()
        ortsteil = ortsteil_input.currentText().strip()
        if not plz or not ortsteil:
            return
        conn = sqlite3.connect("adressen.db")
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT street FROM adressen WHERE plz=? AND ortsteil=? ORDER BY street",
            (plz, ortsteil),
        )
        strasse_input.addItems([row[0] for row in cur.fetchall()])
        conn.close()

    def update_hausnr():
        hausnr_input.clear()
        hausnr_input.addItem("")
        plz = plz_input.currentText().strip()
        ortsteil = ortsteil_input.currentText().strip()
        strasse = strasse_input.currentText().strip()
        if not plz or not ortsteil or not strasse:
            return
        conn = sqlite3.connect("adressen.db")
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT hsnr || adz FROM adressen WHERE plz=? AND ortsteil=? AND street=? ORDER BY hsnr",
            (plz, ortsteil, strasse),
        )
        hausnr_input.addItems([row[0] for row in cur.fetchall()])
        conn.close()

    plz_input.currentIndexChanged.connect(update_ortsteil)
    ortsteil_input.currentIndexChanged.connect(update_strasse)
    strasse_input.currentIndexChanged.connect(update_hausnr)

    # ============================================================
    # RESET FILTERS
    # ============================================================
    def reset_filters():
        plz_input.setCurrentIndex(0)
        ortsteil_input.clear()
        ortsteil_input.addItem("")
        strasse_input.clear()
        strasse_input.addItem("")
        hausnr_input.clear()
        hausnr_input.addItem("")
        abon_table.setRowCount(0)
        suggestions_label.setText("Suggestions will appear here…")

    reset_btn.clicked.connect(reset_filters)

    # ============================================================
    # LOAD ADRESSEN TABLE (FAST)
    # ============================================================
    conn = sqlite3.connect("adressen.db")
    cur = conn.cursor()

    adress_table.setUpdatesEnabled(False)
    adress_table.setSortingEnabled(False)

    cur.execute("SELECT oid, plz, ort, ortsteil, street, hsnr, adz, xcoord, ycoord FROM adressen")
    rows = cur.fetchall()

    adress_table.setRowCount(len(rows))

    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            adress_table.setItem(i, j, QtWidgets.QTableWidgetItem(str(val)))

    adress_table.setUpdatesEnabled(True)
    adress_table.setSortingEnabled(True)

    conn.close()

    # ============================================================
    # SEARCH LOGIC (FULLY FIXED)
    # ============================================================
    def run_search():
        plz = plz_input.currentText().strip()
        ortsteil = ortsteil_input.currentText().strip()
        strasse = strasse_input.currentText().strip()
        hausnr = hausnr_input.currentText().strip()

        adress_table.clearSelection()
        matches = []

        for i in range(adress_table.rowCount()):
            row_plz = adress_table.item(i, 1).text().strip()
            row_ortsteil = adress_table.item(i, 3).text().strip()  # FIXED INDEX
            row_str = adress_table.item(i, 4).text().strip()
            row_hsnr = adress_table.item(i, 5).text().strip()
            row_adzu = adress_table.item(i, 6).text().strip()
            full_hsnr = row_hsnr + row_adzu

            if (
                (not plz or row_plz == plz)
                and (not ortsteil or row_ortsteil.lower() == ortsteil.lower())
                and (not strasse or row_str.lower() == strasse.lower())
                and (not hausnr or full_hsnr == hausnr)
            ):
                adress_table.selectRow(i)
                matches.append((row_plz, row_ortsteil, row_str, full_hsnr))

        # Suggestions
        if matches:
            suggestions_label.setText(
                "Suggestions:\n" + "\n".join([f"{p} {o}, {s} {h}" for p, o, s, h in matches])
            )
        else:
            suggestions_label.setText("No matching suggestions found.")

        # Abonnenten results
        abon_table.setRowCount(0)

        matches = list(set(matches))  # Unique only
        if matches:
            conn = sqlite3.connect("abonenten.db")
            cur = conn.cursor()

            for plz, ortsteil, strasse, hausnr in matches:
                cur.execute("""
                    SELECT abonummer, bezugsnummer, objekt, titel, name, name2
                    FROM abonenten
                    WHERE plz=? AND ort=? AND strasse=? AND hausnr=?
                """, (plz, ortsteil, strasse, hausnr))

                for r in cur.fetchall():
                    row_idx = abon_table.rowCount()
                    abon_table.insertRow(row_idx)
                    for j, val in enumerate(r):
                        abon_table.setItem(row_idx, j, QtWidgets.QTableWidgetItem(str(val)))

            conn.close()

    search_btn.clicked.connect(run_search)
