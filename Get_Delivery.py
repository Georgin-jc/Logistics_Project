import sqlite3
import csv
import os
import re


# ============================================================
# MAIN FUNCTION USED BY FASTAPI
# ============================================================
def get_deliveries_for_zust(zust_number):
    # --- Connect to all three databases ---
    conn_struct = sqlite3.connect("structure.db")
    conn_abos = sqlite3.connect("abonenten.db")
    conn_addr = sqlite3.connect("adressen.db")

    cur_struct = conn_struct.cursor()
    cur_abos = conn_abos.cursor()
    cur_addr = conn_addr.cursor()

    # --- Step 1: Find Bezirk for the given Zust number ---
    cur_struct.execute("""
        SELECT DISTINCT Bezirk 
        FROM structure 
        WHERE Zustellbereich = ?
    """, (zust_number,))
    bezirk = [row[0] for row in cur_struct.fetchall()]
    
    # --- Step 1b: Find Depot information for the given Zust number ---
    cur_struct.execute("""
        SELECT DISTINCT DepotPLZ, DepotOrt, DepotStrasse, DepotHausnummer, DepotHausnummernzusatz 
        FROM structure 
        WHERE Zustellbereich = ?
    """, (zust_number,))
    depot_info = cur_struct.fetchall()

    if not bezirk:
        return []

    # --- Step 2: Get all subscribers for this Bezirk ---
    subscribers = []
    for bez in bezirk:
        cur_abos.execute("""
            SELECT plz, ort, Strasse, Hausnr, name, objekt
            FROM abonenten
            WHERE rayon = ?
        """, (bez,))
        subscribers.extend(cur_abos.fetchall())

    # --- Step 3: For each subscriber, get coordinates ---
    results = []



    for sub in subscribers:
        plz, ort, strasse, hausnr, name, objekt = sub

        # Split house number
        def split_hausnummer(value):
            if not value:
                return "", ""
            value = str(value).strip()
            match = re.match(r"(\d+)\s*([A-Za-z\-]*)", value)
            if match:
                return match.group(1), match.group(2)
            return value, ""

        hausnr, adz = split_hausnummer(hausnr)

        cur_addr.execute("""
            SELECT lat, lon
            FROM adressen
            WHERE plz = ? AND ortsteil = ? AND street = ? AND hsnr = ? AND adz = ?
        """, (plz, ort, strasse, hausnr, adz))

        coords = cur_addr.fetchone()
        lat, lon = coords if coords else (None, None)

        results.append({
            "name": name,
            "abo_type": objekt,
            "plz": plz,
            "ort": ort,
            "strasse": strasse,
            "hausnummer": hausnr,
            "lat": lat,
            "lon": lon
        })
    # --- Convert depot info into a result entry ---
    if depot_info:
        depot_plz, depot_ort, depot_str, depot_hnr, depot_hnr_zus = depot_info[0]


        # Get depot coordinates
        cur_addr.execute("""
            SELECT lat, lon
            FROM adressen
            WHERE plz = ? AND ort = ? AND street = ? AND hsnr = ? AND adz = ?
        """, (depot_plz, depot_ort, depot_str, depot_hnr, depot_hnr_zus))

        depot_coords = cur_addr.fetchone()
        depot_lat, depot_lon = depot_coords if depot_coords else (None, None)

        depot_entry = {
            "name": "Depot",
            "abo_type": "DEPOT",
            "plz": depot_plz,
            "ort": depot_ort,
            "strasse": depot_str,
            "hausnummer": depot_hnr,
            "lat": depot_lat,
            "lon": depot_lon
        }

        # Insert depot at start and end
        results.insert(0, depot_entry)
        #results.append(depot_entry.copy())


    # --- Close connections ---
    conn_struct.close()
    conn_abos.close()
    conn_addr.close()

    return results


def get_delivery_route(zust_number):
    results = get_deliveries_for_zust(zust_number)
    return results




# ============================================================
# OPTIONAL: CSV EXPORT TOOL (ONLY RUNS WHEN CALLED DIRECTLY)
# ============================================================
def save_deliveries_to_csv(deliveries, zust_number, folder_path):
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{zust_number}.csv")

    with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=';')

        writer.writerow([
            "Name", "AboType", "PLZ", "Ort", "Strasse",
            "Hausnummer", "Lat", "Lon"
        ])

        for d in deliveries:
            writer.writerow([
                d["name"],
                d["abo_type"],
                d["plz"],
                d["ort"],
                d["strasse"],
                d["hausnummer"],
                d["lat"],
                d["lon"]
            ])

    print(f"Saved CSV to: {file_path}")


# ============================================================
# CLI MODE (ONLY RUNS WHEN YOU EXECUTE THIS FILE DIRECTLY)
# ============================================================
if __name__ == "__main__":
    zust = input("Enter Zust number: ")
    deliveries = get_deliveries_for_zust(zust)

    for d in deliveries:
        print(d)

    save_folder = r"G:\Python.vscode\GStarLogistics\ZustExports"
    save_deliveries_to_csv(deliveries, zust, save_folder)
