import sqlite3
import csv
from pyproj import Transformer
from PyQt5.QtWidgets import  QFileDialog
import sys

def update_Structure(main_window):
    main_window.status.showMessage("Importing in progress...")

    # ---- Ask user to select CSV file ----
    csv_path, _ = QFileDialog.getOpenFileName(
        None,
        "Select Structure.csv",
        "",
        "CSV Files (*.csv)"
    )

    if not csv_path:
        main_window.status.showMessage("No file selected.")
        sys.exit()

    main_window.status.showMessage(f"Selected file: {csv_path}")


    # ---- SQLite connection ----
    conn = sqlite3.connect("structure.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS structure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Fahrtour TEXT,
            BezFahrtour TEXT,
            Depot TEXT,
            Depotbezeichnung TEXT,
            DepotPLZ TEXT,
            DepotOrt TEXT,
            DepotStrasse TEXT,
            DepotHausnummer TEXT,
            DepotHausnummernzusatz TEXT,
            BezirkPLZ TEXT,
            Bezirksbezeichnung TEXT,
            Zustellbereich TEXT,
            Bezirk TEXT,
            PLZ TEXT,
            Ort TEXT,
            Ortsteil TEXT,
            Strasse TEXT,
            Hausnummer TEXT,
            Zusatz TEXT
        )
    """)




    # ---- Import CSV ----
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=';')
        reader.fieldnames = [h.strip() for h in reader.fieldnames]

        for row in reader:
            try:
                cursor.execute("""
                    INSERT INTO structure (
                        Fahrtour, BezFahrtour, Depot, Depotbezeichnung, DepotPLZ, DepotOrt, DepotStrasse, DepotHausnummer, 
                        DepotHausnummernzusatz, BezirkPLZ, Bezirksbezeichnung, Zustellbereich, Bezirk, PLZ, Ort, Ortsteil, 
                        Strasse, Hausnummer, Zusatz
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("Fahrtour"),
                    row.get("BezFahrtour"),
                    row.get("Depot"),
                    row.get("Depotbezeichnung"),
                    row.get("DepotPLZ"),
                    row.get("DepotOrt"),
                    row.get("DepotStrasse"),
                    row.get("DepotHausnummer"),
                    row.get("DepotHausnummernzusatz"),
                    row.get("BezirkPLZ"),
                    row.get("Bezirksbezeichnung"),
                    row.get("Zustellbereich"),
                    row.get("Bezirk"),
                    row.get("PLZ"),
                    row.get("Ort"),
                    row.get("Ortsteil"),
                    row.get("Strasse"),
                    row.get("Hausnummer"),
                    row.get("Zusatz")

                ))

            except Exception as e:
                print("Skipped row:", e)

    main_window.status.showMessage(f"Headers: {reader.fieldnames}")
    conn.commit()
    conn.close()
    main_window.status.showMessage("Import completed.", 5000)