from math import sqrt
from PIL import Image, ImageDraw
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
        print(' ')
    if cluster.id < 0:
        # Negative id == branch
        print('-')
    else:
        # Positive id == endpoint
        if labels is None:
            print(cluster.id)
        else:
            print(labels[cluster.id])

    # Print right and left branches
    if cluster.left is not None:
        print_cluster(cluster.left, labels=labels, n=n + 1)
    if cluster.right is not None:
        print_cluster(cluster.right, labels=labels, n=n + 1)


def get_height(clust):
    # If this is an endpoint, then height is just 1
    if clust.left is None and clust.right is None:
        return 1

    # Otherwise the height is the same of the heights of each branch
    return get_height(clust.left) + get_height(clust.right)


def get_depth(clust):
    # The distance of an endpoint is 0
    if clust.left is None and clust.right is None:
        return 0

    # The distance of a branch is the grater of its two sides plus its own distance
    return max(get_depth(clust.left), get_depth(clust.right)) + clust.distance


def draw_node(draw, clust, x, y, scaling, labels):
    if clust.id < 0:
        h1 = get_height(clust.left) * 20
        h2 = get_height(clust.right) * 20
        top = y - (h1 + h2) / 2
        bottom = y + (h1 + h2) / 2

        line_len = clust.distance * scaling

        # Vertical line from this cluster to children
        draw.line((x, top + h1 / 2, x, bottom - h2 / 2), fill=(0, 255, 0))

        # Horizontal line to the left item
        draw.line((x, top + h1 / 2, x + line_len, top + h1 / 2), fill=(255, 0, 0))

        # Horizontal line to the right item
        draw.line((x, bottom - h2 / 2, x + line_len, bottom - h2 / 2), fill=(255, 0, 0))

        # Draw left and right nodes
        draw_node(draw, clust.left, x + line_len, top + h1 / 2, scaling, labels)
        draw_node(draw, clust.right, x + line_len, bottom - h2 / 2, scaling, labels)
    else:
        # Draw endpoint if this is an item label
        draw.text((x + 5, y - 7), labels[clust.id], (0, 0, 0))


def draw_dendogram(clust, labels, jpeg='clusters.jpg'):
    h = get_height(clust) * 20
    w = 1200
    depth = get_depth(clust)

    # scale distance based on width
    scaling = float(w - 150) / depth

    # Create new image with white bg
    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.line((0, h / 2, 10, h / 2), fill=(255, 0, 0))

    # Draw the first node
    draw_node(draw, clust, 10, (h / 2), scaling, labels)
    img.save(jpeg, 'JPEG')


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


def scaledown(data, distance=pearson, rate=0.01):
    n = len(data)

    # Real distance between every pair of items
    real_dist = [[distance(data[i], data[j]) for j in range(n)]
                 for i in range(0, n)]

    outersum = 0.0

    # Randomly initialize starting points
    loc = [[random.random(), random.random()] for i in range(n)]
    fake_dist = [[0.0 for j in range(n)] for i in range(n)]

    lasterror = None
    for m in range(0, 1000):
        # Find projected distance
        for i in range(n):
            for j in range(n):
                fake_dist[i][j] = sqrt(sum([pow(loc[i][x] - loc[j][x], 2)
                                            for x in range(len(loc[i]))]))

        # Move points
        grad = [[0.0, 0.0] for i in range(n)]

        totalerror = 0
        for k in range(n):
            for j in range(n):
                if j == k:
                    continue

                # Error is percent diff between distances
                errorterm = (fake_dist[j][k] - real_dist[j][k]) / real_dist[j][k]

                # Each points needs to be moved away from or towards the other point in proportion to how much error
                # it has
                grad[k][0] += ((loc[k][0] - loc[j][0]) / fake_dist[j][k]) * errorterm
                grad[k][1] += ((loc[k][1] - loc[j][1]) / fake_dist[j][k]) * errorterm

                # Keep track of total error
                totalerror += abs(errorterm)

        print(totalerror)

        # If answer got worse by moving the points, we are done
        if lasterror and lasterror < totalerror:
            break

        lasterror = totalerror

        # Move each points by the learning rate times the gradient
        for k in range(n):
            loc[k][0] -= rate * grad[k][0]
            loc[k][1] -= rate * grad[k][1]

    return loc


def draw2d(data, labels, jpeg='mds2d.jpg'):
    img = Image.new('RGB', (2000, 2000), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    for i in range(len(data)):
        x = (data[i][0] + 0.5) * 1000
        y = (data[i][1] + 0.5) * 1000
        draw.text((x, y), labels[i], (0, 0, 0))

    img.save(jpeg, 'JPEG')
