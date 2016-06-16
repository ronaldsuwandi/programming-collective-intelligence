from math import sqrt
import random


def pearson(v1, v2):
    sum1 = sum(v1)
    sum2 = sum(v2)

    sum1_square = sum([pow(v, 2) for v in v1])
    sum2_square = sum([pow(v, 2) for v in v2])

    # sum of products
    product_sum = sum([v1[i] * v2[i] for i in range(len(v1))])

    # r (pearson score)
    num = product_sum - (sum1 * sum2 / len(v1))
    den = sqrt((sum1_square - pow(sum1, 2) / len(v1)) * (sum2_square - pow(sum2, 2) / len(v1)))
    if den == 0:
        return 0
    return 1.0 - num / den


def readfile(filename):
    lines = [line for line in open(filename)]

    # First line is the column titles
    colnames = lines[0].strip().split('\t')[1:]
    rownames = []
    data = []
    for line in lines[1:]:
        p = line.strip().split('\t')

        # First column is row name
        rownames.append(p[0])

        # The data for this row is the remainder of the row
        data.append([float(x) for x in p[1:]])

    return rownames, colnames, data


class Bicluster:
    def __init__(self, vec, left=None, right=None, distance=0.0, id=None):
        self.left = left
        self.right = right
        self.vec = vec
        self.id = id
        self.distance = distance


def hcluster(rows, distance=pearson):
    distances = {}
    current_cluster_id = -1

    # Clusters are initially just the rows
    cluster = [Bicluster(rows[i], id=i) for i in range(len(rows))]

    while len(cluster) > 1:
        lowestpair = (0, 1)
        closest = distance(cluster[0].vec, cluster[1].vec)

        # Loop through every pair looking for the smallest distance
        for i in range(len(cluster)):
            for j in range(i + 1, len(cluster)):
                # distances is cached
                if (cluster[i].id, cluster[j].id) not in distances:
                    distances[(cluster[i].id, cluster[j].id)] = distance(cluster[i].vec, cluster[j].vec)

                d = distances[(cluster[i].id, cluster[j].id)]

                if d < closest:
                    closest = d
                    lowestpair = (i, j)

        # Calculate average of the two clusters
        mergevec = [(cluster[lowestpair[0]].vec[i] + cluster[lowestpair[1]].vec[i]) / 2.0
                    for i in range(len(cluster[0].vec))]

        # Create new cluster
        newcluster = Bicluster(mergevec, left=cluster[lowestpair[0]], right=cluster[lowestpair[1]], distance=closest,
                               id=current_cluster_id)

        current_cluster_id -= 1

        del cluster[lowestpair[1]]
        del cluster[lowestpair[0]]
        cluster.append(newcluster)

    return cluster[0]


def print_cluster(cluster, labels=None, n=0):
    for i in range(n):
        print(' ', end='')
    if cluster.id < 0:
        # Negative id == branch
        print('-')
    else:
        # Positive id == endpoint
        if labels == None:
            print(cluster.id)
        else:
            print(labels[cluster.id])

    # Print right and left branches
    if cluster.left != None:
        print_cluster(cluster.left, labels=labels, n=n + 1)
    if cluster.right != None:
        print_cluster(cluster.right, labels=labels, n=n + 1)


def rotatematrix(data):
    newdata = []
    for i in range(len(data[0])):
        newrow = [data[j][i] for j in range(len(data))]
        newdata.append(newrow)
    return newdata


def kclusters(rows, distance=pearson, k=4):
    # Determines min and max for each point

    ranges = [(min([row[i] for row in rows]), max([row[i] for row in rows]))
              for i in range(len(rows[0]))]

    # Create k randomly placed centroids
    clusters = [[random.random() * (ranges[i][1] - ranges[i][0]) + ranges[i][0]
                 for i in range(len(rows[0]))]
                for j in range(k)]

    lastmatches = None
    # bestmatches = None
    for t in range(1):
        print('Iteration {0}'.format(t))
        bestmatches = [[] for i in range(k)]

        # Find which centroids closet to each row
        for j in range(len(rows)):
            row = rows[j]
            bestmatch = 0
            for i in range(k):
                d = distance(clusters[i], row)
                if d < distance(clusters[bestmatch], row):
                    bestmatch = i
            bestmatches[bestmatch].append(j)

        # If result is the same as last time, this is complete
        if bestmatches == lastmatches:
            break
        lastmatches = bestmatches

        # Move the centroids to the average of their members
        for i in range(k):
            avgs = [0.0] * len(rows[0])
            if len(bestmatches[i]) > 0:
                for rowid in bestmatches[i]:
                    for m in range(len(rows[rowid])):
                        avgs[m] += rows[rowid][m]
                for j in range(len(avgs)):
                    avgs[j] /= len(bestmatches[i])
                clusters[i] = avgs

    return bestmatches
