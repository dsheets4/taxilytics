import logging
import math

import numpy


logger = logging


def highest_probability_topic_per_street():
    pass


def inverse_topic_frequency(data, results, n_trajectories, topic_frequencies):
    for i in range(data.shape[0]):
        for t in range(data.shape[1]):
            data[i][t] /= math.log(
                n_trajectories / (1 + topic_frequencies)
            )

    return data


def common_topics(data, results, topic_counts, num_common=8):

    if num_common == 0:
        return data

    # Negative values will remove the N most common
    # Positive values leave the N most common
    dim2 = data.shape[1]
    if num_common > 0:
        if data.shape[1] > num_common:
            dim2 = num_common
        else:
            logger.warning(
                'Requested Reduction_CommonTopics results in no dimensions')
            dim2 = int(data.shape[1] / num_common)
        topic_counts = sorted(topic_counts, key=lambda x: -x[1])
        logger.info('Retaining the {} least common topics out of {}'.format(
            dim2,
            data.shape[1])
        )
    else:  # Must be negative at this point
        dim2 = data.shape[1] + num_common
        topic_counts = sorted(topic_counts, key=lambda x: x[1])
        logger.info('Retaining the {} most common topics out of {}'.format(
            dim2,
            data.shape[1])
        )

    reduced_cluster_data = numpy.ndarray(
        shape=(data.shape[0], dim2)
    )

    for i in range(reduced_cluster_data.shape[0]):
        for j in range(dim2):
            d = topic_counts[j]
            reduced_cluster_data[i][j] = data[i][d[0]]
    data = reduced_cluster_data

    return data


def PCA(data, results, n_components=8):
    if n_components > data.shape[1]:
        n_components = data.shape[1]

    data = PCA(
        n_components=n_components,
        whiten=True
    ).fit_transform(data)

    results['PCA'] = {
        'input_rows': data.shape[1],
        'pca_components': n_components,
    }

    return data
