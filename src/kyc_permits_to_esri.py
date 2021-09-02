"""
KYC Permit Data to ESRI 

Connect to BigQuery.
Export as ESRI layer.
"""
import datetime
import ibis
import os
import pandas

from common_utils import utils
from google.cloud import bigquery

#Set GCP credentials only for local testing 
#CREDENTIAL = "./gcp-credential.json"
#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f'{CREDENTIAL}'

client = bigquery.Client()


# Use ibis to construct SQL query
conn = ibis.bigquery.connect(
    project_id = 'ita-datalakepoc',
    dataset_id = 'redshift'
)

table = conn.table('kyc_ladbs_permits')

lahub_user = os.environ["LAHUB_ACC_USERNAME"]
lahub_pass = os.environ["LAHUB_ACC_PASSWORD"]

layer = '48fca217dd5a410bbfd6ce0abcdd3a26'
OUTPUT_FILE = "./Building and Safety Permits Last 6 Months.csv"

def prep_permit_data(expr):
    # There seems to be a date issue with ibis
    # Parse the string instead
    # We'll keep up to the last 2 year's of data and use pandas to further subset
    current_year = datetime.datetime.today().year
    prior_year = current_year - 1
    
    expr = expr.mutate(issue_date=expr.issue_date.cast("string"))
    
    expr2 = expr[(expr.issue_date.contains(str(current_year))) | 
                 (expr.issue_date.contains(str(prior_year)))]

    # Select specific permit types
    permit_sub_categories = ["Apartment", "Commercial"]
    permit_type = ["Bldg-Addition", "Bldg-New", "Bldg-Demolition"]
    
    expr3 = expr2[(expr2.permit_sub_type.isin(permit_sub_categories)) & 
                 (expr2.permit_type.isin(permit_type))]
    
    
    # Compile shows the SQL statement
    print(ibis.bigquery.compile(expr3.limit(10)))

    # Execute the query and return a pandas dataframe
    df = expr3.execute(limit=None) 
    
    print("Successfully executed query")
    
    return df


def clean_data(df, file):
    # Fix dtypes
    df = df.assign(
        issue_date = pandas.to_datetime(df.issue_date),
    )
    
    # Subset to keep last 6 month's of data
    today_date = datetime.datetime.today()
    six_months_ago = today_date - pandas.DateOffset(months=6)    
    
    df2 = df[(df.issue_date.notna()) & 
             (df.issue_date >= six_months_ago)]
    
    # Export to CSV (use local file to upload to AGOL)
    df2.to_csv(file, index=False)
    print("Successfully exported as csv")

    
if __name__ == "__main__":
    df = prep_permit_data(table)
    clean_data(df, OUTPUT_FILE)
    utils.update_geohub_layer('https://lahub.maps.arcgis.com', lahub_user, lahub_pass, layer, OUTPUT_FILE)