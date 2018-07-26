import logging
import math

from sklearn import metrics
import numpy
from scipy.spatial.distance import cdist


logger = logging


def cluster_centers(data, algorithm, results):

    try:
        results['centroid_distances'] = cdist(
            data,
            algorithm.cluster_centers_,
            'euclidean'
        )
        results['max_center_distance'] = numpy.amax(
            results['centroid_distances']
        )

    except KeyError:
        logger.info("Calculating cluster centers")
        centers = [(-1, None)] * (results['n_clusters'] + 1)
        for i, d in enumerate(data):
            nClusterId = int(algorithm.labels_[i])
            if nClusterId == -1:
                nClusterId = results['n_clusters']
            curr_center = centers[nClusterId]
            if curr_center[1] is None:
                curr_center = (1, d.copy)
            else:
                for j, e in enumerate(d):
                    curr_center = (
                        curr_center[0] + 1,
                        (curr_center[1][j] * curr_center[0] + e) /
                        (curr_center[0] + 1)
                    )

        centers = numpy.ndarray(
            (results['n_clusters'], 1),
            buffer=numpy.array([center[1] for center in centers])
        )
        # TODO: Figure out how to apply this calculation for the centers.
        # self.results['centroid_distances'] = cdist(
        #    self.cluster_data,
        #    centers,
        #    'euclidean'
        #)
        results['max_center_distance'] = 10


def cluster_entropy(data, algorithm, results):
    cluster_topic_data = []
    n_clusters = results['n_clusters']
    for c in range(n_clusters):
        cluster_topic_data.append([0] * data.shape[1])

    for i in range(data.shape[0]):
        for t in range(data.shape[1]):
            cluster_topic_data[int(algorithm.labels_[i])][t] += (
                data[i][t] * math.log(data[i][t])
            ) if data[i][t] > 0 else 0

    # Now, sum the entropy of each topic in each cluster
    clusterEntropy = [0] * n_clusters
    for c in range(n_clusters):
        for e in cluster_topic_data[c]:
            clusterEntropy[c] += e
        clusterEntropy[c] *= -1

    results['cluster_entropy'] = cluster_entropy


def silhouette_score(data, algorithm, results):

    try:
        results['silhouette_score'] = metrics.silhouette_score(
            data,
            algorithm.labels_,
            metric='euclidean'
        )
    except ValueError:
        pass
