from turfpy import measurement
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def solve_tsp(points):
    distance_matrix = []
    for i in range(len(points)):
        dist_list = []
        for j in range(len(points)):
            start = [points.geometry[i].x, points.geometry[i].y]
            end = [points.geometry[j].x, points.geometry[j].y]
            dist = round(measurement.distance(start, end) * 1000)
            dist_list.append(dist)
        distance_matrix.append(dist_list)
    data = {
        'distance_matrix': distance_matrix,
        'num_vehicles': 1,
        'depot': 0
    }

    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']), data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    solution = routing.SolveWithParameters(search_parameters)

    index = routing.Start(0)
    route = [manager.IndexToNode(index)]
    while not routing.IsEnd(index):
        index = solution.Value(routing.NextVar(index))
        route.append(manager.IndexToNode(index))
    return route
