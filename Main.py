import csv
from itertools import permutations
from mpmath import exp
from math import floor, log
from random import choice, uniform
from timeit import default_timer

debugging = False

ac_data_path = 'Aircraft List.csv'
flight_data_path = 'Heathrow Flights Test.csv'
export_data_path = 'Heathrow Flights Ordered.csv.csv'

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

    print('Importing flight schedule and aircraft data...')
    reader = csv.reader(open(ac_data_path, 'r'))
    ac_data = list(reader)
    open(ac_data_path, 'r').close()
    reader = csv.reader(open(flight_data_path, 'r'))
    flight_data = list(reader)
    open(flight_data_path, 'r').close()

    for i in range(len(ac_data)):
        ac_data[i][1] = int(ac_data[i][1])
        for j in wake_cat_list:
            if ac_data[i][2] == j:
                ac_data[i][2] = wake_cat_list.index(j)

    for i in range(len(flight_data)):
        for j in sid_list:
            if flight_data[i][2] == j:
                flight_data[i].append(sid_list.index(j))
        for j in ac_data:
            if flight_data[i][1] == j[0]:
                flight_data[i].append(j[2])
                flight_data[i].append(j[1])

    print('{} aircraft and {} flights imported successfully'.format(len(ac_data), len(flight_data)))
    return flight_data


def export_data(optimum_solution):
    writer = csv.writer(open(export_data_path, 'w'))
    for i in optimum_solution:
        writer.writerow(i[0:3])
    open(export_data_path, 'w').close()


def route_sep(flight_list, leader_i, follower_i):
    l_sid = flight_list[leader_i][3]
    f_sid = flight_list[follower_i][3]
    return route_sep_matrix[f_sid][l_sid]


def wake_sep(flight_list, leader_i, follower_i):
    l_group = flight_list[leader_i][4]
    f_group = flight_list[follower_i][4]
    return wake_sep_matrix[f_group][l_group]


def speed_sep(flight_list, leader_i, follower_i):
    sep = flight_list[follower_i][5] - flight_list[leader_i][5]
    if sep < 0:
        return 0
    else:
        return sep * 60


def interval(flight_list, leader_i, follower_i):
    sep_list = [route_sep(flight_list, leader_i, follower_i), wake_sep(flight_list, leader_i, follower_i),
                speed_sep(flight_list, leader_i, follower_i)]
    if debugging is True:
        constraint = ''
        if sep_list.index(max(sep_list)) == 0:
            constraint = 'route separation'
        elif sep_list.index(max(sep_list)) == 1:
            constraint = 'wake separation'
        elif sep_list.index(max(sep_list)) == 2:
            constraint = 'speed separation'
        print('{}, {}, {}s due {}'.format(flight_list[leader_i][0],
                                          flight_list[follower_i][0], max(sep_list), constraint))
    return max(sep_list)


def sigma_interval(flight_list):
    sigma = 0
    for i in range(len(flight_list) - 1):
        sigma += interval(flight_list, i, i + 1)
    if debugging is True:
        print('Cumulative interval: {}s'.format(sigma))
    return sigma


def split_list(flight_list, category, value):
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
    for i in flight_list:
        if i[category] == value:
            sublist.append(i)
    return sublist


def optimise_perm(flight_list):
    print('Optimising {} aircraft via permutations'.format(len(flight_list)))
    start_time = default_timer()
    initial_sigma = sigma_interval(flight_list)
    optimum_order = []
    optimal_sigma = 0
    perm = permutations(flight_list)
    for i in perm:
        if sigma_interval(i) < optimal_sigma or optimal_sigma == 0:
            optimum_order = list(i)
            optimal_sigma = sigma_interval(i)
    end_time = default_timer()
    time = round((end_time - start_time), 3)
    print('Optimal order found in {}s with cumulative interval {}s, resulting in improvement of {}% over given order'
          .format(time, optimal_sigma, round(100 - (optimal_sigma * 100 / initial_sigma), 2)))
    if debugging is True:
        print('Optimum order: {}'.format(optimum_order))
    return optimum_order


def swap(flight_list, i, j):
    flight_new = flight_list[:]
    flight_new[i], flight_new[j] = flight_new[j], flight_new[i]
    return flight_new


def optimise_tabu(flight_list, iteration_percent, tenure_percent):
    start_time = default_timer()
    iteration = 1
    iteration_lim = floor(iteration_percent * len(flight_list))
    tenure = floor(tenure_percent * len(flight_list))
    tabu = []
    initial_sigma = sigma_interval(flight_list)
    current_solution = flight_list[:]
    optimal_solution = flight_list[:]
    optimal_sigma = sigma_interval(optimal_solution)

    print('Optimising via tabu search: {} iterations, tenure length {}...'.format(iteration_lim, tenure))
    if debugging is True:
        print('Starting order: ', flight_list)

    index = list(range(len(current_solution)))
    index_pairs = []
    for i in index[:- 1]:
        for j in index[i + 1:]:
            index_pairs.append([i, j])

    while iteration <= iteration_lim:
        if debugging is True:
            print('Beginning iteration {}...'.format(iteration))
            print('Current solution: {}'.format(current_solution))
        neighbourhood = index_pairs[:]
        neighbourhood_sigma = []
        for i in neighbourhood:
            if i in tabu:
                neighbourhood.remove(i)
        for i in neighbourhood:
            neighbourhood_sigma.append(sigma_interval(swap(current_solution, i[0], i[1])))

        current_swap = neighbourhood[neighbourhood_sigma.index(min(neighbourhood_sigma))]
        current_solution = swap(current_solution, current_swap[0], current_swap[1])
        current_sigma = sigma_interval(current_solution)
        tabu.append(current_swap)
        if len(tabu) > tenure:
            del tabu[0]

        if debugging is True:
            print('Best swap {}, with cumulative interval: {}s'.format(current_swap, current_sigma))
            print('Tabu: {}'.format(tabu))

        if current_sigma < optimal_sigma:
            optimal_sigma = current_sigma
            optimal_solution = current_solution[:]
            if debugging is True:
                print('New optimal solution found: {}'.format(optimal_solution))
        iteration += 1

    end_time = default_timer()
    time = round((end_time - start_time), 3)
    print('Optimal order found in {}s with cumulative interval {}s, resulting in improvement of {}% over given order'
          .format(time, optimal_sigma, round(100 - (optimal_sigma * 100 / initial_sigma), 2)))
    return optimal_solution


