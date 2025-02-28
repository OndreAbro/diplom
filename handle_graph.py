import osmnx as _ox
import networkx as _nx
import pandas as _pd
import shapely as _shpl
import geopandas as _gpd
import os
import json
from datetime import datetime


graph_path = '.\\source\\graphml\\'


# Получение названия города на английском языке
def translate_city(city_name):
    with open('.\\source\\tdict.txt', 'r', encoding='utf-8') as tdict:
        return json.loads(tdict.read()).get(city_name)


# Проверка срока давности графа города
def check_mtime(city):
    mtime = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(f'{graph_path}{city}_D.graphml'))).days
    return mtime < 30


# Сохранение графа города в двух вариантах
def save_graphml_to_file(city):
    if not os.path.exists(f'{graph_path}{city}_D.graphml') or \
            not os.path.exists(f'{graph_path}{city}_W.graphml') or \
            not check_mtime(city):
        print('Загрузка города...')
        d = _ox.graph_from_place(f'{city}, Russia', network_type='drive')
        w = _ox.graph_from_place(f'{city}, Russia', network_type='walk')
        _ox.save_graphml(d, filepath=f'{graph_path}{city}_D.graphml')
        _ox.save_graphml(w, filepath=f'{graph_path}{city}_W.graphml')


# Загрузка геоданных из файла OSM
def load_geom(filename):
    points = _ox.features_from_xml(f'.\\source\\geojson_osm\\{filename}.osm')
    return points


# Построение оптимальных маршрутов от адреса к ближайшему узлу в графе D
# и построение маршрутов между ближайшими к адресам узлами графа D после решения TSP
def build_optimal_routes(city, points, tsp_list):
    w = _ox.load_graphml(f'{graph_path}{city}_W.graphml')
    d = _ox.load_graphml(f'{graph_path}{city}_D.graphml')

    routes_to_nearest_node, routes_between_points = [], []

    for i in range(len(points)):
        # Нахождение ближайшего к адресу пешеходного узла
        nearest_node_walk = _ox.nearest_nodes(w, points.geometry[i].x, points.geometry[i].y)

        # Нахождение ближайшего к адресу автомобильного узла
        nearest_node_drive = _ox.nearest_nodes(d, points.geometry[i].x, points.geometry[i].y)

        # Нахождение ближайшего к автомобильному узлу пешеходного узла
        nearest_node_w_to_d = _ox.nearest_nodes(w, d.nodes[nearest_node_drive]['x'], d.nodes[nearest_node_drive]['y'])

        # Построение маршрута между двумя пешеходными узлами (маршрут от здания к улице)
        route = _nx.shortest_path(w, nearest_node_walk, nearest_node_w_to_d, weight='length')

        points_in_route = []

        for j in route:
            points_in_route.append([w.nodes[j]['y'], w.nodes[j]['x']])
        routes_to_nearest_node.append(points_in_route)

    for i in range(len(points) - 1):
        # Нахождение ближайшего автомобильного узла для адреса, соответствующего текущему из решения TSP
        nearest_node_start = _ox.nearest_nodes(d, points.geometry[tsp_list[i]].x, points.geometry[tsp_list[i]].y)

        # Нахождение ближайшего автомобильного узла для адреса, соответствующего следующему из решения TSP
        nearest_node_end = _ox.nearest_nodes(d, points.geometry[tsp_list[i + 1]].x, points.geometry[tsp_list[i + 1]].y)

        # Построение маршрута между двумя соседними узлами из решения TSP
        route = _nx.shortest_path(d, nearest_node_start, nearest_node_end, weight='length')

        points_in_route = []

        for j in route:
            points_in_route.append([d.nodes[j]['y'], d.nodes[j]['x']])
        routes_between_points.append(points_in_route)

    return routes_to_nearest_node, routes_between_points


# Смена начальной точки
def change_depot(points, depot_address, depot_geo):
    depot_geometry = _shpl.geometry.Point(depot_geo[0], depot_geo[1])
    points.loc[('node', 1), 'description'] = depot_address
    points.loc[('node', 1), 'geometry'] = depot_geometry
    return points


# Добавление начальной точки
def add_depot(points, depot_address, depot_geo):
    depot_geometry = _gpd.GeoSeries.from_xy([depot_geo[0]], [depot_geo[1]], index=[('node', 0)])
    depot_gdf = _gpd.GeoDataFrame({'description': depot_address, 'geometry': depot_geometry}, crs="EPSG:4326")
    points = _pd.concat([depot_gdf, points])
    return points
