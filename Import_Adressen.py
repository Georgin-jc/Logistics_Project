import sqlite3
import csv
from pyproj import Transformer
from PyQt5.QtWidgets import  QFileDialog
import sys

def update_adressen(main_window):
    main_window.status.showMessage("Importing in progress...")


    # ---- Ask user to select CSV file ----
    csv_path, _ = QFileDialog.getOpenFileName(
        None,
        "Select adressen.csv",
        "",
        "CSV Files (*.csv)"
    )

    if not csv_path:
        main_window.status.showMessage("No file selected.")
        sys.exit()

    main_window.status.showMessage(f"Selected file: {csv_path}")

    # ---- Coordinate transformer (Gaus-Krüger Zone 4 → WGS84) ----
    transformer = Transformer.from_crs(
        "EPSG:31468",
        "EPSG:4326",
        always_xy=True
    )

    # ---- SQLite connection ----
    conn = sqlite3.connect("adressen.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS adressen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        oid TEXT,           
        plz TEXT,
        ort TEXT,
        ortsteil TEXT,
        street TEXT,
        hsnr TEXT,
        adz TEXT,           
        xcoord REAL,
        ycoord REAL,
        lat REAL,
        lon REAL
    )
    """)

    # ---- Import CSV ----
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=';')
        reader.fieldnames = [h.strip() for h in reader.fieldnames]

        for row in reader:
            try:
                x = float(row["xcoord"])
                y = float(row["ycoord"])

                lon, lat = transformer.transform(x, y)

                cursor.execute("""
                    INSERT INTO adressen (
                        oid, plz, ort, ortsteil, street, hsnr, adz,
                        xcoord, ycoord, lat, lon
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("oid"),
                    row.get("PLZ"),
                    row.get("Ort"),
                    row.get("Ortsteil"),
                    row.get("Street"),
                    row.get("Hsnr"),
                    row.get("adz"),
                    x,
                    y,
                    lat,
                    lon
                ))

            except Exception as e:
                print("Skipped row:", e)

    main_window.status.showMessage(f"Headers: {reader.fieldnames}")
    conn.commit()
    conn.close()
    main_window.status.showMessage("Import completed.", 5000)