def optimise_annealing(flight_list, initial_temperature, end_temperature, temperature_model, iteration_lim):
    print('Optimising via simulated annealing: initial temperature {}, end temperature {}, {} decrease function...'
          .format(initial_temperature, end_temperature, temperature_model))
    if debugging is True:
        print('Starting order: ', flight_list)
    start_time = default_timer()

    iteration = 1
    initial_sigma = sigma_interval(flight_list)
    current_solution = flight_list[:]
    current_sigma = sigma_interval(current_solution)
    optimal_solution = flight_list[:]
    optimal_sigma = sigma_interval(optimal_solution)
    temperature = initial_temperature
    if temperature_model == 'exponential':
        def temperature_decrease(k):
            current_temperature = initial_temperature * (0.95 ** k)
            return current_temperature
    elif temperature_model == 'fast':
        def temperature_decrease(k):
            current_temperature = initial_temperature / k
            return current_temperature
    elif temperature_model == 'Boltzmann':
        def temperature_decrease(k):
            current_temperature = initial_temperature / (log(k + 1))
            return current_temperature
    else:
        print('Error: Temperature decrease function {} is unknown'.format(temperature_model))
        return

    def acceptance(delta, t):
        probability = 1 / (exp(delta / t))
        return probability

    neighbourhood = []
    index = list(range(len(current_solution)))
    for i in index[:- 1]:
        for j in index[i + 1:]:
            neighbourhood.append([i, j])

    while end_temperature <= temperature and iteration <= iteration_lim:
        accept_solution = False
        if debugging is True:
            print('Beginning iteration {}'.format(iteration))
        while accept_solution is False:
            candidate_swap = choice(neighbourhood)
            candidate_solution = swap(current_solution, candidate_swap[0], candidate_swap[1])
            candidate_sigma = sigma_interval(candidate_solution)
            if candidate_sigma < current_sigma:
                current_solution = candidate_solution[:]
                current_sigma = candidate_sigma
                accept_solution = True
                if debugging is True:
                    print('Better solution accepted with cumulative interval {}s'.format(current_sigma))
            elif uniform(0, 1) <= acceptance(candidate_sigma - current_sigma, temperature):
                current_solution = candidate_solution[:]
                current_sigma = candidate_sigma
                accept_solution = True
                if debugging is True:
                    print('Worse solution accepted with cumulative interval {}s'.format(current_sigma))
            elif debugging is True:
                print('Worse solution not accepted')
        if current_sigma < optimal_sigma:
            optimal_solution = current_solution[:]
            optimal_sigma = current_sigma
            if debugging is True:
                print('New optimal solution found with cumulative interval {}s'.format(optimal_sigma))
        temperature = temperature_decrease(iteration)
        iteration += 1

    end_time = default_timer()
    time = round((end_time - start_time), 3)
    print('Optimal order found, {} iterations, in {}s. Cumulative interval {}s, improvement of {}% over given order'
          .format(iteration, time, optimal_sigma, round(100 - (optimal_sigma * 100 / initial_sigma), 2)))
    return optimal_solution


def optimise(flight_list, change_count_lim):
    start_time = default_timer()
    initial_sigma = sigma_interval(flight_list)

    if len(flight_list) == 0:
        print('Flight list is empty')
        return
    elif 0 < len(flight_list) <= 10:
        optimal_solution = optimise_perm(flight_list)
    elif 10 < len(flight_list) <= 25:
        optimal_solution = optimise_tabu(flight_list, 50, 0.8)
    elif len(flight_list) > 25:
        optimal_solution = flight_list[:]
        optimal_sigma = sigma_interval(optimal_solution)
        current_solution = flight_list[:]
        iteration = 1
        change_count = 0

        while change_count < change_count_lim:
            if iteration == 1:
                print('Beginning iteration {}...'.format(iteration))
            else:
                print('Re-annealing and beginning iteration {}...'.format(iteration))
            current_solution = optimise_annealing(current_solution, 3000, 0.1, 'fast', 100000)
            current_sigma = sigma_interval(current_solution)
            if current_sigma < optimal_sigma:
                optimal_solution = current_solution[:]
                optimal_sigma = current_sigma
                change_count = 0
            elif current_sigma == optimal_sigma:
                change_count += 1
            iteration += 1

        print('Terminated after {} iterations due to {} consecutive failures to improve the solution'
              .format(iteration, change_count_lim))
        end_time = default_timer()
        time = round((end_time - start_time), 3)
        print('Final solution found in {}s. Cumulative interval {}, improvement of {}% over starting order'
              .format(time, optimal_sigma, round(100 - (optimal_sigma * 100 / initial_sigma), 2)))

    return optimal_solution


flight_data = import_data()
optimum_order = (optimise(flight_data, 3))
print(optimum_order)
for i in optimum_order:
    print(i[0:3])

# 36080s
