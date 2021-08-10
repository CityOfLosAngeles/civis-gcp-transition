"""
Utility functions related to ArcGIS Online
and SendGrid.
"""
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection

#------------------------------------------------------------------------#
# ArcGIS Online 
#------------------------------------------------------------------------#
# Overwrite ESRI layer
def update_geohub_layer(geohubUrl, user, pw, layer, update_data):
    """
    geohubUrl: str, ex: 'https://lahub.maps.arcgis.com'
    user: str, ESRI username
    pw: str, ESRI password
    layer: str, ESRI feature layer ID
    update_data: path to local CSV data used to overwrite feature layer
                ex: "./file_name.csv"
    """

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
        
        
# Overwrite source file then republish and overwrite hosted feature layer
def overwrite_agol_table_and_publish(geohubUrl, user, pw, layer, local_file_path, local_file_type):        
    """
    user: str, ESRI username
    pw: str, ESRI password
    layer: str, ESRI feature layer ID
    local_file_path: path to local data used to overwrite the table backing the hosted feature layer
                ex: "./file_name.csv"
    
    Reference: 
    What file types are available to be uploaded: 
    https://developers.arcgis.com/python/api-reference/arcgis.gis.toc.html
    """  
    geohub = GIS(geohubUrl, user, pw)
    
    # This is the feature layer ID for the table or file backing the hosted feature layer
    # NOT the hosted feature layer itself
    item = geohub.content.get(layer)
    item.update(data=local_file_path)
    
    # Publishing pushes the table to the hosted feature layer again
    # If overwrite = False, then a new feature layer ID will be created for this "new" hosted feature layer.
    item.publish(overwrite=True, file_type=local_file_type)
    
    
#------------------------------------------------------------------------#
# SendGrid emailing service 
#------------------------------------------------------------------------#
import base64
import json
import urllib.request as urllib

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId)


def sendgrid_simple_html(EMAIL_SENDER, EMAIL_RECIPIENT, EMAIL_SUBJECT, BODY_TEXT, SENDGRID_API):
    """
    EMAIL_SENDER: str, email address
    EMAIL_RECIPIENT: str, email address
    EMAIL_SUBJECT: str
    BODY_TEXT: str, can also include html content
    SENDGRID_API: str, SENDGRID_API_KEY
    """
    message = Mail(
        from_email=EMAIL_SENDER,
        to_emails=EMAIL_RECIPIENT,
        subject=EMAIL_SUBJECT,
        html_content=BODY_TEXT)

    try:
        sg = SendGridAPIClient(SENDGRID_API)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)
        
        
def sendgrid_pdf(EMAIL_SENDER, EMAIL_RECIPIENT, EMAIL_SUBJECT, BODY_TEXT,
                 OUTPUT_DICT, SENDGRID_API):
    """
    OUTPUT_DICT: dict,
                key: output pdf's file path
                value: name of the pdf as displayed as email attachment
    """
    message = Mail(
        from_email=EMAIL_SENDER,
        to_emails=EMAIL_RECIPIENT,
        subject=EMAIL_SUBJECT,
        html_content=BODY_TEXT)
    
    # Attaching 1 pdf and attaching multiple, it's basically same steps
    # Create empty list to store the attachments 
    attachment_list = []
    i = 0
    for key, value in OUTPUT_DICT.items():
        name = f"attachment{i}"
        with open(key, 'rb') as f:
            data = f.read()
            f.close()
        encoded = base64.b64encode(data).decode()
        name = Attachment()
        name.file_content = FileContent(encoded)
        name.file_type = FileType('application/pdf')
        name.file_name = FileName(value)
        name.disposition = Disposition('attachment')
        name.content_id = ContentId(f'Content ID{i}')  
        i += 1
        attachment_list.append(name)
    
    message.attachment = attachment_list

    try:
        sendgrid_client = SendGridAPIClient(SENDGRID_API)
        response = sendgrid_client.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)
    