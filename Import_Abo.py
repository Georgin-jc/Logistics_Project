import os
import sys
import sqlite3
import csv
import pandas as pd
from openpyxl import Workbook
from PyQt5.QtWidgets import QFileDialog

def update_Abonents(main_window):
    main_window.status.showMessage("Importing in progress...")

    # ------------------------------------------------------------
    # Select folder
    # ------------------------------------------------------------
    folder_path = QFileDialog.getExistingDirectory(
        None,
        "Select Folder Containing CSV Files",
        ""
    )

    if not folder_path:
        main_window.status.showMessage("No folder selected.")
        return

    main_window.status.showMessage(f"Selected folder: {folder_path}")

    # ------------------------------------------------------------
    # Merge CSV files
    # ------------------------------------------------------------
    merged_df = pd.DataFrame()

    for file in os.listdir(folder_path):
        if file.lower().endswith(".csv"):
            file_path = os.path.join(folder_path, file)

            # Auto-detect delimiter
            with open(file_path, "r", encoding="latin1") as f:
                first_line = f.readline()
                delimiter = ";" if first_line.count(";") > first_line.count(",") else ","

            df = pd.read_csv(file_path, delimiter=delimiter, dtype=str, encoding="latin1")
            merged_df = pd.concat([merged_df, df], ignore_index=True)

    # ------------------------------------------------------------
    # Save merged Excel file
    # ------------------------------------------------------------
    merged_path = os.path.join(folder_path, "abonenten_merged.xlsx")

    wb = Workbook()
    ws_main = wb.active
    ws_main.title = "Merged_output"

    ws_main.append(list(merged_df.columns))
    for row in merged_df.itertuples(index=False, name=None):
        ws_main.append(row)

    wb.save(merged_path)
    main_window.status.showMessage("Merged Excel file created.")

    # ------------------------------------------------------------
    # Import merged data into SQLite
    # ------------------------------------------------------------
    conn = sqlite3.connect("abonenten.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS abonenten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            abonummer TEXT,
            bezugsnummer TEXT,
            objekt TEXT,
            titel TEXT,
            name TEXT,
            name2 TEXT,
            plz TEXT,
            ort TEXT,
            strasse TEXT,
            hausnr TEXT,
            etage TEXT,
            tuer TEXT,
            lieferinfo TEXT,
            rayon TEXT,
            bezug TEXT,
            netz TEXT,
            hausobjekt TEXT,
            zustellart TEXT,
            etiketten TEXT
        )
    """)

    # Normalize column names for safety
    merged_df.columns = [c.strip() for c in merged_df.columns]

    for _, row in merged_df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO abonenten (
                    abonummer, bezugsnummer, objekt, titel, name, name2,
                    plz, ort, strasse, hausnr, etage, tuer, lieferinfo,
                    rayon, bezug, netz, hausobjekt, zustellart, etiketten
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row.get("Abonummer"),
                row.get("Bezugsnummer"),
                row.get("Objekt"),
                row.get("Titel"),
                row.get("Name"),
                row.get("Name 2"),
                row.get("PLZ"),
                row.get("Ort"),
                row.get("Strasse"),
                row.get("Hausnr"),
                row.get("Etage"),
                row.get("Tür"),
                row.get("Lieferinfo"),
                row.get("Rayon"),
                row.get("Bezug"),
                row.get("Netz"),
                row.get("Hausobjekt"),
                row.get("Zustellart"),
                row.get("Etiketten")
            ))
        except Exception as e:
            print("Skipped row:", e)

    conn.commit()
    conn.close()

    main_window.status.showMessage("Import completed successfully.", 5000)
