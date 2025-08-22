from flask_pymongo import PyMongo
from pymongo import MongoClient, cursor
from pymongo.collection import Collection
import math
import networkx as nx
import matplotlib.pyplot as plt
import utils as U
import datetime
from copy import deepcopy

# .py file that includes all methods that query the database

# find all POI within the circle O([lng, lat], dist) that have the POI type(s) specified in filter
def pointQ(collection: Collection, filter, lat, lng, dist):
    # Make a list of Dictionaries to complete the or statement
    finalOrQuery = U.str_filterBldr(filter)
    return collection.find({
        '$and': [
            {
                '$or': finalOrQuery
            },
            {
                'geometry': {
                    '$geoWithin': {
                        '$centerSphere': [
                            [
                                lng, lat
                            ], dist
                        ]
                    }
                }
            }
        ]
    }, {'_id': 0}).to_list()

# assigns the nearest node from the graph to a set of coordinates provided (used for starting and ending point of route)
def find_nearest_node(nodes: Collection, lat, lng):
    return nodes.find_one({
            "geometry" : {
                "$near" : {
                    "$geometry" : { "type" : "Point", "coordinates" : [lng, lat] },
                    "$maxDistance" : 100
                }
            }
    })

# assigns a node from the graph to a POI
def poiToNode(nodes: Collection, coords, geometryType, cLat, cLng):
    if geometryType == "Point":
        # POI is point type, so find nearest node
        return nodes.find_one({
            'geometry': {
                '$near': {
                    '$geometry': {
                        'type': 'Point', 
                        'coordinates': coords
                    }, 
                    '$maxDistance': 120
                }
            }
        }, {'properties.street_count': 0, 'properties.highway': 0, 'properties.ref': 0})
    else:
        # POI is polygon type, so find the corner closest to centre of search radius and from there assign a node
        finalNodeCoords = None
        dist = 100000
        for coordinateArray in coords:
            for coordSet in coordinateArray:
                # find the closest to the centre node equivalent to the POI
                tempDist = U.getDistanceFromLatLonInM(coordSet[1], coordSet[0], cLat, cLng)
                if dist > tempDist:
                    dist = tempDist
                    finalNodeCoords = coordSet
        return nodes.find_one({
                    'geometry': {
                        '$near': {
                            '$geometry': {
                                'type': 'Point', 
                                'coordinates': finalNodeCoords
                            }, 
                            '$maxDistance': 120
                        }
                    }
                }, {'properties.street_count': 0, 'properties.highway': 0, 'properties.ref': 0})

# fetch all the edges/roads from the database to build local graph. The area pulled from is the circle defined by the centre being middle point of the line made by the
# starting and ending point of the path, and the radius being the half of the distance between those two points
def get_SNWedges(edges: Collection, lat, lng, radius):
    return edges.aggregate([
            {
            '$geoNear': {
                'near': {
                    'type': 'Point', 
                    'coordinates': [
                        lng, lat
                    ]
                }, 
                'distanceField': 'string', 
                'maxDistance': radius, #METRES
                'query': {}, 
                'spherical': 'True'
            }
            },{
            '$match': {
                'geometry': {
                    '$geoWithin': {
                        '$centerSphere': [
                            [
                                lng, lat
                            ],
                            radius
                        ]
                    }
                }
            }
            }, {
                '$lookup': {
                    'from': 'Street_Network_Nodes', 
                    'localField': 'properties.u', 
                    'foreignField': 'properties.osmid', 
                    'pipeline': [
                        {
                            '$unset': [
                                'properties.street_count', 'properties.highway', 'properties.ref'
                            ]
                        }
                    ], 
                    'as': 'properties.nodeU'
                }
            }, {
                '$lookup': {
                    'from': 'Street_Network_Nodes', 
                    'localField': 'properties.v', 
                    'foreignField': 'properties.osmid', 
                    'pipeline': [
                        {
                            '$unset': [
                                'properties.street_count', 'properties.highway', 'properties.ref'
                            ]
                        }
                    ], 
                    'as': 'properties.nodeV'
                }
            }
        ]).to_list()

