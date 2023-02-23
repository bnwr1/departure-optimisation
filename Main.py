import csv
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
    sigma_initial = sigma_interval(route_list)
    order_optimum = []
    sigma_min = 0
    perm = permutations(route_list)
    for i in perm:
        if sigma_interval(i) < sigma_min or sigma_min == 0:
            order_optimum = list(i)
            sigma_min = sigma_interval(i)
    print('Optimal order found with cumulative interval: {}s, resulting in improvement of {}% over default order'
          .format(sigma_min, round(100 - (sigma_min * 100 / sigma_initial), 2)))
    if debugging is True:
        print('Optimum order: {}'.format(order_optimum))
    return order_optimum


import_data()
optimise_perm(split_list(flight_data, 4, 4))

'''count = 0
for i in range(len(flight_data)):
    if flight_data[i][4] == 0:
        count+=1
print(count)'''

# BPK/UMLAT: 186
# CPT/GOGSI: 110
# MAXIT: 92
# DET: 169
