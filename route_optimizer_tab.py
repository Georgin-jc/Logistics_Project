# route_optimizer_tab.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtCore import QUrl
from Route_Stats import compute_route_stats
from Get_Delivery import get_delivery_route
from distance_to_road import distance_to_road
from Route_Stats import optimize_route, extract_order
import requests
import folium
import json
import os
from api import ORS_API_KEY
from Export_CSV import export_to_csv
from pop_up import show_info_popup
import openrouteservice as ors



class RouteOptimizerTab(QWidget):

    def __init__(self, main_window=None):

        self.current_zoom = 15  # default zoom

        super().__init__()

        # --- MAIN LAYOUT: Map left, Info right ---
        main_layout = QHBoxLayout(self)

        # =======================
        # LEFT SIDE → MAP VIEW
        # =======================
        left_layout = QVBoxLayout()

        # Input row
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Zust:"))

        self.zust_input = QLineEdit()
        input_row.addWidget(self.zust_input)

        # Vehicle profile dropdown
        self.profile_dropdown = QComboBox()
        self.profile_dropdown.addItems([
            "Car (driving-car)",
            "Truck (driving-hgv)",
            "Bike (cycling-regular)",
            "Road Bike (cycling-road)",
            "E-Bike (cycling-electric)",
            "Walking (foot-walking)"
        ])
        input_row.addWidget(self.profile_dropdown)

        self.profile_map = {
            "Car (driving-car)": "driving-car",
            "Truck (driving-hgv)": "driving-hgv",
            "Bike (cycling-regular)": "cycling-regular",
            "Road Bike (cycling-road)": "cycling-road",
            "Mountain Bike (cycling-mountain)": "cycling-mountain",
            "E-Bike (cycling-electric)": "cycling-electric",
            "Walking (foot-walking)": "foot-walking"
        }

        # Show saved Route
        self.btn_view_saved = QPushButton("View Saved Route")
        self.btn_view_saved.clicked.connect(self.view_saved_route)
        input_row.addWidget(self.btn_view_saved)


        # Generate button
        self.btn_generate = QPushButton("Generate Route")
        self.btn_generate.clicked.connect(self.generate_route)
        input_row.addWidget(self.btn_generate)

        # Add to layout
        left_layout.addLayout(input_row)


        # Map widget
        self.map_view = QWebEngineView()
        left_layout.addWidget(self.map_view)

        # =======================
        # RIGHT SIDE → INFO PANEL
        # =======================
        right_layout = QVBoxLayout()

        # Export button
        self.exportButton = QPushButton("Export CSV")
        self.exportButton.clicked.connect(self.handle_export)
        right_layout.addWidget(self.exportButton)
        
        self.exportOrderButton = QPushButton("Export Route Order")
        self.exportOrderButton.clicked.connect(self.export_route_order)
        right_layout.addWidget(self.exportOrderButton)


        # Table for results
        self.routeTable = QTableWidget()
        self.routeTable.setColumnCount(2)
        self.routeTable.setHorizontalHeaderLabels(["Label", "Value"])
        self.routeTable.verticalHeader().setVisible(False)
        self.routeTable.setEditTriggers(QTableWidget.NoEditTriggers)
        right_layout.addWidget(self.routeTable)

        # Table for route order
        self.routeOrderTable = QTableWidget()
        self.routeOrderTable.setColumnCount(3)
        self.routeOrderTable.setHorizontalHeaderLabels(["Pos", "Strasse", "Hausnr"])
        self.routeOrderTable.verticalHeader().setVisible(False)
        self.routeOrderTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.routeOrderTable.setAlternatingRowColors(True)
        self.routeOrderTable.setSortingEnabled(True)
        self.routeOrderTable.setColumnWidth(0, 50)   # Pos
        self.routeOrderTable.setColumnWidth(1, 120)  # Strasse
        self.routeOrderTable.setColumnWidth(2, 80)   # Hausnr

        self.routeOrderTable.resizeColumnsToContents()
        self.routeOrderTable.cellClicked.connect(self.highlight_selected_address)


        # Wrap in scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.routeOrderTable)
        scroll_area.setMinimumHeight(240)
        scroll_area.setMaximumHeight(400)

        # Add to layout
        right_layout.addWidget(scroll_area)

        # Add both sides to main layout
        main_layout.addLayout(left_layout, stretch=5)
        main_layout.addLayout(right_layout, stretch=1)

    def generate_route(self):

        selected_label = self.profile_dropdown.currentText()
        profile = self.profile_map[selected_label]
        self.current_profile = profile

        try:
            zust = self.zust_input.text().strip()
            self.zust_name = zust
            if not zust:
                show_info_popup(self, "Fehler", "Bitte Zustellbereich eingeben.")
                return

            deliveries = []

            # -----------------------------
            # 1) FETCH RAW DELIVERY LIST
            # -----------------------------
            results = get_delivery_route(zust)
            if not results or len(results) < 2:
                show_info_popup(self, "Fehler", "Nicht genug Adressen für eine Route.")
                return

            # -----------------------------
            # 2) OPTIMIZE ROUTE
            # -----------------------------
            try:
                optimized = optimize_route(results, ORS_API_KEY, profile)

                # Convert ORS optimization output into ordered list
                results = extract_order(optimized, results)
                self.ordered_route = results

            except Exception as e:
                show_info_popup(self, "Fehler", f"Optimierung fehlgeschlagen:\n{e}")
                return

            # -----------------------------
            # 3) BUILD COORDS FROM ORDERED ROUTE
            # -----------------------------
            coords = [
                [r["lon"], r["lat"]]
                for r in self.ordered_route
                if r.get("lat") is not None and r.get("lon") is not None
            ]
            if not coords:
                show_info_popup(self, "Fehler", "Keine gültigen Koordinaten für die Route.")
                return

            lon, lat = coords[0]

            # -----------------------------
            # 4) GET GEOMETRY FROM ORS DIRECTIONS
            # -----------------------------
            client = ors.Client(key=ORS_API_KEY)
            try:
                route_geojson = client.directions(
                    coordinates=coords,
                    profile=profile,
                    format="geojson"
                )
            except Exception as e:
                show_info_popup(self, "Fehler", f"Route konnte nicht berechnet werden:\n{e}")
                return

            self.last_route_geojson = route_geojson

            # -----------------------------
            # 5) BUILD FOLIUM MAP
            # -----------------------------
            m = folium.Map(location=[lat, lon], zoom_start=25)
            folium.GeoJson(route_geojson, name="Optimierte Route").add_to(m)

            # -----------------------------
            # 6) FETCH DELIVERIES FOR MARKERS
            # -----------------------------
            try:
                deliveries_url = f"http://localhost:8000/deliveries/{zust}"
                deliveries = requests.get(deliveries_url).json()
            except:
                deliveries = []

            if isinstance(deliveries, list):
                for d in deliveries:
                    if d.get("lat") and d.get("lon"):
                        popup_html = (
                            f"<b>{d.get('name','')}</b><br>"
                            f"Abo: {d.get('abo_type','')}<br>"
                            f"{d.get('strasse','')} {d.get('hausnummer','')}<br>"
                            f"{d.get('plz','')} {d.get('ort','')}"
                        )

                        folium.CircleMarker(
                            location=[d["lat"], d["lon"]],
                            radius=6,
                            color="red",
                            fill=True,
                            fill_color="red",
                            fill_opacity=0.9,
                            popup=popup_html
                        ).add_to(m)

            map_path = os.path.abspath("route_map.html")
            m.save(map_path)
            self.map_view.load(QUrl.fromLocalFile(map_path))

            # -----------------------------
            # 7) UPDATE ORDER TABLE
            # -----------------------------
            self.routeOrderTable.setRowCount(len(self.ordered_route))

            for i, d in enumerate(self.ordered_route):
                self.routeOrderTable.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.routeOrderTable.setItem(i, 1, QTableWidgetItem(d.get("strasse", "")))
                self.routeOrderTable.setItem(i, 2, QTableWidgetItem(d.get("hausnummer", "")))

            self.routeOrderTable.setAlternatingRowColors(True)
            self.routeOrderTable.setSortingEnabled(True)
            self.routeOrderTable.resizeColumnsToContents()

            # -----------------------------
            # 8) COMPUTE ROUTE STATS
            # -----------------------------
            total_km, total_min, segments = compute_route_stats(
                self.ordered_route,
                ORS_API_KEY,
                profile
            )

            total_hours = round(total_min / 60, 2)

            # -----------------------------
            # 9) SUM DISTANCE TO ROAD
            # -----------------------------
            total_offset = 0.0

            if isinstance(deliveries, list):
                for d in deliveries:
                    try:
                        lat_d = float(str(d.get("lat")).strip())
                        lon_d = float(str(d.get("lon")).strip())
                    except:
                        continue

                    try:
                        dist_m, snapped = distance_to_road(lat_d, lon_d, ORS_API_KEY)
                        total_offset += dist_m
                    except:
                        continue

            distance_toanfro_road = total_offset * 2

            # -----------------------------
            # 10) UPDATE STATS TABLE
            # -----------------------------
            labels = [
                "Driving Distance",
                "Driving Time",
                "Walking Distance",
                "Walking time (hours)",
                "Walking time (minutes)",
                "Total Distance",
                "Total Time",
                "Weekly (6 days)",
                "Weekly (5 days)",
                "Monthly"
            ]

            values = [
                f"{total_km:.1f} km",
                f"{total_hours:.1f} Stunden",
                f"{distance_toanfro_road / 1000:.2f} km",
                f"{distance_toanfro_road / 1.194 / 60 / 60:.2f} Stunden",
                f"{distance_toanfro_road / 1.194 / 60:.2f} Minuten",
                f"{total_km + distance_toanfro_road / 1000:.1f} km",
                f"{total_hours + distance_toanfro_road / 1.194 / 60 / 60:.1f} Stunden",
                f"{(total_hours + distance_toanfro_road / 1.194 / 60 / 60) * 6:.1f} Stunden",
                f"{(total_hours + distance_toanfro_road / 1.194 / 60 / 60) * 5:.1f} Stunden",
                f"{(total_hours + distance_toanfro_road / 1.194 / 60 / 60) * 26.09:.1f} Stunden"
            ]

            self.routeTable.setRowCount(len(labels))

            for i in range(len(labels)):
                self.routeTable.setItem(i, 0, QTableWidgetItem(labels[i]))
                self.routeTable.setItem(i, 1, QTableWidgetItem(values[i]))

            # -----------------------------
            # 11) SAVE EVERYTHING TO DISK
            # -----------------------------
            save_data = {
                "profile": self.current_profile,
                "optimized": optimized,
                "ordered_route": self.ordered_route,
                "route_geojson": self.last_route_geojson,
                "stats": {
                    "total_km": total_km,
                    "total_min": total_min,
                    "segments": segments
                }
            }

            folder = "Optimised routes"
            os.makedirs(folder, exist_ok=True)
            filepath = os.path.join(folder, f"{zust}.json")

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            show_info_popup(self, "Info", f"Route gespeichert unter {filepath}")

        except Exception as e:
            show_info_popup(self, "Fehler", f"Ein Fehler ist aufgetreten:\n{e}")

    # ============================================================
    # Show Saved BUTTON
    # ============================================================


    def view_saved_route(self):
        zust = self.zust_input.text().strip()
        if not zust:
            show_info_popup(self, "Fehler", "Bitte Zustellbereich eingeben.")
            return

        folder = "Optimised routes"
        filepath = os.path.join(folder, f"{zust}.json")

        if not os.path.exists(filepath):
            show_info_popup(self, "Info", f"Keine gespeicherte Route für {zust} gefunden.")
            return

        with open(filepath, "r", encoding="utf-8") as f:
            saved = json.load(f)

        # Restore everything
        self.current_profile = saved["profile"]
        self.ordered_route = saved["ordered_route"]
        self.last_route_geojson = saved["route_geojson"]

        stats = saved["stats"]
        total_km = stats["total_km"]
        total_min = stats["total_min"]
        segments = stats["segments"]

        # Rebuild UI
        self.update_table(self.ordered_route)
        self.update_stats(total_km, total_min, segments)
        self.update_map(self.last_route_geojson)

        show_info_popup(self, "Info", f"Gespeicherte Route für {zust} geladen.")




    # ============================================================
    # EXPORT BUTTON
    # ============================================================
    def handle_export(self):
        try:
            # Convert table to CSV text
            rows = self.routeTable.rowCount()
            csv_lines = ["Label,Value"]

            for i in range(rows):
                label = self.routeTable.item(i, 0).text()
                value = self.routeTable.item(i, 1).text()
                csv_lines.append(f"{label},{value}")

            text = "\n".join(csv_lines)

            zust = getattr(self, "zust_name", "zust")  # fallback if not set
            filepath = export_to_csv(text, zust)


            show_info_popup(
                self,
                "Export erfolgreich",
                f"Die Datei wurde gespeichert:\n{filepath}"
            )

        except Exception as e:
            show_info_popup(
                self,
                "Export Fehler",
                f"Es ist ein Fehler aufgetreten:\n{e}"
            )

    def export_route_order(self):
        try:
            if not hasattr(self, "ordered_route") or not self.ordered_route:
                show_info_popup(self, "Fehler", "Keine Route zum Exportieren vorhanden.")
                return

            from datetime import datetime
            import os

            # Create folder
            root_dir = os.path.dirname(os.path.abspath(__file__))
            export_dir = os.path.join(root_dir, "Route Calculation")
            os.makedirs(export_dir, exist_ok=True)
        

            # Filename
            zust = getattr(self, "zust_name", "zust")  # fallback if not set
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filepath = os.path.join(export_dir, f"{zust}_route_order_{timestamp}.csv")

            # Build CSV lines
            lines = ["Position,Name,Street,Hausnummer,Ort,PLZ,Lat,Lon"]
            for i, d in enumerate(self.ordered_route, start=1):
                name = d.get("name", "")
                street = d.get("strasse", "")
                housenr = d.get("hausnummer", "")
                ort = d.get("ort", "")
                plz = d.get("plz", "")
                lat = d.get("lat", "")
                lon = d.get("lon", "")
                lines.append(f"{i},{name},{street},{housenr},{ort},{plz},{lat},{lon}")


            # Save file
            with open(filepath, "w", encoding="utf-8-sig") as f:
                f.write("\n".join(lines))

            show_info_popup(
                self,
                "Export erfolgreich",
                f"Die Reihenfolge wurde gespeichert:\n{filepath}"
            )

        except Exception as e:
            show_info_popup(
                self,
                "Export Fehler",
                f"Es ist ein Fehler aufgetreten:\n{e}"
            )

    def highlight_selected_address(self, row, col):
        try:
            d = self.ordered_route[row]
            sel_lat = d.get("lat")
            sel_lon = d.get("lon")

            if sel_lat is None or sel_lon is None:
                show_info_popup(self, "Fehler", "Ausgewählte Adresse hat keine gültigen Koordinaten.")
                return

            # Create map centered on selected point, but zoom will be overridden by fit_bounds
            m = folium.Map(location=[0, 0], zoom_start=2)
            folium.GeoJson(self.last_route_geojson, name="Route").add_to(m)

            # Add markers
            for item in self.ordered_route:
                lat = item.get("lat")
                lon = item.get("lon")
                if lat is None or lon is None:
                    continue

                color = "blue" if lat == sel_lat and lon == sel_lon else "red"

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=7,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.9,
                    popup=item.get("name", "")
                ).add_to(m)

            # -----------------------------
            # FIX: Auto-zoom to full route extent
            # -----------------------------
            bounds = [
                [min(item["lat"] for item in self.ordered_route),
                min(item["lon"] for item in self.ordered_route)],
                [max(item["lat"] for item in self.ordered_route),
                max(item["lon"] for item in self.ordered_route)]
            ]
            m.fit_bounds(bounds)

            map_path = os.path.abspath("route_map.html")
            m.save(map_path)
            self.map_view.load(QUrl.fromLocalFile(map_path))

        except Exception as e:
            show_info_popup(self, "Fehler", f"Highlight error:\n{e}")


    def build_map_from_ordered_route(self):
        coords = [[r["lon"], r["lat"]] for r in self.ordered_route]
        lon, lat = coords[0]

        client = ors.Client(key=ORS_API_KEY)
        route_geojson = client.directions(
                coordinates=coords,
                profile=self.current_profile,
                format="geojson"
        )

        self.last_route_geojson = route_geojson

        m = folium.Map(location=[lat, lon], zoom_start=13)
        folium.GeoJson(route_geojson).add_to(m)

        map_path = "route_map.html"
        m.save(map_path)
        self.map_view.load(QUrl.fromLocalFile(os.path.abspath(map_path)))

    def build_stats_from_ordered_route(self):
        total_km, total_min, segments = compute_route_stats(
            self.ordered_route,
            ORS_API_KEY,
            self.current_profile
        )
        # Fill your stats table here

    def update_table(self, ordered):
        self.routeOrderTable.setRowCount(len(ordered))

        for i, d in enumerate(ordered):
            self.routeOrderTable.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.routeOrderTable.setItem(i, 1, QTableWidgetItem(d.get("strasse", "")))
            self.routeOrderTable.setItem(i, 2, QTableWidgetItem(d.get("hausnummer", "")))

        self.routeOrderTable.setAlternatingRowColors(True)
        self.routeOrderTable.setSortingEnabled(True)
        self.routeOrderTable.resizeColumnsToContents()

    def update_stats(self, total_km, total_min, segments):
        total_hours = round(total_min / 60, 2)

        labels = [
            "Driving Distance",
            "Driving Time",
            "Walking Distance",
            "Walking time (hours)",
            "Walking time (minutes)",
            "Total Distance",
            "Total Time",
            "Weekly (6 days)",
            "Weekly (5 days)",
            "Monthly"
        ]

        values = [
            f"{total_km:.1f} km",
            f"{total_hours:.1f} Stunden",
            f"0.00 km",
            f"0.00 Stunden",
            f"0.00 Minuten",
            f"{total_km:.1f} km",
            f"{total_hours:.1f} Stunden",
            f"{total_hours * 6:.1f} Stunden",
            f"{total_hours * 5:.1f} Stunden",
            f"{total_hours * 26.09:.1f} Stunden"
        ]

        self.routeTable.setRowCount(len(labels))

        for i in range(len(labels)):
            self.routeTable.setItem(i, 0, QTableWidgetItem(labels[i]))
            self.routeTable.setItem(i, 1, QTableWidgetItem(values[i]))


    def update_map(self, geojson):
        first = self.ordered_route[0]
        m = folium.Map(location=[first["lat"], first["lon"]], zoom_start=25)

        folium.GeoJson(geojson, name="Optimierte Route").add_to(m)

        for d in self.ordered_route:
            folium.CircleMarker(
                location=[d["lat"], d["lon"]],
                radius=6,
                color="red",
                fill=True,
                fill_color="red",
                fill_opacity=0.9
            ).add_to(m)

        map_path = os.path.abspath("route_map.html")
        m.save(map_path)
        self.map_view.load(QUrl.fromLocalFile(map_path))


            


