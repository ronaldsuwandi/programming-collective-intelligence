import math
import random


def annealing(domain, costf, T=10000.0, cooling_rate=0.95, step=1):
    vec = [float(random.randint(domain[i][0], domain[i][1]))
           for i in range(len(domain))]

    while T > 0.1:
        # Choose random indices
        i = random.randint(0, len(domain) - 1)

        # Choose direction
        direction = step * (-1) ** int(round(random.random()))

        # New list with one of the values changed
        vec_new = vec[:]
        vec_new[i] += direction
        if vec_new[i] < domain[i][0]:
            vec_new[i] = domain[i][0]
        elif vec_new[i] > domain[i][1]:
            vec_new[i] = domain[i][1]

        current_cost = costf(vec)
        new_cost = costf(vec_new)

        if new_cost < current_cost:
            vec = vec_new
        else:
            p = pow(math.e, (-new_cost - current_cost) / T)
            if random.random() < p:
                vec = vec_new

        # Decrease temperature
        T = T * cooling_rate

    return vec
