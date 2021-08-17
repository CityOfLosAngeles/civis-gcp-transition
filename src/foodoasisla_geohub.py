"""
Food Oasis to ESRI 

Connect to Food Oasis API.
Export as ESRI layer.
"""
import requests
import pandas
import os

from common_utils import utils

lahub_user = os.environ["LAHUB_ACC_USERNAME"]
lahub_pass = os.environ["LAHUB_ACC_PASSWORD"]

URL = "https://foodoasis.la/api/stakeholderbests?categoryIds[]=1&categoryIds[]=9&latitude=33.99157326008516&longitude=-118.25853610684041&distance=5&isInactive=either&verificationStatusId=0&maxLng=-117.83718436872704&maxLat=34.193301591847344&minLng=-118.67988784495431&minLat=33.78936487151597&tenantId=1"
OUTPUT_FILE = "./Food Oasis LA.csv"
fla_layer = 'b3a61e62a98d46ecb078aca873fa1eae'

category_type_dict = {
    "FPF": "Food Pantry",
    "MPF": "Meal Program",
    "OTF": "Other",
    "SHF": "Shelter",
    "FBF": "Food Bank",
    "CCF": "Care Center",
    "UKF": "Unknown",
    "CGF": "Community Garden",
}

def foodoasisla(json, output):
    r = requests.get(json)
    j = r.json()
    df = pandas.DataFrame.from_dict(j)
    #fix column that looks like a dictionary
    split_df = (pandas.DataFrame.from_records(df.categories)
                         .rename(columns = 
                                 {0: "one", 1: "two", 2: "three", 3: "four"}
                                )
                        )
    # Need cleaning, since one row can have up to 4 different entires with the `categories` column
    category_df = pandas.DataFrame()
    for col in ["one", "two", "three", "four"]:
        # This apply function unpacks all the dictionary key/value pairs
        # However many items are in there, it'll create new columns for it
        this_col_df = split_df[col].apply(pandas.Series)
        print("Unpack our dictionary")
        category_df = category_df.append(this_col_df, sort=False)
        
        
    # Clean up, drop NaN values
    category_df = (category_df[category_df.stakeholder_id.notna()]
                   .reset_index(drop=True)
                   .drop(columns = ["id", "display_order"])
                    .rename(columns = {"name": "category_name"})
                   .astype({"stakeholder_id": int})
                  )
    df2 = pandas.merge(df, 
                   category_df, 
                   left_on = "id", 
                   right_on = "stakeholder_id",
                   validate = "1:m"
              ).drop(columns = ["categories"])
    
    # Create a string that captures all the possible categories for each stakeholder ID
    df2['categories'] = (df2[['id','category_name']]
            .groupby(['id'])['category_name'].transform(lambda x: ' & '.join(x))
    )

    # Drop duplicate obs 
    df3 = df2.drop_duplicates(subset = ['id'])
    
    # Create dummy variables flagging various categories
    for key, value in category_type_dict.items():
        df3 = df3.assign(
            new_col = df3.apply(lambda x: value in x.categories, axis=1).astype(int)
        ).rename(columns = {"new_col": f"{value} Flag"})

    keep_cols = [
        'name','categories','address1','address2','city','state','zip','phone',
        'latitude','longitude','website','notes',
        'email','facebook','twitter','pinterest','linkedin',
        'description','donationSchedule','donationDeliveryInstructions','donationNotes',
        'covidNotes','categoryNotes','eligibilityNotes','isVerified',
        'Food Pantry Flag', 'Meal Program Flag', 'Other Flag', 'Shelter Flag', 
        'Food Bank Flag', 'Care Center Flag', 'Unknown Flag', 'Community Garden Flag'
    ]

    fla = df3[keep_cols].copy()
    
    fla.index.name='UNIQID'
    fla.to_csv(output)
    print("Successfully exported as csv")

    
if __name__ == "__main__":
    foodoasisla(URL, OUTPUT_FILE)
    utils.update_geohub_layer('https://lahubcom.maps.arcgis.com', lahub_user, lahub_pass, fla_layer, OUTPUT_FILE)