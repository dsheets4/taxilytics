import django_filters

from .models import ClusterConfig, ClusterModel


def _make_cluster_filterset(relation='', m=ClusterConfig):
    """
    Since many items are related to an Entity, and it's convenient to filter by
    criteria related to a trip, this function helps create new classes that
    allow various related objects to generate an appropriate filter.
    """
    class NewClusterFilterSet(django_filters.FilterSet):

        class Meta:
            model = m
            fields = [
                '%salgorithm' % (relation),
            ]

    return NewClusterFilterSet


ClusterConfigFilterSet = _make_cluster_filterset()
ClusterModelFilterSet = _make_cluster_filterset(
    relation='config__', m=ClusterModel)
