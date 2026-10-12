# pylint: disable=E0401,W0621
"""FR : Tests des traitements de la centrale d'achat (bin : logos, doublons, traduction du fichier


     des comptes, mise à jour des comptes des articles) et de l'import des comptes
EN : Tests for purchasing center processings and accounts import

created at: 2026-10-11
created by: Paulo ALVES
"""

import csv
import io
import logging

import pytest

from apps.articles.models import ArticleAccount
from apps.centers_purchasing.bin import data_pre_processing_pool, update_account_article
from apps.centers_purchasing.bin.copy_logos import copy_static
from apps.centers_purchasing.bin.data_post_processing_pool import post_axe_pro_account
from apps.centers_purchasing.bin.data_pre_processing_pool import (
    get_account,
    get_axe_pro,
    get_big_category,
    get_sub_category,
    translate_accounts_axe_pro_category,
)
from apps.centers_purchasing.bin.duplicates import duplicates_delete_accounts
from apps.centers_purchasing.bin.update_account_article import (
    delete_orphans_accounts,
    set_update_articles_account,
    set_update_articles_confict_account,
    update_axes_edi,
)
from apps.centers_purchasing.excel_outputs.output_excel_account_axe_list import (
    excel_liste_account_axe,
)
from apps.centers_purchasing.imports.imports_data import axe_pro_account
from apps.centers_purchasing.models import AccountsAxeProCategory
from apps.data_flux.exceptions import DuplicatesError, ModelFieldError
from apps.data_flux.models import Trace
from apps.edi.models import EdiImport

pytestmark = pytest.mark.django_db


# LOGOS ============================================================================================


def test_copy_static_copie_les_logos_existants(media_dirs):
    """Chaque logo présent dans media/logos est copié dans static, static/images et static/img"""
    (media_dirs.logos / "acuitis.png").write_bytes(b"PNG acuitis")

    copy_static({"logos/acuitis.png", "logos/absent.png"})

    for directory in (media_dirs.static, media_dirs.static / "images", media_dirs.static / "img"):
        assert (directory / "acuitis.png").read_bytes() == b"PNG acuitis"
        assert not (directory / "absent.png").exists()


# DOUBLONS =========================================================================================


def test_duplicates_delete_accounts(make_accounts_axe_pro_category, make_sub_category):
    """Avec une rubrique nulle, l'unicité ne joue pas : seul le doublon le plus récent est gardé"""
    make_accounts_axe_pro_category(child_center="ACF", vat="001")
    make_accounts_axe_pro_category(child_center="ACF", vat="001")
    last = make_accounts_axe_pro_category(child_center="ACF", vat="001")
    other = make_accounts_axe_pro_category(child_center="ACF", vat="002")
    with_sub = make_accounts_axe_pro_category(
        child_center="ACF", vat="001", sub_category=make_sub_category("Montures")
    )

    duplicates_delete_accounts()

    assert set(AccountsAxeProCategory.objects.values_list("pk", flat=True)) == {
        last.pk,
        other.pk,
        with_sub.pk,
    }


# TRADUCTION DU FICHIER DES COMPTES ================================================================


@pytest.fixture
def referentiel(
    make_child_center, make_big_category, make_sub_category, make_section, make_vat, make_account
):
    """Centrale, catégories, axe pro, tva et comptes nécessaires à la traduction d'un fichier"""
    make_child_center("ACF", name="Acuitis")
    category = make_big_category("Marchandises")
    return {
        "category": category,
        "sub": make_sub_category("Montures", big_category=category),
        "pro": make_section("PRO", "OPT", name="Optique"),
        "vat": make_vat("001"),
        "purchase": make_account("FRA", "607000"),
        "sale": make_account("FRA", "707000"),
        "sale_bel": make_account("BEL", "707000"),
    }


