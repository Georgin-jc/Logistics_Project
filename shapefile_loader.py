import geopandas as gpd
import folium

def load_shapefile(path):
    gdf = gpd.read_file(path)
    return gdf.to_json()

def add_shapefile_layer(map_obj, geojson_data, layer_name):
    fg = folium.FeatureGroup(name=layer_name, show=False)
    folium.GeoJson(geojson_data, name=layer_name).add_to(fg)
    fg.add_to(map_obj)
