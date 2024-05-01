# Source: https://github.com/prestinomills/aqueduct/blob/Know_Your_Community_Pipelines/civis/geohub/ActiveBusinessBlockgroupAggregation/Active_Business_Finalized_Script.py
# %load active_business_script.py
"""
Created on Wed May  1 08:51:03 2019
@author: myrfid041
"""
import geopandas as gpd
import os
import pandas as pd

from civis_aqueduct_utils.github import upload_file_to_github
from common_utils import utils

from sodapy import Socrata
from arcgis.gis import GIS
from arcgis.features import FeatureLayer, FeatureLayerCollection
from copy import deepcopy

LAHUB_USER = os.environ["LAHUB_ACC_USERNAME"]
LAHUB_PASS = os.environ["LAHUB_ACC_PASSWORD"]

#---Setting the Outputs
OUTPUT_FILE = "./Listing_of_Active_Businesses.csv"
OUTPUT_LAYER_NAME = "067a9242fbef4afeb1ca0744952e5724"

# Grab the Socrata dataset for active businesses
client = Socrata("data.lacity.org", None)
abiz = pd.DataFrame(client.get('ngkp-kqkn', limit=10_000_000))

# Constants for loading the file to GitHub
TOKEN = os.environ["GITHUB_TOKEN_PASSWORD"]
REPO = "CityOfLosAngeles/data-team-wiki"
BRANCH = "master"

DEFAULT_COMMITTER = {
    "name": "Los Angeles ITA data team",
    "email": "ITAData@lacity.org",
}


def dataprep(df, branch="master"):

    # Pull NAICS Industry Table
    n_table=(
        'https://raw.githubusercontent.com/CityofLosAngeles/civis-gcp-transition/{}/'
        'data/naics_industry_table.csv'
    )
    naics_table=pd.read_csv(n_table.format(branch))

    # Grab location info
    df = (df.dropna(subset=['location_1', 'naics'])
        .assign(
            location_2 = df.location_1.astype(str).str[34:-2]
        )
    )

    df = df.assign(
        longitude = df.location_2.str.split(",", expand=True)[0].astype(float),
        latitude = df.location_2.str.split(",", expand=True)[1].astype(float),
        naics_sector = df.naics.str[:2].astype(str),
    ).dropna(subset=["longitude", "latitude"])

    # Merge in NAICS sector
    df2 = pd.merge(df, 
                   naics_table.assign(
                       naics_sector = naics_table.naics_sector.astype(str)
                   ), 
            how = 'inner', on = 'naics_sector', validate = 'm:1'
            )

    # Create geometry column
    gdf = gpd.GeoDataFrame(df2.dropna(subset=['longitude', 'latitude']), 
        geometry = gpd.points_from_xy(df2.longitude, df2.latitude),
                                      crs = "EPSG:4326"
    ).to_crs("EPSG:2229") # Change to CA State Plane

    # Import block groups
    block_group_file=(
        'https://raw.githubusercontent.com/CityofLosAngeles/civis-gcp-transition/{}/'
        'data/LACounty_Blockgroup.geojson'
    )
    block = gpd.read_file(block_group_file.format(branch))

    # Aggregate
    sjoin=gpd.sjoin(gdf, block, how='inner', op='intersects')
    
    sjoin = sjoin.assign(
        GEOID10 = sjoin.GEOID10.astype(str).apply(lambda x: '{0:0>12}'.format(x))
    )

    sjoin2=(sjoin.pivot_table(index='GEOID10', 
                    values='business_name',
                    columns=['naics_industry'], 
                    aggfunc=len)
        .reset_index()
        .fillna(0)
        .rename_axis(None, axis="columns")
    )
    
    return sjoin2


def top10(df):
    '''
    Find the top 10 predominant industries in entire county
    Exclude 2 categories
    Return a list (used to update feature layer item property)
    df: pandas.DataFrame. Use the output returned from `dataprep()`.
    '''
    
    county_aggregate = (
        pd.DataFrame(df.set_index("GEOID10")
                     .idxmax(axis=1))
        .reset_index()
        .rename(columns = {0: "predominant_industry"})
    )
    
    # Get a list, descending order
    predominant_industries = (county_aggregate.predominant_industry.value_counts()
                              .index
                              .to_list()
                             )
    
    # Exclude these categories, then grab top 10
    exclude_me = ['Professional, Scientific, and Technical Services', 
              'Other Services (except Public Administration)']
    for i in exclude_me:
        predominant_industries.remove(i)
    
    top10_industries = predominant_industries[0:10]
    
    return top10_industries


'''
ESRI stores the column names slightly differently (subject to 10 char limits)
Use dict to map and rename (key-value pair)
Key: dataframe's existing column name
Value: ESRI column name
'''
LAYER_RENAME_COLUMNS_DICT = {
    'Accommodation and Food Services': 'Accommodation_and_Food_Services',
    'Administrative and Support and Waste Management and Remediation Services': 'Administrative_and_Support_and_',
    'Agriculture, Forestry, Fishing and Hunting': 'Agriculture__Forestry__Fishing_',
    'Arts, Entertainment, and Recreation': 'Arts__Entertainment__and_Recrea',
    'Construction': 'Construction',
    'Educational Services': 'Educational_Services',
    'Finance and Insurance': 'Finance_and_Insurance',
    'Health Care and Social Assistance': 'Health_Care_and_Social_Assistan',
    'Information': 'Information',
    'Manufacturing': 'Manufacturing',
    'Medical Marijuana Collective': 'Medical_Marijuana_Collective',
    'Mining': 'Mining',
    'Not Classified': 'Not_Classified',
    'Other Services (except Public Administration)': 'Other_Services__except_Public_A',
    'Professional, Scientific, and Technical Services': 'Professional__Scientific__and_T',
    'Real Estate Rental and Leasing': 'Real_Estate_Rental_and_Leasing',
    'Retail Trade': 'Retail_Trade',
    'Transportation and Warehousing': 'Transportation_and_Warehousing',
    'Utilities': 'Utilities',
    'Wholesale Trade': 'Wholesale_Trade'                                               
}


