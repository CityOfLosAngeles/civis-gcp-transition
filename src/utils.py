"""
Utility functions
"""
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection

# Overwrite ESRI layer
def update_geohub_layer(user, pw, layer, update_data):
    """
    user: str, ESRI username
    pw: str, ESRI password
    layer: str, ESRI feature layer ID
    update_data: path to local CSV data used to overwrite feature layer
                ex: "./file_name.csv"
    """

    geohub = GIS('https://lahub.maps.arcgis.com', user, pw)
    flayer = geohub.content.get(layer)
    flayer_collection = FeatureLayerCollection.fromitem(flayer)
    flayer_collection.manager.overwrite(update_data)
    print("Successfully updated AGOL")