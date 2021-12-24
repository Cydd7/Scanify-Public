from flask import Flask, request
from google.cloud import vision
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
# from httplib2 import oauth2client

import urllib.request
import gspread
import io
import re
import os
import json

#______________________________________________________________________________

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/cloud-vision']

creds = ServiceAccountCredentials.from_json_keyfile_name('client_secrets_gs.json', scope)
client = gspread.authorize(creds)

# client_id='943560631298-bh7ls831or935i1j0mvf55nb7p8cqokd.apps.googleusercontent.com'
# client_secrets='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'
# refresh_token='1//04FIvzLcxXU44CgYIARAAGAQSNwF-L9IrstWIMwksEjdt-7bAEgWJvge3oqVTd3pDAOEvVnQ9NJbDHEocBY2z3EHF8lvfHgEoWXs'

# Automating pydrive authentication process
gauth = GoogleAuth()
# Try to load saved client credentials
gauth.LoadCredentialsFile("mycreds.txt")
if gauth.credentials is None:
    # Authenticate if they're not there
    gauth.GetFlow()
    gauth.flow.params.update({'access_type': 'offline'})
    gauth.flow.params.update({'approval_prompt': 'force'})

    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    # Refresh them if expired
    gauth.Refresh()
else:
    # Initialize the saved creds
    gauth.Authorize()
# Save the current credentials to a file
gauth.SaveCredentialsFile("mycreds.txt")

# Opening google drive in drive
drive = GoogleDrive(gauth)

#______________________________________________________________________________

def detect_container_vision():
    # Creating GOOGLE_APPLICATION_CREDENTIALS enviroment from
    # "client_secrets_gs.json" file. These creds are associated with gcp of
    # 17uec122@lnmiit.ac.in
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="client_secrets_gs.json"

    #Processing the image
    client = vision.ImageAnnotatorClient()
    fn=os.path.join(os.path.dirname(__file__),'cn1.jpeg')

    with io.open(fn, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    ans=texts[0].description
    ans = ''.join(ans.split())

    # Using RegEx to find container number
    containerNoRegex = re.compile(r'([A-Z]{4})(\d{7})')
    mo = containerNoRegex.search(ans)
    cont = mo.group(1)+" "+mo.group(2)

    return cont

def detect_vehicle_plate_vision():
    # Creating GOOGLE_APPLICATION_CREDENTIALS enviroment from
    # "client_secrets_gs.json" file. These creds are associated with gcp of
    # 17uec122@lnmiit.ac.in
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="client_secrets_gs.json"

    # Processing the image
    client = vision.ImageAnnotatorClient()
    fn=os.path.join(os.path.dirname(__file__),'vn1.jpeg')

    with io.open(fn, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    ans=texts[0].description
    ans = ''.join(ans.split())

    # Using RegEx to find Vehicle number
    vehicleNoRegex = re.compile(r'[A-Z]{2}[-_.]{0,1}\d{1,2}[-_.]{0,1}[A-Z]{1,3}\d{4}')
    mo = vehicleNoRegex.search(ans)
    vehNo = mo.group()

    return vehNo

#______________________________________________________________________________

#Starting the flask app
app = Flask(__name__)

# Home
@app.route('/')
def hello_world():
    return 'Welcome to Scanify\'s back-end server'

# Creating an endpoint to detect container image by taking in arguments:
# id -> Drive id of the uploaded image
# row -> Row number of the updated cell
@app.route('/detect_container')

def detectcn():

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("TestApp").sheet1

    #get row of updated cell and id of the image from the URL
    row = request.args.get('row')
    id = request.args.get('id')

    # Using pyDrive to fectch the container image from the google drive with
    # the help of it's id and downloading the file as 'cn1.jpeg'.
    file6 = drive.CreateFile({'id': id})
    file6.GetContentFile('cn1.jpeg')
    #file6.FetchMetadata(field='permissions')

    # Returning container number from function detect_container_vision in textr
    textr=detect_container_vision()
    # Update the text in the sheet from here only
    sheet.update_cell(row, 2, textr)

    return "Done Container"

# Creating an endpoint to detect vehicle plate image by taking in arguments:
# id -> Drive id of the uploaded image
# row -> Row number of the updated cell
@app.route('/detect_vehicle_plate')

def detectvp():

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("TestApp").sheet1

    #get row of updated cell and id of the image from the URL
    row = request.args.get('row')
    id = request.args.get('id')

    # Using pyDrive to fectch the vehicle plate image from the google drive with
    # the help of it's id and downloading the file as 'vn1.jpeg'.
    file6 = drive.CreateFile({'id': id})
    file6.GetContentFile('vn1.jpeg')
    #file6.FetchMetadata(field='permissions')

    # Returning container number from function detect_vehicle_plate_vision in textr
    textr=detect_vehicle_plate_vision()
    #Update the text in the sheet from here only
    sheet.update_cell(row, 3, textr)

    return "Done Vehicle Plate"

if __name__ == '__main__':
    app.run(debug=True,port=8000)
