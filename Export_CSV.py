import os
from datetime import datetime

def export_to_csv(text: str, zust: str, filename_prefix="route_export"):
    # 1) Root folder
    root_dir = os.path.dirname(os.path.abspath(__file__))

    # 2) Folder with Zust name
    export_dir = os.path.join(root_dir, "Route Statistics", zust)
    os.makedirs(export_dir, exist_ok=True)

    # 3) Filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{zust}_{filename_prefix}_{timestamp}.csv"
    filepath = os.path.join(export_dir, filename)

    # 4) Save file
    with open(filepath, "w", encoding="utf-8-sig") as f:
        f.write(text)

    return filepath
