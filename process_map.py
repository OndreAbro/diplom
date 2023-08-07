import folium as _f


def create_map(filename, city_geo, points, routes_to_nearest_node, routes_between_points):
    m = _f.Map([city_geo[1], city_geo[0]])
    for i in range(len(points)):
        _f.Marker([points.geometry[i].y, points.geometry[i].x],
                  popup=points.description[i], icon=_f.Icon(color='green')).add_to(m)
    for route in routes_to_nearest_node:
        _f.PolyLine(route, color='orange').add_to(m)
    for route in routes_between_points:
        _f.PolyLine(route, color='red').add_to(m)

    m.save(f'.\\source\\maps\\{filename}.html')
