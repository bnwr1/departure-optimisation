import csv
import math
from itertools import permutations

debugging = False

ac_data_path = 'Aircraft List.csv'
flight_data_path = 'Heathrow Flights.csv'

wake_cat_list = ['J', 'H', 'U', 'M', 'S', 'L']
sid_list = ['BPK', 'UMLAT', 'CPT', 'GOGSI', 'MAXIT', 'DET']

route_sep_matrix = [
    [120, 120, 120, 120, 60, 60],
    [120, 120, 120, 120, 60, 60],
    [120, 120, 120, 120, 120, 60],
    [120, 120, 120, 120, 120, 60],
    [60, 60, 120, 120, 120, 120],
    [60, 60, 60, 60, 120, 120],
]

wake_sep_matrix = [
    [0, 0, 0, 0, 0, 0],
    [100, 0, 0, 0, 0, 0],
    [120, 0, 0, 0, 0, 0],
    [140, 100, 80, 0, 0, 0],
    [160, 120, 100, 0, 0, 0],
    [180, 140, 120, 120, 100, 0],
]


def import_data():
    # Imports flight data as [Call-sign, A/C Type, SID, SID Index, Wake Category Index, Speed Group]
    global flight_data

    print('Importing flight schedule and aircraft data...')
    reader = csv.reader(open(ac_data_path, 'r'))
    ac_data = list(reader)
    reader = csv.reader(open(flight_data_path, 'r'))
    flight_data = list(reader)

    for i in range(len(ac_data)):
        ac_data[i][1] = int(ac_data[i][1])
        for j in wake_cat_list:
            if ac_data[i][2] == j:
                ac_data[i][2] = wake_cat_list.index(j)
    print('{} aircraft imported'.format(len(ac_data)))

    for i in range(len(flight_data)):
        for j in sid_list:
            if flight_data[i][2] == j:
                flight_data[i].append(sid_list.index(j))
        for j in ac_data:
            if flight_data[i][1] == j[0]:
                flight_data[i].append(j[2])
                flight_data[i].append(j[1])
    print('{} flights imported'.format(len(flight_data)))


def route_sep(route_list, leader_i, follower_i):
    l_sid = route_list[leader_i][3]
    f_sid = route_list[follower_i][3]
    return route_sep_matrix[f_sid][l_sid]


def wake_sep(route_list, leader_i, follower_i):
    l_group = route_list[leader_i][4]
    f_group = route_list[follower_i][4]
    return wake_sep_matrix[f_group][l_group]


def speed_sep(route_list, leader_i, follower_i):
    sep = route_list[follower_i][5] - route_list[leader_i][5]
    if sep < 0:
        return 0
    else:
        return sep * 60


def interval(route_list, leader_i, follower_i):
    sep_list = [route_sep(route_list, leader_i, follower_i), wake_sep(route_list, leader_i, follower_i),
                speed_sep(route_list, leader_i, follower_i)]
    if debugging is True:
        constraint = ''
        if sep_list.index(max(sep_list)) == 0:
            constraint = 'route separation'
        elif sep_list.index(max(sep_list)) == 1:
            constraint = 'wake separation'
        elif sep_list.index(max(sep_list)) == 1:
            constraint = 'speed separation'
        print('{}, {}, {}s due {}'.format(route_list[leader_i][0],
                                          route_list[follower_i][0], max(sep_list), constraint))
    return max(sep_list)


def sigma_interval(route_list):
    sigma = 0
    for i in range(len(route_list) - 1):
        sigma += interval(route_list, i, i + 1)
    if debugging is True:
        print('Cumulative interval: {}s'.format(sigma))
    return sigma


def split_list(route_list, category, value):
    category_text = ''
    value_text = ''
    if category == 3:
        category_text = 'SID'
        value_text = sid_list[value]
    elif category == 4:
        category_text = 'wake category'
        value_text = wake_cat_list[value]
    elif category == 5:
        category_text = 'speed group'
        value_text = str(value)
    print('Filtering data via {}: {}'.format(category_text, value_text))
    sublist = []
    for i in route_list:
        if i[category] == value:
            sublist.append(i)
    return sublist


def optimise_perm(route_list):
    print('Optimising {} aircraft via permutations'.format(len(route_list)))
    initial_sigma = sigma_interval(route_list)
    optimum_order = []
    optimal_sigma = 0
    perm = permutations(route_list)
    for i in perm:
        if sigma_interval(i) < optimal_sigma or optimal_sigma == 0:
            optimum_order = list(i)
            optimal_sigma = sigma_interval(i)
    print('Optimal order found with cumulative interval: {}s, resulting in improvement of {}% over starting order'
          .format(optimal_sigma, round(100 - (optimal_sigma * 100 / initial_sigma), 2)))
    if debugging is True:
        print('Optimum order: {}'.format(optimum_order))
    return optimum_order


def swap(flight_list, i ,j):
    flight_new = flight_list[:]
    flight_new[i], flight_new[j] = flight_new[j], flight_new[i]
    return flight_new


def optimise_tabu(flight_list, iteration_lim, tenure_percent):
    iteration = 1
    optimal_solution = []
    optimal_sigma = 0
    current_solution = flight_list[:]
    initial_sigma = sigma_interval(current_solution)
    tabu = []
    tenure = math.floor(tenure_percent * len(current_solution))

    print('Optimising via tabu search with {} iterations and tenure length {}...'.format(iteration_lim, tenure))
    if debugging is True:
        print('Starting order: ', flight_list)

    while iteration <= iteration_lim:
        if debugging is True:
            print('Beginning iteration {}...'.format(iteration))
            print('Current solution: {}'.format(current_solution))
        index = list(range(len(current_solution)))
        index_pairs = []
        pairs_sigma = []
        for i in index[:-1]:
            for j in index[i+1:]:
                index_pairs.append([i,j])
        for i in index_pairs:
            if i in tabu:
                index_pairs.remove(i)
        for i in index_pairs:
            pairs_sigma.append(sigma_interval(swap(current_solution, i[0], i[1])))
        current_swap = index_pairs[pairs_sigma.index(min(pairs_sigma))]
        current_solution = swap(current_solution, current_swap[0], current_swap[1])
        current_sigma = sigma_interval(current_solution)
        if debugging is True:
            print('Best swap {}, with cumulative interval: {}s'.format(current_swap, current_sigma))
        tabu.append(current_swap)
        if len(tabu) > tenure:
            del tabu[0]
        if current_sigma < optimal_sigma or optimal_sigma == 0:
            optimal_sigma = current_sigma
            optimal_solution = current_solution[:]
            if debugging is True:
                print('Tabu: {}'.format(tabu))
                print('New optimal solution found: {}'.format(optimal_solution))
        iteration += 1
    
    print('Optimal order found with cumulative interval: {}s, resulting in improvement of {}% over starting order'
          .format(optimal_sigma, round(100 - (optimal_sigma * 100 / initial_sigma), 2)))
    return optimal_solution


import_data()
optimise_tabu(split_list(flight_data, 4, 2), 1000, 0.8)


# BPK/UMLAT: 186
# CPT/GOGSI: 110
# MAXIT: 92
# DET: 169
