import logging
import sys
import traceback


from sklearn import cluster
from sklearn.neighbors import kneighbors_graph

import util


logger = logging


def require_method(obj, methods):
    for m in methods:
        if m not in dir(obj) or not callable(getattr(obj, m)):
            raise Exception('Missing method {}'.format(m))


class ClusterModel(object):

    def __init__(self, impl='KMEANS', **kwargs):
        # Finally, we create the model and let 'r rip!
        class_name = '_{}'.format(impl)
        model_class = getattr(sys.modules[__name__], class_name)
        kwargs, unused, _ = util.filter_kwargs(model_class, kwargs)
        if len(unused) > 0:
            logger.warning(
                'Cluster model "{}" has unused arguments: {}'.format(
                    impl,
                    unused
                )
            )
        self._model = model_class(**kwargs)

    def fit(self, data):
        self._model.fit(data)

    def __getattr__(self, name):
        return getattr(self._model, name)


class _BaseClusterModel(object):

    def __init__(self):
        self.results = {}

    def _get_connectivity(self, data, n_neighbors=10):
        if data.shape[0] < (n_neighbors * 2):
            n_neighbors = data.shape[0] / 2

        connectivity = kneighbors_graph(
            data,
            n_neighbors=n_neighbors
        )

        # make connectivity symmetric
        connectivity = 0.5 * (connectivity + connectivity.T)
        return connectivity

    def log_not_enough_samples(self, new_num):
        logger.warning(
            "Not enough samples for {} clusters, setting to {}".format(
                self.algorithm.n_clusters,
                new_num
            )
        )

    def fit(self, data):

        try:
            logger.info('Clustering with {}. Data shape: {}'.format(
                self.__class__.__name__,
                data.shape
            ))

            self.algorithm.fit(data)
            n_clusters = len(set(self.algorithm.labels_))
            n_noise = self.algorithm.labels_.tolist().count(-1)
            if n_noise > 0:
                n_clusters -= 1
            self.results['n_clusters'] = n_clusters
            self.results['n_noise'] = n_noise
            self.results['labels'] = self.algorithm.labels_

            logger.info('Clustering complete: {} clusters, {} noise'.format(
                self.results['n_clusters'],
                self.results['n_noise'],
            ))

        except (OverflowError, ValueError) as e:
            logger.warning(
                "{} detected: Trace and Cluster data follows:".format(
                    e.__class__.__name__
                )
            )
            logger.warning(traceback.format_exc())
            for i, d in data:
                logger.info('   {}'.format((i, d)))
            self.results['n_clusters'] = 0
            self.results['n_noise'] = 0
            logger.warning(
                "Error clustering data. Shape of input is {}".format(
                    data.shape
                )
            )

    def __getattr__(self, name):
        return self.results[name]


class _NClusterModel(_BaseClusterModel):

    def __init__(self):
        super().__init__()

    def fit(self, data):
        if self.algorithm.n_clusters > data.shape[0]:
            self.log_not_enough_samples(data.shape[0])
            self.algorithm.n_clusters = data.shape[0]

        super().fit(data)


class _ConnectivityClusterModel(_BaseClusterModel):

    def __init__(self):
        super().__init__()

    def fit(self, data):
        if self.algorithm.n_clusters > data.shape[0]:
            self.log_not_enough_samples(data.shape[0])
            self.algorithm.n_clusters = data.shape[0]

        super().fit(data)


class _AffinityPropagation(_BaseClusterModel):

    def __init__(self, damping=0.9, preference=200):
        super().__init__()
        self.algorithm = cluster.AffinityPropagation(
            damping=damping,
            preference=preference
        )


class _DBSCAN(_BaseClusterModel):

    def __init__(self, eps, min_pts):
        super().__init__()

        self.algorithm = cluster.DBSCAN(
            eps=eps,
            min_samples=min_pts,
        )


class _Agglomerative(_NClusterModel):

    def __init__(self, n_clusters, connectivity=None, linkage=None):
        super().__init__()

        if linkage is None:
            linkage = 'average'

        if connectivity is None:
            connectivity = self._get_connectivity(self.cluster_data)

        self.algorithm = cluster.AgglomerativeClustering(
            n_clusters=n_clusters,
            connectivity=connectivity,
            linkage=linkage
        )


class _KMeans(_NClusterModel):

    def __init__(self, n_clusters):
        super().__init__()

        self.algorithm = cluster.KMeans(
            n_clusters=n_clusters
        )


class _MiniBatchKMeans(_NClusterModel):

    def __init__(self, n_clusters):
        super().__init__()

        self.algorithm = cluster.MiniBatchKMeans(
            n_clusters=n_clusters
        )


class _MeanShift(_NClusterModel):

    def __init__(self, n_clusters, bandwidth=None, bin_seeding=True):
        super().__init__()

        if bandwidth is None:
            bandwidth = cluster.estimate_bandwidth(
                self.cluster_data,
                quantile=0.3
            )

        self.algorithm = cluster.MeanShift(
            bandwidth=bandwidth,
            bin_seeding=bin_seeding
        )


class _Spectral(_NClusterModel):

    def __init__(self, n_clusters,
                 eigen_solver='arpack',
                 affinity='nearest_neighbors'):
        super().__init__()

        self.algorithm = cluster.SpectralClustering(
            n_clusters=self.results['n_clusters'],
            eigen_solver=eigen_solver,
            affinity=affinity
        )


class _Ward(_NClusterModel):

    def __init__(self, n_clusters, connectivity=None):
        super().__init__()

        if connectivity is None:
            connectivity = self.get_connectivity(self.cluster_data)

        self.algorithm = cluster.AgglomerativeClustering(
            n_clusters=n_clusters,
            connectivity=connectivity,
            linkage='ward'
        )


class _Birch(_NClusterModel):

    def __init__(self, n_clusters, threshold=0.5, branching_factor=50):
        super().__init__()

        self.algorithm = cluster.AgglomerativeClustering(
            n_clusters=n_clusters,
            threshold=threshold,
            branching_factor=branching_factor
        )