def geohub_updates(df,user,pas, feature_layer_id, 
        top10_industries, column_renaming_dict, OUTPUT_FILE):
    """
    df: pandas.DataFrame. Input the df that is returned from `dataprep()`
    user: str. AGOL username
    pas: str. AGOL password
    feature_layer_id: str. The feature layer ID of the AGOL layer.
    top10_industries: list.
    column_renaming_dict: dict. The dictionary to map our df column names to how it's stored in AGOL.
    OUTPUT_FILE: str. The path to where the local CSV is stored, will be checked into GitHub.
    """
    gis = GIS('https://lahub.maps.arcgis.com', username=user, password=pas)
    flayer = gis.content.get(feature_layer_id)
    ActiveBusinesses_flayer = flayer.layers[0]
    ActiveBusinesses_fset = ActiveBusinesses_flayer.query() #querying without any conditions returns all the features    
    
    # Grab the spatial dataframe in the layer
    # Drop the GEOID10s that don't have a match in the existing sdf
    # Only keep the columns to update (various industries), and leave geometry columns intact
    existing_table = ActiveBusinesses_fset.sdf
    
    industry_cols = list(column_renaming_dict.values())
    
    new_updated_table = (df[df.GEOID10.isin(existing_table.GEOID10)]
                         .rename(columns = column_renaming_dict)
                     [["GEOID10"] + industry_cols]
                    )
    new_updated_table[industry_cols] = new_updated_table[industry_cols].fillna(0).astype(int)
    
    updated_values_dict = new_updated_table.set_index("GEOID10").to_dict(orient="index")
    
    # Grab the features, save as a list. It's actually a list, but each element in the list is a dictionary.
    feature_list = ActiveBusinesses_fset.features
   
    # Loop through each GEOID, then loop through the columns, and update the values
    # Use try/except because there are some GEOIDs in the original sdf that aren't in our df (about 10ish)
    # Leave these with original values, since we don't have updated values
    updated_features = []
    for i in range(0, len(feature_list)):
        original_feature = [f for f in feature_list][i]
        feature_to_be_updated = deepcopy(original_feature)
        attributes_to_update = feature_to_be_updated.attributes
        geoid = attributes_to_update["GEOID10"]
        try:
            for col in industry_cols:
                '''
                This doesn't work: 
                feature_to_be_updated[col] = updated_values_dict[geoid][col]

                feature_to_be_updated[col] = features object...not a dict
                print(type(feature_list[0]))
                print(type(feature_list[0].attributes))

                Somehow, it won't let us key into the dict and change values
                But, since we earlier got into the attributes, we can update the values for each attribute
                https://gis.stackexchange.com/questions/394259/esri-notebook-select-and-append-records-to-table
                '''
                attributes_to_update[col] = int(updated_values_dict[geoid][col])
            updated_features.append(feature_to_be_updated)

        except:
            pass

    # Update the feature layer in chunks of 1000 rows
    utils.chunks(updated_features, 1000, ActiveBusinesses_flayer)

    # Update the AGOL item properties
    text = """
    This layer is aggregating 
    <a href="https://data.lacity.org/A-Prosperous-City/Listing-of-Active-Businesses/6rrh-rzua">
    Listing of Active Businesses Data</a> 
    that have geospatial information associated. 
    The top 10 most frequent industries in block groups are:
    {}
    """
    # In list of frequent industries, let's display as a string, not a list
    x = ', '.join([str(elem) for elem in top10_industries]) 
    item_props = {'title' : 'Active Businesses Data by Block Group', 'description':text.format(x)}
    flayer.update(item_properties=item_props)
    print("item properties updated!")
    
    # Stage the file to check into GitHub
    new_updated_table.to_csv(OUTPUT_FILE, index=False)


# Run it all
if __name__ == "__main__":
    # Import data and clean
    df = dataprep(abiz, branch="master")
    # Grab top 10 industries as a list
    top10_industries = top10(df)
    # Update AGOL, export local CSV
    geohub_updates(df,LAHUB_USER,LAHUB_PASS, OUTPUT_LAYER_NAME, 
        top10_industries, LAYER_RENAME_COLUMNS_DICT, OUTPUT_FILE)
    
    
    # Upload to GitHub
    # the github repo has been archived. no longer need upload_file_to_github (5/1/2024)
    #upload_file_to_github(
    #    TOKEN,
    #    REPO,
    #    BRANCH,
    #    f"ActiveBusinessBlockgroupAggregation/{OUTPUT_FILE.replace('./', '')}",
    #    f"{OUTPUT_FILE}",
    #    f"Update Active Businesses",
    #    DEFAULT_COMMITTER,
    #)
    
    os.remove(OUTPUT_FILE)
