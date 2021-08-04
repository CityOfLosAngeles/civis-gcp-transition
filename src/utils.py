"""
Utility functions
"""
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection

# Overwrite ESRI layer
def update_geohub_layer(geohubUrl, user, pw, layer, update_data):
    """
    user: str, ESRI username
    pw: str, ESRI password
    layer: str, ESRI feature layer ID
    update_data: path to local CSV data used to overwrite feature layer
                ex: "./file_name.csv"
    """

    #geohub = GIS('https://lahub.maps.arcgis.com', user, pw)
    geohub = GIS(geohubUrl, user, pw)
    flayer = geohub.content.get(layer)
    flayer_collection = FeatureLayerCollection.fromitem(flayer)
    flayer_collection.manager.overwrite(update_data)
    print("Successfully updated AGOL")
    
    
# Function to update feature layer, line by line
def chunks(list_of_features, n, agol_layer):
    """
    Yield successive n-sized chunks from list_of_features.
    list_of_features: list. List of features to be updated.
    n: numeric. chunk size, 1000 is the max for AGOL feature layer
    agol_layer: AGOL layer.
                Ex: 
                flayer = gis.content.get(feature_layer_id)
                agol_layer = flayer.layers[0]
    """
    for i in range(0, len(list_of_features), n):
        chunk_list=list_of_features[i:i + n]
        agol_layer.edit_features(updates=chunk_list)
        print("update successful")