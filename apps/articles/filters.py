# pylint: disable=E0401,R0903
"""
Filtres pour des recherches dans les views
"""
import django_filters

from apps.articles.models import Article, ArticleAccount


class ArticleFilter(django_filters.FilterSet):
    """Filtre des articles"""

    class Meta:
        """class Meta django"""

        model = Article
        fields = {
            "third_party_num": ["exact"],
            "reference": ["exact", "icontains"],
            "libelle": ["exact", "icontains"],
            "libelle_heron": ["exact", "icontains"],
            "big_category": ["exact"],
            "sub_category": ["exact"],
            "axe_pro_supplier": ["exact"],
        }


class ArticleAccountFilter(django_filters.FilterSet):
    """Filtre des articles / comptes x3"""

    class Meta:
        """class Meta django"""

        model = ArticleAccount
        fields = ["child_center"]
        # fields = {
        #     "third_party_num": ["exact"],
        #     "reference": ["exact", "icontains"],
        #     "libelle": ["exact", "icontains"],
        #     "libelle_heron": ["exact", "icontains"],
        #     "big_category": ["exact"],
        #     "sub_category": ["exact"],
        #     "axe_pro_supplier": ["exact"],
        # }
