import sqlite3
from PyQt5 import QtWidgets


def Structure_tab(parent: QtWidgets.QWidget):
    # Use existing layout created by MainWindow
    #layout = parent.layout()
    layout = QtWidgets.QHBoxLayout(parent)
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(10)

    table = QtWidgets.QTableWidget()
    table.setColumnCount(8)
    headers = ["Zustellbereich", "Bezirk", "PLZ", "Ort", "Ortsteil", "Strasse", "Hausnummer", "Zusatz"]
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    # Make header bold for better readability
    header = table.horizontalHeader()
    font = header.font()
    font.setBold(True)
    header.setFont(font)

    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    layout.addWidget(table)

    conn = sqlite3.connect("structure.db")
    cur = conn.cursor()

    try:
        cur.execute("SELECT zustellbereich, bezirk, plz, ort, ortsteil, strasse, hausnummer, zusatz FROM structure")
        rows = cur.fetchall()
    except Exception:
        rows = []

    table.setRowCount(len(rows))

    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            item = QtWidgets.QTableWidgetItem(str(val) if val is not None else "")
            table.setItem(i, j, item)

    conn.close()
