# VolExplore-Diploma-Thesis

This repository includes code and data used for my diploma thesis

<h4 style="text-align:center;">"City navigation website using MongoDB for data management and geospatial querying"</h4>

for the Department of Electrical and Computer Engineering of University of Thessaly.

## About the site
_**VolExplore**_ is a web application that can search Points of Interest (POI) and calculate a route passing through them in the city of Volos. For the geospatial data storage and querying we used MongoDB, a NoSQL database. The users can also create accounts to submit comments to POI, while an administrative account can also add or update POI in the database (So far a user can be registered as an administrator only via direct access to the database). For the backend-frontend communication, Flask was used. The app is meant to run locally. More information and proper citations are included in the paper.

## About the data
The geospatial data used by this project was collected from OpenStreetMap using the OSMnx library. The unprocessed data can be found in the ["OSMnx_unprocessed_data"](OSMnx_unprocessed_data) directory. The way the data was collected can be seen in the ["dataOSMN.py](scripts/dataOSMN.py) file. The raw data was then refined manually for the requirements of the app, and can be found in their final forms in the ["processed_data"](processed_data) directory. These are the ones used by the app itself and saved in the database.

## About the files included
Aside from the data files and the script mentioned in the previous paragraph there are other files.
- The ["static"](static) directory includes a custom css file and a directory with images used for some extra design customisation.
- The ["templates"](templates) directory includes all the HTML files used by Flask to render each page.
- ["constants.py"](constants.py) includes the radians to metres coefficient used in some calculations
- ["custom_query.py"](custom_query.py) includes all the python methods that queried MondoDB, whether it be geospatial or not queries.
- ["utils.py"](utils.py) includes the rest of the python methods that mostly involved data manipulation
- And lastly, ["volExplore.py"](volExplore.py) is the main code file

## How to run the app
To run the app first you would need to insert in a MongoDB database the JSON files. Then you would need to set up the environment according to the requirements listed [here](requirements.txt). Then to finally run the app you need to use the following command in a terminal in the main directory of the app:

```flask --app volExplore.py run```

Then as instructed, you can view the site itself by following the link provided in the terminal
