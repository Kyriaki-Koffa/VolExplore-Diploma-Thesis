import networkx as nx
import osmnx as ox
import matplotlib as plt
import geopandas as gpandas
from pathlib import Path
import os

# OSMNX Bootstrapping
ox.__version__

#What I need is 1. STREET NETWORK
#2. AMENITY: ARTS_CENTRE, COMMUNITY_CENTRE, FOUNTAIN   BARRIER: CITY_WALL    BUILDING: MUSEUM, CASTLE     HISTORIC: YES   TOURISM: YES
#3. LANDUSE: GRASS, RECREATION_GROUND   LEISURE: BEACH_RESORT, GARDEN. PARK, PLAYGROUND, TRACK, SWIMMING_AREA   WATER: YES

currentDir = Path(os.getcwd()).resolve()

volos_streetNW = ox.graph_from_place("Volos", network_type="all")
volos_streetNW_N = ox.graph_to_gdfs(volos_streetNW, edges=False)
volos_streetNW_E = ox.graph_to_gdfs(volos_streetNW, nodes=False)

#THESE ALSO RETURN GEODATAFRAMES
volos_POI = ox.features_from_place(
    "Volos", 
    {
        'amenity' : ['arts_centre', 'community_centre', 'fountain'],
        'barrier' : 'city_wall', 
        'building': ['museum', 'castle'],
        'historic' : True,
        'tourism' : ['artwork', 'attraction', 'gallery', 'museum', 'viewpoint'] 
    }
)
volos_PS = ox.features_from_place(
    "Volos", 
    {
        'landuse' : ['grass', 'recreation_ground'], 
        'leisure' : ['beach_resort', 'garden', 'park', 'playground']
    }
)

dataDir = currentDir / "data"
os.makedirs(currentDir / "data", exist_ok=True)

volos_streetNW_N.to_file((dataDir / "streetNW_Volos_nodes.json").absolute(), driver="GeoJSON")
volos_streetNW_E.to_file((dataDir / "streetNW_Volos_edges.json").absolute(), driver="GeoJSON")

volos_POI.to_file((dataDir / "POI_Volos.json").absolute(), driver="GeoJSON")
volos_PS.to_file((dataDir / "PS_Volos.json").absolute(), driver="GeoJSON")