def test_resolutions_des_identifiants(referentiel):
    assert get_big_category("Marchandises") == referentiel["category"].uuid_identification
    assert get_sub_category("Montures") == referentiel["sub"].uuid_identification
    assert get_sub_category("") == ""
    assert get_axe_pro("OPT") == referentiel["pro"].uuid_identification
    assert get_account("FRA", "607000") == referentiel["purchase"].uuid_identification
    assert get_account("BEL", "707000") == referentiel["sale_bel"].uuid_identification


@pytest.mark.parametrize(
    ("function", "args", "message"),
    [
        (get_big_category, ("Inconnue",), "La Catégorie : 'Inconnue', n'existe pas"),
        (get_sub_category, ("Inconnue",), "La rubrique presta : 'Inconnue', n'existe pas"),
        (get_axe_pro, ("ZZZ",), "L'axe pro : 'ZZZ', n'existe pas"),
        (get_account, ("FRA", "999999"), "Le compte : 'FRA' - '999999', n'existe pas"),
    ],
)
def test_resolutions_inconnues(referentiel, function, args, message):
    function.cache_clear()

    with pytest.raises(ModelFieldError, match=message):
        function(*args)


def _export_file(tmp_path, name="LISTING_DES_COMPTES_2026_10_11_1.xlsx"):
    """Fichier excel au format de l'export de l'écran des comptes"""
    file_io = io.BytesIO()
    excel_liste_account_axe(file_io, name, "*")
    path = tmp_path / name
    path.write_bytes(file_io.getvalue())
    return path


def _read_rows(path):
    with path.open("r", encoding="utf8", newline="") as file:
        return list(csv.reader(file, delimiter=";", quotechar='"'))


def test_translate_depuis_l_export_de_l_ecran(
    referentiel, make_accounts_axe_pro_category, tmp_path
):
    """L'export de l'écran (14 colonnes) est traduit en 7 identifiants par ligne, sans entête"""
    with_sub = make_accounts_axe_pro_category(
        axe_pro=referentiel["pro"],
        big_category=referentiel["category"],
        sub_category=referentiel["sub"],
        child_center="ACF",
        vat="001",
    )
    without_sub = make_accounts_axe_pro_category(
        axe_pro=referentiel["pro"],
        big_category=referentiel["category"],
        child_center="ACF",
        vat="001",
    )

    csv_file = translate_accounts_axe_pro_category(_export_file(tmp_path))

    rows = _read_rows(csv_file)
    assert csv_file.suffix == ".csv"
    assert len(rows) == 2
    assert rows[0] == [
        "ACF",
        str(referentiel["category"].uuid_identification),
        str(referentiel["sub"].uuid_identification),
        str(referentiel["pro"].uuid_identification),
        "001",
        str(with_sub.purchase_account.uuid_identification),
        str(with_sub.sale_account.uuid_identification),
    ]
    assert rows[1][2] == ""
    assert rows[1][5] == str(without_sub.purchase_account.uuid_identification)


def test_translate_doublons_dans_le_fichier(
    referentiel, make_accounts_axe_pro_category, tmp_path, monkeypatch
):
    """Deux lignes de même clé dans le fichier : DuplicatesError"""
    make_accounts_axe_pro_category(
        axe_pro=referentiel["pro"],
        big_category=referentiel["category"],
        child_center="ACF",
        vat="001",
    )
    original = data_pre_processing_pool.excel_file_to_csv_string_io

    def _doubled(file, csv_io):
        original(file, csv_io)
        lines = csv_io.getvalue().splitlines(keepends=True)
        csv_io.seek(0)
        csv_io.truncate()
        csv_io.write("".join(lines) + lines[-1])
        csv_io.seek(0)

    monkeypatch.setattr(data_pre_processing_pool, "excel_file_to_csv_string_io", _doubled)
    export_file = _export_file(tmp_path)

    with pytest.raises(DuplicatesError):
        translate_accounts_axe_pro_category(export_file)