# sorting algorithm for the nodes that dictates the visitation order
def sortNodes(nodes: Collection, start, finish, poiNodeList, diametre):

    poiNum = len(poiNodeList)
    dupNodeList = deepcopy(poiNodeList)

    # visitation list's length is the number of POI to visit plus 2, for the start and the end
    visitationList = [None]*(poiNum+2)
    visitationList[0] = deepcopy(start)
    visitationList[poiNum+1] = deepcopy(finish)

    i=0
    for i in range(poiNum//2):
        q = U.NodeorQuery(dupNodeList)
        # find closest POI node to point A's node
        tempA = nodes.aggregate([
            {
                '$geoNear': {
                    'near': {
                        'type': 'Point', 
                        'coordinates': visitationList[i]['geometry']['coordinates']
                    }, 
                    'distanceField': 'distFromNode', 
                    'maxDistance': diametre, #METRES
                    'query': {
                        '$or': q
                    }, 
                    'spherical': 'True'
                }
            },{
                '$limit' : 1
            }
        ]).to_list()
        # find closest POI node to point B's node that is not the one chosen for point A
        tempB = nodes.aggregate([
            {
                '$geoNear': {
                    'near': {
                        'type': 'Point', 
                        'coordinates': visitationList[poiNum+1-i]['geometry']['coordinates']
                    }, 
                    'distanceField': 'distFromNode', 
                    'maxDistance': diametre, #METRES
                    'query': {
                        '$or': q
                    }, 
                    'spherical': 'True'
                }
            },{
                '$limit' : 2
            }
        ]).to_list()
        visitationList[i+1] = tempA[0]

        # if out of the closest node found is different from the one chosen for point A, we keep it
        if tempA[0]['properties']['osmid'] != tempB[0]['properties']['osmid']:
            visitationList[poiNum-i] = tempB[0]
        # otherwise we keep the second
        else:
            visitationList[poiNum-i] = tempB[1]

        indexA = 0
        indexB = 0
        
        # find the indeces of the nodes submitted into the list
        for u, node in enumerate(dupNodeList):
            if isinstance(node, dict):
                if node['properties']['osmid'] == visitationList[i+1]['properties']['osmid']:
                    indexA = u
                elif node['properties']['osmid'] == visitationList[poiNum-i]['properties']['osmid']:
                    indexB = u
            else:
                for polNode in node:
                    if polNode['properties']['osmid'] == visitationList[i+1]['properties']['osmid']:
                        indexA = u
                    elif polNode['properties']['osmid'] == visitationList[poiNum-i]['properties']['osmid']:
                        indexB = u
        
        # remove them from the list (first th one with the larger index)
        if indexA > indexB:
            del dupNodeList[indexA]
            del dupNodeList[indexB]
        elif indexA < indexB:
            del dupNodeList[indexB]
            del dupNodeList[indexA]
        else:
            del dupNodeList[indexA]

    # only happens if poiNum is an odd number, so there is only one element left in the duplicate poi list
    if dupNodeList:
        q = U.NodeorQuery(dupNodeList)
        tempA = nodes.aggregate([
            {
                '$geoNear': {
                    'near': {
                        'type': 'Point', 
                        'coordinates': visitationList[i]['geometry']['coordinates']
                    }, 
                    'distanceField': 'distFromNode', 
                    'maxDistance': diametre, #METRES
                    'query': {
                        '$or': q
                    }, 
                    'spherical': 'True'
                }
            },{
                '$limit' : 1
            }
        ]).to_list()
        visitationList[(poiNum//2)+1] = tempA[0]

    return visitationList

# fetch all comments in database for item with given POI id
def selectComments(comcol: Collection, poid):

    comments = comcol.find({
        'POI_id': poid
    },{'_id':0}).to_list()

    for com in comments:
        temp = com['time'].isoformat("\t","minutes")
        com['time'] = temp

    return comments

# submit new comment to database
def addComment(comcol: Collection, poid, newComment, username):
    num = comcol.count_documents({})
    comcol.update_one({
        '_id': num
    },{
        '$currentDate': {'time': {'$type' : 'date'}},
        '$set': {
            'guest_usr': username,
            'comment': newComment,
            'POI_id': poid
        },
    },upsert=True)

# find poi in base that are in the same area as the new poi suggestion in admin only page "is there something missing?" (addPOI)
def fetchPOI(poi_col: Collection, poiFilter, coords, r):
    if len(coords) == 1:
        lat = coords[0][1]
        lng = coords[0][0]
        return pointQ(poi_col, poiFilter, lat, lng, r)
    else:
        return poi_col.find({
            'geometry': {
                '$geoIntersects': {
                    '$geometry': {
                        'type': 'Polygon',
                        'coordinates': [coords]
                    }
                }
            }
        }, {'_id': 0}).to_list()

# update the information of an already existing POI as an admin
def updatePOI(poi_col: Collection, poid, new_name, new_details):
    newVal = {}

    old_info = poi_col.find_one({'POID': poid},{'properties.name': 1, 'properties.details': 1, '_id': 0})

    if new_name != old_info['properties']['name']:
        newVal.update({'properties.name': new_name})

    if new_details != old_info['properties']['details']:
        newVal.update({'properties.details': new_details})

    poi_col.update_one({
        'POID': poid
    },{
        '$set': newVal
    })

# add new POI as an admin
def insertPOI(poi_col: Collection, typePOI, name, details, coords):
    poid = U.generatePOID(typePOI)
    geometryType = ""
    elementType = ""
    coordinates = []

    if len(coords) > 1:
        geometryType = "Polygon"
        elementType = "way"
        coordinates = [coords]
    else:
        geometryType = "Point"
        elementType = "node"
        coordinates = coords[0]

    poi_col.insert_one({
        'type': 'Feature',
        'properties': {
            'element_type' : elementType,
            'name': name,
            'details': details,
            'type': typePOI
        },
        'geometry': {
            'type': geometryType,
            'coordinates': coordinates
        },
        'POID': poid
    })

# method to calculate path
def NEWcalc_path(edges: Collection, nodes: Collection, start_lat, start_lng, end_lat, end_lng, centreLat, centreLng, radius, qResult):

    G = nx.MultiGraph()
    # assign node for beginning and ending and fetch all the surrounding edges/roads
    start_node = find_nearest_node(nodes, start_lat, start_lng)
    end_node = find_nearest_node(nodes, end_lat, end_lng)
    edge_listE = get_SNWedges(edges, centreLat, centreLng, radius+100)

    # MAKE LOCAL GRAPH

    for entry in edge_listE:

        G.add_edge(
            entry['properties']['u'], 
            entry['properties']['v'],
            geometry = entry['geometry']['coordinates'],
            weight = entry['properties']['length']
        )

    # GET ALL THE NODES THAT ARE THE CLOSEST TO EACH POI
    poiNodes = []
    for queryResultElement in qResult:
        poiNodes.append(poiToNode(nodes, queryResultElement['geometry']['coordinates'], queryResultElement['geometry']['type'], centreLat, centreLng))
    
    # SORT NODES SO THAT WE VISIT THE CLOSEST EACH TIME
    orderedNodes = sortNodes(nodes, start_node, end_node, poiNodes, radius*2)
    distance_res = 0 # total distance
    route_res = [] # list of sets of coords that comprise the final route/path

    flag = 1 #to check whether a poi is too close to the previous one
    pointA = None
    # FIND THE PATH TO EACH NODE AND COMBINE THE PATHS
    for nodePoint in range(len(orderedNodes)-1):
        # i could save the last node I used for the path finding and check the distance with the rest
        # like if the last poi node in the path is within 120 metres of the next, continue
        if flag:
            pointA = orderedNodes[nodePoint]
        
        pointB = orderedNodes[nodePoint+1]
        dist = U.getDistanceFromLatLonInM(pointA['properties']['x'], pointA['properties']['y'], pointB['properties']['x'], pointB['properties']['y'])
        if dist <= 120:
            # nodes are either the same or too close together for it to matter so skip second point to get to the closest next
            flag = 0
            continue
        flag = 1

        # find each smaller path from A to B
        path_nodes = nx.dijkstra_path(G, pointA['properties']['osmid'], pointB['properties']['osmid'], "weight")
        path_part = nx.utils.pairwise(path_nodes)
        # add all the coordinates of the smaller paths to the final path
        for i, path_edge in enumerate(path_part):
            key = min(G.get_edge_data(*path_edge), key=lambda k: G.get_edge_data(*path_edge)[k].get("weight", 1))
            distance_res += G.edges[path_edge[0], path_edge[1], key]['weight']
            tempGeo = deepcopy(G.edges[path_edge[0], path_edge[1], key]['geometry'])
            route_res.append(tempGeo)

    return distance_res, U.ReRoute(route_res)