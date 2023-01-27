"""
KYC 311 to ESRI 

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
#CREDENTIAL = "./ita-datalake-1ba73cf7af69.json"
#CREDENTIAL = "./gcp-credential.json"
#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f'{CREDENTIAL}'
#GCP_PROJECT_ID = 'ita-datalake'
#os.environ['PROJECT_ID'] = f'{GCP_PROJECT_ID}'

# Set GCP Project ID
client = bigquery.Client()
gcp_project = os.environ['PROJECT_ID']

# Use ibis to construct SQL query
# redshift
conn = ibis.bigquery.connect(
    project_id = gcp_project,
    dataset_id = 'publicworks'
)

table = conn.table('import311')

lahub_user = os.environ["LAHUB_ACC_USERNAME"]
lahub_pass = os.environ["LAHUB_ACC_PASSWORD"]

layer = '981076361934439691c2b395896ca99b' #'3eb07324793142c4a0d991084b920349'
OUTPUT_FILE = "./MyLA311 Service Requests Last 6 Months.csv"

def prep_311_data(expr):
    # There seems to be a date issue with ibis
    # Parse the string instead
    # We'll keep up to the last 2 year's of data and use pandas to further subset
    current_year = datetime.datetime.today().year
    prior_year = current_year - 1
    
    # Cast to string
    expr = expr.mutate(createddate=expr.createddate.cast("string"))
    
    expr2 = expr[(expr.createddate.contains(str(current_year))) | 
                 (expr.createddate.contains(str(prior_year)))]

    # Remove specific request types
    expr3 = expr2[expr2.requesttype != "Homeless Encampment"]
    
    # Compile shows the SQL statement
    print(ibis.bigquery.compile(expr3.limit(10)))

    # Execute the query and return a pandas dataframe
    df = expr3.execute(limit=None)
 
    
    print("Successfully executed query")
    
    return df


def clean_data(df, file):
    # Fix dtypes
    df = df.assign(
        createddate = pandas.to_datetime(df.createddate, errors="coerce"),
        updateddate = pandas.to_datetime(df.updateddate, errors="coerce"),
        closeddate = pandas.to_datetime(df.closeddate, errors="coerce"),
        servicedate = pandas.to_datetime(df.servicedate, errors="coerce")
    )
    
    # Subset to keep last 6 month's of data
    today_date = datetime.datetime.today()
    six_months_ago = today_date - pandas.DateOffset(months=6)    
    
    df2 = df[(df.createddate.notna()) & 
             (df.createddate >= six_months_ago)]
    
    # Export to CSV (use local file to upload to AGOL)
    df2.to_csv(file, index=False)
    print("Successfully exported as csv")
    
    
if __name__ == "__main__":
    df = prep_311_data(table)
    clean_data(df, OUTPUT_FILE)
    utils.update_geohub_layer('https://lahub.maps.arcgis.com', lahub_user, lahub_pass, layer, OUTPUT_FILE)