def test_translate_plan_comptable_absent_vaut_fra(referentiel, tmp_path, monkeypatch):
    """Sans plan comptable dans le fichier, le compte est cherché sur le plan FRA"""

    def _fake(_file, csv_io):
        csv_io.write(
            "titre\n\n\nentetes\n"
            + ";".join(
                [
                    "ACF",
                    "Acuitis",
                    "01",
                    "Marchandises",
                    "",
                    "",
                    "OPT",
                    "Optique",
                    "FRA",
                    "001",
                    "",
                    "607000",
                    "",
                    "707000",
                ]
            )
            + "\n"
        )
        csv_io.seek(0)

    monkeypatch.setattr(data_pre_processing_pool, "excel_file_to_csv_string_io", _fake)
    source = tmp_path / "comptes.xlsx"
    source.write_bytes(b"")

    rows = _read_rows(translate_accounts_axe_pro_category(source))

    assert rows == [
        [
            "ACF",
            str(referentiel["category"].uuid_identification),
            "",
            str(referentiel["pro"].uuid_identification),
            "001",
            str(referentiel["purchase"].uuid_identification),
            str(referentiel["sale"].uuid_identification),
        ]
    ]


# IMPORT DES COMPTES (chaîne complète) =============================================================


@pytest.mark.integration
def test_axe_pro_account_importe_l_export_et_cree_les_comptes_des_articles(
    referentiel, media_dirs, make_accounts_axe_pro_category, make_article, make_society, tmp_path
):
    """Export, modification du compte, ré-import : la ligne importée gagne, fichier sauvegardé, articles complétés"""
    account = make_accounts_axe_pro_category(
        axe_pro=referentiel["pro"],
        big_category=referentiel["category"],
        child_center="ACF",
        vat="001",
    )
    article = make_article(
        "ART-1",
        society=make_society("FOUR001", is_client=False),
        big_category=referentiel["category"],
        axe_pro=referentiel["pro"],
    )
    file = _export_file(media_dirs.import_accounts)
    account.sale_account = referentiel["sale_bel"]
    account.save()

    axe_pro_account(file)

    trace = Trace.objects.get()
    imported = AccountsAxeProCategory.objects.get()
    assert trace.errors is False
    assert trace.errors_numbers_records == 0
    assert imported.pk != account.pk
    assert imported.sale_account == referentiel["sale"]
    assert not file.exists()
    assert (media_dirs.backup_accounts / file.name).exists()
    assert not (media_dirs.import_accounts / "LISTING_DES_COMPTES_2026_10_11_1.csv").exists()
    assert ArticleAccount.objects.get(article=article).sale_account == "707000"


@pytest.mark.integration
def test_axe_pro_account_fichier_invalide(referentiel, media_dirs, caplog):
    """Un fichier qui n'est pas un classeur est tracé en erreur et conservé"""
    file = media_dirs.import_accounts / "LISTING_DES_COMPTES_2026_10_11_2.xlsx"
    file.write_bytes(b"pas un classeur")

    with caplog.at_level(logging.ERROR, logger="imports"):
        axe_pro_account(file)

    assert Trace.objects.get().errors is True
    assert file.exists()
    assert "Exception Générale" in caplog.text


# COMPTES DES ARTICLES =============================================================================


@pytest.fixture
def articles_et_comptes(
    referentiel,
    make_accounts_axe_pro_category,
    make_article,
    make_society,
    make_section,
    make_big_category,
):
    """Deux articles de la catégorie Marchandises / axe OPT, un paramétrage de comptes ACF 001"""
    four = make_society("FOUR001", is_client=False)
    settings = make_accounts_axe_pro_category(
        axe_pro=referentiel["pro"],
        big_category=referentiel["category"],
        child_center="ACF",
        vat="001",
    )
    first = make_article(
        "ART-1", society=four, big_category=referentiel["category"], axe_pro=referentiel["pro"]
    )
    new = make_article(
        "ART-2",
        society=four,
        big_category=referentiel["category"],
        axe_pro=referentiel["pro"],
        new_article=True,
    )
    other = make_article(
        "ART-3",
        society=four,
        big_category=make_big_category("Services"),
        axe_pro=make_section("PRO", "SRV"),
    )
    return {"settings": settings, "first": first, "new": new, "other": other, "society": four}


