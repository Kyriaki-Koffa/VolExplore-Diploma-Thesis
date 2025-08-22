import math
from typing import List, Dict
import random
import datetime
from copy import deepcopy

# additional methods

# finds the distance in metres between two points when given their coordinates
def getDistanceFromLatLonInM(lat1, lon1, lat2, lon2):
    R = 6371000 # Radius of the earth in m
    dLat = deg2rad(lat2-lat1)  # deg2rad below
    dLon = deg2rad(lon2-lon1) 
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
 
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c # Distance in m
    return d

# converts degrees to radians
def deg2rad(deg):
    return deg * (math.pi/180)

# finds the centre point's coordinates between two points and its distance from them
def centreQ(start_lat, start_lng, end_lat, end_lng):
    lat = (start_lat + end_lat)/2
    lng = (start_lng + end_lng)/2
    radius = getDistanceFromLatLonInM(start_lat, start_lng, end_lat, end_lng)/2

    return(lat, lng, radius)

# reformats the route coordinates to be usable by frontend (they are sometimes jumbled up, and in mongoDB coordinates are saved in [lng, lat] pairs)
def ReRoute(route):

    reRouted = []
    tempRoute = []

    for i, part in enumerate(route):
        if i == 0:
            if i != len(route)-1:
                # LOOK IF THE LAST COORDSET OF THE FIRST PART EXISTS IN THE NEXT PART. IF IT DOES NOT THEN REVERSE
                if (part[-1] != route[i+1][0]) and (part[-1] != route[i+1][-1]):
                    temp = deepcopy(part)
                    temp.reverse()
                    tempRoute.append(temp) # the first part definitely belongs
                else:
                    temp = deepcopy(part)
                    tempRoute.append(temp)
        else:
            if part[0] != tempRoute[len(tempRoute)-1][-1]:
                # we want the first coordset to match the last coordset of the last edge path thing
                temp = deepcopy(part)
                temp.reverse()
                tempRoute.append(temp)
            else:
                temp = deepcopy(part)
                tempRoute.append(temp)
    
    for i, part in enumerate(tempRoute):
        for coordSet in part:
            temp = deepcopy(coordSet)
            temp.reverse()
            reRouted.append(temp)
    
    return reRouted

# creates the POI type "or" query based on the types received from the frontend filter
def str_filterBldr(type_filter: List[str]) -> List[Dict]:
    query_key = "properties.type"
    final_filterQuery = []
    for typeName in type_filter:
        final_filterQuery.append({query_key: typeName})
    return final_filterQuery

# takes all the osmids of the POI in the list of the POI left for visitation and builds the or query
def NodeorQuery(poiNodeList):
    query_key = "properties.osmid"
    finalOrQuery = []
    for node in poiNodeList:
        if isinstance(node, dict):
            finalOrQuery.append({query_key: node['properties']['osmid']})
        else:
            for polNode in node:
                finalOrQuery.append({query_key: polNode['properties']['osmid']})
    return finalOrQuery

# generates a POID for any new POI added based on type, date of addition and a random four digit number added at the end
def generatePOID(typePOI):
    poid = ""
    if typePOI == "Archaeological_Site":
        poid = "ARC"
    elif typePOI == "Arts_Centre":
        poid = "ART"
    elif typePOI == "Castle":
        poid = "CAS"
    elif typePOI == "Fountain":
        poid = "FNT"
    elif typePOI == "Historic":
        poid = "HIS"
    elif typePOI == "Memorial":
        poid = "MEM"
    elif typePOI == "Museum":
        poid = "MSM"
    elif typePOI == "Park":
        poid = "PRK"
    elif typePOI == "Playground":
        poid = "PGR"
    elif typePOI == "Recreational_Ground":
        poid = "REC"
    elif typePOI == "Tourist_Attraction":
        poid = "TRS"
    elif typePOI == "Viewpoint":
        poid = "VPT"
    
    today = datetime.date.today()
    poid = poid + today.strftime('%y%m%d') + str(random.randint(0, 9999))

    return poid