def test_set_update_articles_account_global_et_unitaire(articles_et_comptes):
    """Les comptes manquants sont créés pour les articles non nouveaux, ou pour un article donné"""
    set_update_articles_account()

    accounts = {row.article.reference: row for row in ArticleAccount.objects.all()}
    assert set(accounts) == {"ART-1"}
    assert (
        accounts["ART-1"].purchase_account,
        accounts["ART-1"].sale_account,
        accounts["ART-1"].vat.vat,
    ) == ("607000", "707000", "001")

    set_update_articles_account(articles_et_comptes["new"].uuid_identification)

    assert set(ArticleAccount.objects.values_list("article__reference", flat=True)) == {
        "ART-1",
        "ART-2",
    }

    set_update_articles_account()

    assert ArticleAccount.objects.count() == 2


def test_set_update_articles_confict_account(articles_et_comptes, make_article_account):
    """Les articles (nouveaux compris) sans compte pour la centrale / tva sont complétés, sans doublon"""
    make_article_account(
        articles_et_comptes["first"], "ACF", "001", purchase_account="601000", sale_account="701000"
    )

    set_update_articles_confict_account()

    accounts = {row.article.reference: row for row in ArticleAccount.objects.all()}
    assert set(accounts) == {"ART-1", "ART-2"}
    assert accounts["ART-1"].purchase_account == "601000"
    assert accounts["ART-2"].purchase_account == "607000"


def test_post_axe_pro_account(articles_et_comptes):
    post_axe_pro_account()

    assert ArticleAccount.objects.filter(article__reference="ART-1").exists()


def test_delete_orphans_accounts(articles_et_comptes, make_article_account):
    """Les comptes d'articles sans paramétrage correspondant sont supprimés"""
    kept = make_article_account(articles_et_comptes["first"], "ACF", "001")
    orphan_vat = make_article_account(articles_et_comptes["first"], "ACF", "002")
    orphan_axe = make_article_account(articles_et_comptes["other"], "ACF", "001")

    delete_orphans_accounts()

    assert set(ArticleAccount.objects.values_list("pk", flat=True)) == {kept.pk}
    assert not ArticleAccount.objects.filter(pk__in=[orphan_vat.pk, orphan_axe.pk]).exists()


def test_update_axes_edi(articles_et_comptes, make_edi_import, make_section):
    """Les lignes edi dont les axes diffèrent de l'article sont réalignées, les autres inchangées"""
    first = articles_et_comptes["first"]
    outdated = make_edi_import(
        "FOUR001", "ART-1", axe_pro=make_section("PRO", "OLD"), big_category=first.big_category
    )
    aligned = make_edi_import(
        "FOUR001", "ART-1", axe_pro=first.axe_pro, big_category=first.big_category
    )
    unknown = make_edi_import(
        "FOUR001", "ART-9", axe_pro=make_section("PRO", "OLD"), big_category=first.big_category
    )

    update_axes_edi()

    outdated.refresh_from_db()
    aligned.refresh_from_db()
    unknown.refresh_from_db()
    assert outdated.axe_pro == first.axe_pro
    assert outdated.big_category == first.big_category
    assert aligned.axe_pro == first.axe_pro
    assert unknown.axe_pro.section == "OLD"
    assert EdiImport.objects.count() == 3


def test_set_update_articles_confict_account_est_idempotent(articles_et_comptes):
    set_update_articles_confict_account()
    set_update_articles_confict_account()

    assert ArticleAccount.objects.count() == 2
    assert callable(update_account_article.delete_orphans_accounts)
