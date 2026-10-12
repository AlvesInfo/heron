# Directives qualité — projet heron

Document de pilotage. Chaque directive est autonome : elle peut être soumise seule à Claude
(« applique la directive D3 ») et contient tout le contexte nécessaire. Cocher l'état au fil de l'eau.

État au 2026-10-11 : D0 réalisée pour `accountancy`, `core` (vue `api_models_query`),
`centers_clients`, `articles`, `edi`, `compta`, `invoices`, `validation_purchases` ; D1 réalisée
(1 604 tests, 100 % lignes + branches, ~60 s).

Légende : `[ ]` à faire · `[~]` en cours · `[x]` fait

---

## D0 — Conventions de test (socle, toujours applicable)

Règles valables pour toute directive de type « tester l'app X ».

- **Objectif** : 100 % de couverture lignes **et** branches de l'app, sans ligne exclue hormis
  `if __name__ == "__main__":`.
- **Ordre** : corriger les bugs révélés **avant** d'écrire les tests qui les figeraient. Chaque
  correction est signalée dans le compte rendu (fichier, symptôme, correction).
- **Forme** : pytest, fonctions de test uniquement (pas de classes), fixtures-fabriques en
  fonctions, context managers pour le patching et les fichiers temporaires.
- **Conftests** :
  - `conftest.py` racine = bibliothèque générique : `patched_attrs`, `csv_file`,
    `captured_queries`, `raising_once`, `heron_settings`, `sage_dirs`, `make_csv`, `make_trace`,
    `make_user`, `logged_client`, `ajax_client`, fabriques de référentiels (`make_society`,
    `make_article`, `make_maison`, `make_section`, `make_vat`, `make_account`, ...).
  - `apps/<app>/tests/conftest.py` = uniquement les fabriques propres à l'app.
  - Les fabriques sont idempotentes (get-or-create) ; un test de doublon crée le doublon lui-même.
- **Commandes** :
  - une app : `uv run pytest apps/<app>/tests --cov=apps/<app>`
  - tout : `uv run pytest --cov` (ajouter l'app dans `[tool.coverage.run] source` et dans
    `testpaths` de `pyproject.toml`)
  - après un changement de modèle : `--create-db`
- **Pièges connus** :
  - `FlagsTable.delete` est un BooleanField : supprimer via QuerySet, jamais `instance.delete()`
    (voir D4).
  - Les réglages se lisent via `django.conf.settings` (D7) : dans les tests, la fixture
    `settings` de pytest-django ; les fixtures de répertoires (`sage_dirs`, `edi_dirs`,
    `invoices_dirs`...) la posent déjà.
  - Fixtures des modules d'aide `helpers_*.py` : exposées par le conftest de l'app, ne pas les
    importer dans les tests ; paramètre de fixture non utilisé dans le corps du test ->
    `@pytest.mark.usefixtures("nom")`. Lint : `uv run ruff check conftest.py apps/*/tests`.
  - Jamais de `reverse()` à la collecte (paramétrage) : construire les URLs dans le test.
  - Aucun module du projet ne doit interroger la base à l'import (garde-fou :
    `apps/core/tests/test_project_import.py`). Les schémas djantic de `edi` se construisent via
    `get_schema(name)` à l'appel, jamais par import de classe.
  - Tables FDW (`heron_bi_*`, `heron_directbi_*`) : créées en DDL dans la transaction de test.
  - pandas `read_excel` convertit les colonnes en float si les lignes de titre ignorées sont
    vides : remplir toutes les colonnes des lignes ignorées dans les classeurs de test.
  - Sous Python 3.11, coverage doit être ≥ 7 (pin 7.6.12).
- **Interdits** : écrire dans `files/` ou sur les répertoires réels, appeler la base de prod, tests
  dépendant de l'ordre d'exécution.
- **Compte rendu attendu** : liste des bugs corrigés, nombre de tests, sortie de coverage, ce qui
  n'a volontairement pas été corrigé et pourquoi.

---

## D1 — Supprimer l'accès base à l'import de `apps/edi` `[x]`

- **Constat** : `apps/edi/forms/forms_djantic/forms_invoices.py` construit ses schémas djantic à
  partir de `ColumnDefinition` en base au moment de l'import. Conséquences : `heron/urls.py` ne se
  charge pas sur une base vide, pydantic lève `ConfigError` puis « duplicate validator » aux
  imports suivants, les migrations et les tests dépendent d'un instantané
  (`apps/edi/tests/test_fixtures/column_definitions.json`).
- **Objectif** : aucun accès base pendant l'import d'un module Python du projet.
- **Approche recommandée** : construction paresseuse des schémas (fonction `get_schema(name)`
  mémoïsée avec `functools.lru_cache`, ou construction à la première utilisation dans la vue /
  l'import). Les modules appelants (`apps.compta`, vues `edi`) appellent la fonction au lieu
  d'importer la classe.
- **Critères d'acceptation** :
  - `python -c "import heron.urls"` passe sur une base vide (settings de test, avant loaddata).
  - Le `loaddata` autouse de session dans le conftest racine peut être retiré, ou ne sert plus
    qu'aux tests fonctionnels d'`edi`.
  - Suite complète toujours à 100 %.
- **Hors périmètre** : modifier la structure de `ColumnDefinition`.
- **Réalisé le 2026-10-10** : `forms_invoices.py` réécrit en déclaratif (`SCHEMA_DEFINITIONS`,
  `build_schema`, `get_schema` mémoïsé, validateurs de date partagés avec `allow_reuse`) ;
  le pool d'import appelle `get_schema("XSchema")` dans chaque fonction ; schémas vérifiés
  identiques aux anciens (include, champs, défauts, validateurs). Le `loaddata` de session
  n'est plus autouse : fixture `column_definitions_data` à la demande. Garde-fou :
  `apps/core/tests/test_project_import.py` importe l'URLconf dans un sous-processus avec une
  base inexistante.

---

## D2 — Tests de `apps/edi` `[x]`

- **Pré-requis** : D1 (fait). Les schémas se testent isolément avec les fabriques
  `make_supplier_definition` / `make_column_definitions` et la fixture `schema_cache_cleared`
  de `apps/edi/tests/conftest.py` ; l'instantané de production se charge avec
  `column_definitions_data`.
- **Réalisé le 2026-10-10** : 349 tests (`apps/edi/tests`, 30 fichiers + conftest + helpers),
  100 % lignes et branches sur les 11 800 lignes de l'app, suite projet 968 tests à 100 %.
  Bugs corrigés : voir compte rendu de session (set_hand_invoices finally/unit_weight,
  tasks, loops, get_user_automate, set_signboard, cache redis, johnson, SQL widex/interson/
  generic, duplicates_check comment NULL, bbgr_monthly dict, prints bbgr/chrono/serializers,
  set_hand_sales_prices supprimé, NullZeroDecimalField dans apps/core).
  Points laissés tels quels, à confirmer : la fonction PostgreSQL maison `is_date(text)`
  (sql_interson) n'existe pas dans le schéma Django (fixture `pg_is_date` la recrée ; à porter en
  migration RunSQL) ; `edi_import_duplicate_check` marque en erreur la trace du dernier import
  alors que ce sont les lignes du plus ancien qui sont supprimées ; bbgr monthly/retours :
  `livraison = '0'` devient le n° de facture ; starkey copie vers edi_starkeydepot avant
  normalisation des quantités ; `data_flux/validation.py` a un print (D8) ; `get_retours_valid`
  lit `connections["bi_bdd"]` (testé en patchant vers default).
- **Appliquer D0.** Points d'attention : flux d'import fournisseurs (fichiers `data_flux` réels
  disponibles pour des tests `@pytest.mark.integration`), schémas djantic par fournisseur,
  tâches de post-traitement SQL, vues d'import.
- **Spécifique** : les fichiers d'exemple réels restent en lecture seule ; les tests d'écriture
  utilisent `tmp_path` via `sage_dirs` / un équivalent `edi_dirs` à créer dans le conftest d'app.

---

## D3 — Tests de `apps/compta`, `apps/invoices`, `apps/validation_purchases` `[x]`

- **Pré-requis** : D2 (ces apps consomment les imports `edi`).
- **Appliquer D0**, une app par soumission, dans cet ordre : `compta` → `invoices` →
  `validation_purchases`.
- **Points d'attention** : `apps/invoices/sql_files/sql_invoices_insertions.py` (1528 lignes de
  SQL) et `apps/invoices/bin/fpdf2/pdf_base.py` (1271 lignes) ; `validation_purchases/views`
  concentre 14 appels `is_ajax()` (voir D5). Les PDF générés sont comparés par contenu texte
  extrait, pas par octets.
- **Réalisé le 2026-10-11** : compta 88 tests, invoices 378 tests (24 fichiers), validation_purchases
  202 tests (16 fichiers) ; projet 1 655 tests à 100 % lignes + branches en ~65 s (base recréée).
  Code mort supprimé : 10 modules `invoices/bin/api_gmail` (variantes jamais importées), 2 benchmarks,
  `validation_purchases/__init__.py` (330 lignes de POST collées avec jeton CSRF).
  Principaux bugs corrigés : contrôle des totaux achats jamais exécuté à l'insertion ; compteurs
  remis à NULL sans facture ; export 5.3A (CA par familles) échouait toujours (18 colonnes vs 17) ;
  objets Gmail construits à l'import (OAuth interactif possible au chargement de l'URLconf) ; tâche
  SSE Gmail sans décorateur ; mapping Factur-X du moyen de paiement par uuid sur un libellé ;
  traversée de répertoire sur le téléchargement des PDF et exports X3 ; redirections en boucle ou
  NoReverseMatch dans 5 vues de validation ; gardes ajax `and` -> `or` (15 vues) ; lecture
  positionnelle de `request.POST.values()` ; formulaires de suppression sans champ ; échéance sans
  condition de paiement (TypeError, apps/core) ; `trace_change` sur enregistrement absent et FK en
  instance (apps/core) ; plantages du sommaire PDF ; 15+ `print()` -> loggers ; `except:` nus.
  À arbitrer (non modifié) : exports X3 odana/ventes/achats nommés `<fcy>_<num>.txt` avec trois
  compteurs distincts (collision = fichier écrasé dans le zip) ; moteurs fpdf2 et playwright supprimés
  le 2026-10-11 (jamais importés, dépendances fpdf2/playwright retirées) ; route `/send_email_essais/`
  retirée (vue et tâche d'essai conservées, non routées) ; SQL validation_purchases : parties
  edi sans filtre valid/delete (clients_news, cct_franchiseur, suppliers_m_m1, refac_cct), produit
  cartésien dans sql_subscriptions, `sql_ca_familly_cct.sql` sans colonne commentaire (contourné en
  Python), `sql_current_purchases_csv.sql` écrit côté serveur ; `SQL_SALES_DETAILS_BACKUP` et
  `SQL_*_ACCOUNTS` vides dans sql_invoices_insertions ; `core.bin.emails.send_mass_mail` en smtplib
  direct ; modules excel qui mutent `COLUMNS` au niveau module.

---

## D4 — Renommer le champ `FlagsTable.delete` `[ ]`

- **Constat** : `apps/core/models.py` `FlagsTable.delete = BooleanField` masque
  `Model.delete()` sur toutes les tables qui en héritent. `instance.delete()` lève
  `'bool' object is not callable`.
- **Objectif** : champ renommé (proposition : `deleted`, `db_column="delete"` dans un premier
  temps pour éviter de toucher le SQL brut), méthode `delete()` de Django de nouveau utilisable.
- **Étapes** :
  1. Inventaire : `grep -rn "\.delete\b\|delete=" apps --include=*.py --include=*.html
     --include=*.sql` ; distinguer champ / méthode / filtre `delete=False`.
  2. Renommage du champ avec `db_column="delete"` → une migration par app héritant de
     FlagsTable, sans modification de schéma.
  3. Mise à jour des querysets, filtres django-filter, templates, SQL brut (`"delete"` reste la
     colonne, seul l'ORM change).
  4. Phase 2 optionnelle : retirer `db_column` et renommer la colonne en base.
- **Critères d'acceptation** : suite complète verte avec `--create-db`, `makemigrations --check`
  propre, tests ajoutés sur `instance.delete()` dans `apps/core/tests`.
- **Risque** : SQL brut et vues B.I qui référencent la colonne `delete` ; la phase 1 ne les touche
  pas.

---

## D5 — Remplacer `request.is_ajax()` `[x]`

- **Constat** : 51 appels dans `apps` (validation_purchases 14, rfa 6, parameters 5,
  centers_purchasing 5, centers_clients 5, book 2, users / invoices / edi / core 1 chacun).
  Méthode supprimée dans Django 4.0.
- **Objectif** : une fonction unique `apps/core/functions/functions_http.py::is_ajax(request)`
  testant `request.headers.get("x-requested-with") == "XMLHttpRequest"`, utilisée partout.
- **Critères d'acceptation** : `grep -rn "is_ajax()" apps` ne renvoie que la définition ; la
  fixture `ajax_client` du conftest racine continue de fonctionner ; tests unitaires de la
  fonction.
- **Note** : garder la sémantique des gardes `if not is_ajax(request) or request.method != "POST"`
  déjà corrigées dans `centers_clients` et `articles`.
- **Réalisé le 2026-10-11** : `is_ajax(request)` dans `apps/core/functions/functions_http.py`
  (en-tête `x-requested-with`, insensible à la casse) ; 51 appels remplacés dans 42 fichiers de 12
  apps ; tests `apps/core/tests/test_functions_http.py`, dont un garde-fou qui échoue si un
  `.is_ajax()` réapparaît dans le code. Suite : 1 610 tests, 100 %.

---

## D6 — Migration Django 3.2 → 4.2 LTS `[ ]`

- **Pré-requis** : D5 ; idéalement D1, D2, D3 pour avoir un filet.
- **Points connus** : `NullBooleanField` modèle supprimé (vérifier les modèles), `url()` →
  `re_path`, `USE_L10N`, `DEFAULT_AUTO_FIELD`, `django-axes` et autres dépendances à monter en
  version, `CSRF_TRUSTED_ORIGINS` avec schéma.
- **Fait le 2026-10-10 (préalable)** : `pyproject.toml` nettoyé de 269 à 48 dépendances directes
  + groupe `dev` (pytest, coverage, debug-toolbar, black, pylint, ruff). Décision : aucune montée
  de version avant les tests ; les transitives Google sont figées dans
  `[tool.uv] constraint-dependencies` au niveau d'avant (lock identique à HEAD hors coverage).
  Retirer ce bloc au moment de D6.
- **Méthode** : `python -W error::DeprecationWarning manage.py check` sur 3.2 d'abord, corriger,
  puis passer la version dans `pyproject.toml` et `uv lock`.
- **Critères d'acceptation** : `manage.py check --deploy` sans erreur, migrations à jour, suite
  complète verte.

---

## D7 — Lire `django.conf.settings` et non le module `heron.settings` `[x]`

- **Constat** : 10 modules métier importent directement le module `heron.settings`. Les réglages
  surchargés par environnement (`heron.settings.test`, futurs `prod`/`staging`) ne sont pas vus.
- **Objectif** : `from django.conf import settings` partout hors du package `heron.settings`.
- **Critères d'acceptation** : `grep -rn "from heron import settings\|from heron.settings import\|import heron.settings" apps` vide ; la fixture `heron_settings` du conftest racine
  devient inutile et est retirée au profit de la fixture `settings` de pytest-django.
- **Impact tests** : remplacer les `patched_attrs(monkeypatch, heron_settings, ...)` par
  `settings.X = ...`.
- **Réalisé le 2026-10-11** : `functions_setups.settings` est `django.conf.settings` ; 31 modules
  basculés (imports nominatifs `from heron.settings import X` -> `settings.X`, `heron.settings.base`
  -> `settings`, `heron/loggers.py`, `heron/processors.py`, `users/views.py`) ; `settings.path_env`
  (minuscule, non exposé par Django) -> `settings.ENV_ROOT`. Restent volontairement sur le module :
  `heron/bin/*.py` (scripts hors Django) et la commande `init_directories` (introspection des
  sous-modules). Fixture `heron_settings` supprimée, toutes les fixtures de répertoires passent
  par la fixture `settings` de pytest-django.
- **Hygiène des tests (2026-10-11, suite aux avertissements SonarLint)** : fixtures des modules
  `helpers_*.py` exposées par les conftests d'app (plus d'import de fixtures dans les tests, 3
  collisions renommées) ; 307 paramètres de fixtures inutilisés convertis en
  `@pytest.mark.usefixtures` (271 tests) ; imports inutilisés, parametrize, yield sans teardown,
  conditions Yoda, classes factices nommées, `ClassVar`, `pytest.raises` trop larges corrigés.
  Règle SonarLint python:S9073 (assertion composée `assert a and b`) = ruff PT018 : 341 assertions
  scindées. Règle python:S3776 (complexité cognitive > 15) : aucune fonction des tests au-dessus du
  seuil ; dans le code, `file_for_insert_excel_to_csv` (articles), `write_rows` (abonnements) et
  `write_sum` (RFA) découpées ; puis les 16 fonctions des apps couvertes (edi 8, invoices 6,
  validation_purchases 1, centers_clients 1) ramenées sous 15 SANS toucher aux tests (198 fichiers
  de tests identiques au SHA près, 1 646 tests, 100 %). Restent 15 fonctions dans des apps sans
  tests (core, data_flux, users, book, centers_purchasing, od, commandes de gestion) : à traiter
  après leur couverture. Bugs repérés pendant ce découpage, corrigés ensuite le 2026-10-11 avec
  leurs tests (1 653 tests) : division par zéro en saisie manuelle (qty 0 + TVA saisie) ; flux ou
  import B.I inconnu signalé par une erreur explicite au lieu d'un TypeError ;
  `purchase_without_suppliers_update` : mise à jour tiers + import dans une même transaction,
  « success » seulement si l'import est rattaché, et le JavaScript recharge la page sur « ko » au
  lieu de naviguer vers l'url « ko » ; tâche Gmail SSE et `send_mass_mail` : un email n'est compté
  qu'une fois, pièces jointes facultatives, l'échec du suivi ne change plus le résultat de l'envoi.
  Reste à arbitrer : collision des noms de fichiers X3.
  Mesure : `uv run --with cognitive-complexity`.
  Règles Web:S6853 et Web:InputWithoutLabelCheck (labels et champs de formulaire) : 48 avertissements
  corrigés dans 17 templates, plus aucun dans le projet. Config `[tool.ruff]` ajoutée au pyproject : `uv run ruff check conftest.py apps/*/tests` est propre.
  Lot de 14 avertissements du 2026-10-11 : page `heron/404.html` (doctype, `lang`, plus de
  `bgcolor` / `<center>` / `<image>`), code commenté retiré (`accountancy/bin/__init__.py` vidé,
  `articles_fixtures.py`), icônes de suppression accessibles au clavier (`role="button"`,
  `tabindex`, `onkeydown`, `aria-label`) dans `account_axe_list_table.html` et
  `articles_account_vat_update_table.html`, et Web:S5247 : la pagination
  (`functions_http.get_pagination_buttons`) est construite avec `format_html` et affichée sans
  `|safe` dans 6 templates (rendu identique octet pour octet, garde-fou en test).
  Tour complet du 2026-10-11 : les 27 autres icônes de suppression `<i onclick>` ont reçu le même
  correctif clavier (plus aucun élément non interactif avec gestionnaire souris seul). Tour
  `|safe` / `autoescape off` : 26 occurrences ramenées à 3. Faille réelle corrigée :
  `attrs_filter|safe` écrivait les paramètres de l'URL bruts dans un script de
  `base_semantic.html` (injection par `</script>`), remplacé par `json_script`. Filtres à liste
  blanche `keep_br` et `trace_comment` (`heron/templatetags/filters_tags.py`) pour les libellés
  de mois, le PDF personnel et les commentaires de trace (données de fichiers fournisseurs
  échappées, seuls `<br>` et le bloc indenté des doublons passent). Titres avec HTML construits
  par `format_html` dans 4 vues. `datatable_ordering` est une donnée (`{"order": [(1, "desc")]}`)
  et non plus du code JavaScript. `base_modals.html` et `ModalForms` (orphelins) supprimés. Emails
  de mot de passe en texte brut renommés en `.txt`. Restent volontairement 3 `|safe` : mentions
  légales, pied de page et message d'enseigne des factures PDF, texte riche saisi dans CKEditor
  par les administrateurs et rendu par WeasyPrint (aucun script exécuté). Garde-fous :
  `apps/core/tests/test_templates_security.py`.
  Web:S6819 (2026-10-11) : `role="button"` sur une icône est lui-même signalé, les 29 corbeilles
  sont donc de vrais `<button type="button">` transparents et sans bordure qui enveloppent
  l'icône `<i class="red trash icon" aria-hidden="true">` (rendu mesuré identique dans Chrome :
  position, taille, couleur, hauteur de ligne). Même bouton pour les lignes générées par
  `apps/users/views.py`. Garde-fous : `apps/core/tests/test_templates_accessibility.py`.
  SonarLint n'est pas exécutable hors PyCharm (pas de scanner, de serveur ni de Java sur le poste) :
  ruff joue le rôle de contrôle reproductible.

---

## D8 — Journalisation : plus de `print()`, exceptions ciblées `[x]`

- **Constat** : 313 `print()` hors tests, 151 `except Exception`.
- **Objectif** :
  - aucun `print()` dans `apps/` hors `bin/` exécutables et scripts de bootstrap ; utiliser les
    loggers de `heron/loggers.py` (`LOGGER_IMPORT`, `LOGGER_EXPORT_EXCEL`, ...).
  - chaque `except Exception` soit : réduit au type attendu, soit conservé mais avec
    `logger.exception(...)` et un commentaire justifiant le filet (vue utilisateur, boucle
    d'import).
- **Méthode** : par app, lors du passage en D0, et en bloc pour les apps déjà testées.
- **Critères d'acceptation** : `grep -rn "^\s*print(" apps --include=*.py | grep -v /tests/ |
  grep -v /bin/` vide ; aucune régression de couverture.
- **Réalisé le 2026-10-11** : 132 `print()` remplacés par les loggers de `heron/loggers.py`
  (choix par emplacement : vues -> error_views, exports -> export_excel, imports/bin/loops ->
  imports, data_flux -> loader/validation/postgres_save, invoices -> invoices_flux, edi -> edi,
  reste -> django ; `.exception` dans un `except`, `.info` sinon) dans 114 fichiers ; 108 `except:`
  nus -> `except Exception:` ; 4 `except Exception` silencieux journalisés (mail_alertes,
  tasks_gmail_sse). Restent des `print` uniquement sous `if __name__ == "__main__":` (26), dans
  `heron/bin`, `heron/env` et `heron/settings/__init__.py` (affichage LOCAL_SETTINGS au démarrage,
  avant toute configuration de logging). Les tests qui lisaient stdout (capsys) lisent les
  enregistrements de log (caplog, logger nommé). 148 `except Exception` conservés : tous
  journalisent ou relèvent.

---

## D9 — Factoriser les exports Excel `[x]`

- **Constat** : 76 modules `excel_outputs`, structure quasi identique (requête → entêtes →
  `GenericExcel` → colonnes). Doublon identique déjà supprimé dans `articles`.
- **Objectif** : un générateur unique `apps/core/excel/generic_list_export.py` prenant
  (titre, requête ou queryset, liste de colonnes, formats) ; chaque export devient une
  déclaration de colonnes + requête.
- **Méthode** : commencer par les apps testées (`centers_clients`, `articles`) pour disposer du
  filet, puis migrer les autres au fil de D0. Ne pas réécrire `columns_excel.py` /
  `book_columns.py` (1700 lignes) : les brancher tels quels.
- **Critères d'acceptation** : fichiers produits identiques (comparaison par `openpyxl` cellule à
  cellule dans les tests), couverture inchangée.
- **Réalisé le 2026-10-11 (phase 1)** : `apps/core/excel_outputs/generic_list_export.py` expose
  `excel_list_export(file_io, file_name, *, sheet_name, title, columns, rows, orientation,
  repeat_row, fit_page, header_row, odd_color, odd_first, in_memory, merged_headers, hide_zero)` ;
  `rows` peut être une fonction, évaluée dans le try (erreur de requête -> KO). 45 des 64 exports
  (toutes les listes « titre + date + entêtes + lignes ») y sont ramenés par une transformation
  AST : chaque fonction d'export garde sa signature publique et devient préambule + un appel.
  Tests du générique dans `apps/core/tests/test_generic_list_export.py` ; les tests d'app qui
  forçaient une erreur patchent désormais `generic_list_export`. Suite : 1 618 tests, 100 %.
- **Réalisé le 2026-10-11 (phase 2)** : le générique devient multi-feuilles (`SheetSpec`,
  `excel_sheets_export`, `excel_list_export` = une feuille) avec points d'extension : `columns`
  calculables (`with_headers`, `month_headers` : copies, plus de mutation des listes de colonnes au
  niveau module), `writer` pour l'écriture spécifique des lignes (blocs par client, sous-totaux,
  `write_alternate_rows` réutilisable), `after_rows` (formats conditionnels), `footer`
  (`PAGE_NUMBERS_FOOTER`), `write_headers`, `hide_zero`, `extra_formatting`. Il s'appuie sur
  `GenericExcelOptimized` (formats mis en cache) : tous les exports en profitent. Les 62 exports
  restants passent par le générique ; les deux versions « classiques » des achats/ventes non
  finalisés, non utilisées par les vues, sont supprimées (seules les versions optimisées, réécrites
  sur le générique avec lecture par lots, subsistent). excel_outputs : 19 342 -> 17 573 lignes.
  Suite : 1 622 tests, 100 %.

---

## D10 — Connexions base : plus de psycopg2 direct `[~]`

- **Fait le 2026-10-10** : `cnx_postgresql(CNX_STRING).cursor()` remplacé par
  `django.db.connection.cursor()` dans 6 modules (`articles`, `centers_purchasing` ×3, `book` ×2).
  Plus aucun usage de `CNX_STRING` hors de sa définition dans
  `apps/core/functions/functions_setups.py`.
- **Reste** : `apps/edi/bin/chrono_direct.py` (2 connexions `psycopg2.connect`, script hors
  requête HTTP) et le module utilitaire `apps/core/functions/functions_postgresql.py`
  (`cnx_postgresql`, `psycopg2.connect`). Règle : psycopg2 direct accepté uniquement pour `COPY`
  et les traitements lancés hors Django (cron, scripts), avec commentaire ; sinon
  `django.db.connection`.
- **Critères d'acceptation** : usages restants listés et commentés, `CNX_STRING` et
  `cnx_postgresql` supprimés si plus rien ne les appelle.

---

## D11 — Hygiène de code `[x]`

Petites corrections à passer app par app, en même temps que D0 :

- imports en double (ex. `redirect`, `reverse` importés deux fois dans
  `apps/articles/views/views_article_accounts.py`) ;
- mutation de classe au niveau module (`form_class.use_required_attribute = False`) → attribut
  défini dans la classe de formulaire ;
- `HttpResponse(response)` autour d'un `JsonResponse` (2 restants, dont `apps/users/views.py`) →
  retourner le `JsonResponse` ;
- templates orphelins référençant des routes supprimées
  (`articles_account_vat_list_entete.html`) ;
- en-têtes `# pylint: disable=...` globaux → cibler les lignes concernées ou supprimer ;
- `apps/parameters/tests/test_counters_parameters.py` cassé : réécrire selon D0 ou supprimer.
- **Réalisé le 2026-10-11** : 147 imports inutilisés et 12 redéfinitions retirés du code applicatif
  (ruff F401/F811/F841/F821, hors tests et migrations) ; 70 `form_class.use_required_attribute = False`
  déplacés des vues vers l'attribut de classe des 24 formulaires concernés ; `HttpResponse(JsonResponse)`
  éliminé de `users/views.py` ; 31 templates orphelins supprimés (jamais rendus ni inclus, dont
  `articles_account_vat_list`, `acuitis_axe_*`, `cosium_axe_*`, `invoices_suppliers*`), 3 lignes
  commentées pointant des routes mortes retirées, route inexistante corrigée dans
  `validation_sales/sage_controls_entete.html` (-> `sage_controls_globals_sales`) ; plus aucun
  `{% url %}` vers une route absente ; 392 en-têtes `# pylint: disable` remplacés par une section
  `[tool.pylint]` du pyproject (codes universellement désactivés) ; `functions_celery.py` : requête
  au niveau module sur un nom indéfini (NameError à l'import) supprimée ; `functions_sql` :
  paramètre `sql` masquant le module renommé ; `data_flux/validation` : import pydantic
  `ValidationError` masqué par l'exception locale retiré ; filtres de template homonymes renommés ;
  stub vide `validation_sales/bin/control_rebilling.py` supprimé ; `test_counters_parameters.py`
  réécrit (24 cas paramétrés, fabriques) et `apps/parameters/tests` ajouté aux chemins de tests.
- **Imports Django (2026-10-11)** : `reverse` et `HttpResponse` ne sont plus importés depuis
  `django.shortcuts` (effet de bord, hors API publique, signalé par PyCharm) mais depuis
  `django.urls` et `django.http` : 69 fichiers, aucun test modifié.

---

## D12 — Tests de `apps/book` `[x]`

- **Appliquer D0** sur le répertoire des tiers (Sage BPR/BPS/BPC, adresses, contacts, banques,
  identifiants cct par fournisseur, familles statistiques / axes).
- **Réalisé le 2026-10-11** : 214 tests (15 fichiers), book à 100 % lignes + branches, projet
  1 887 tests à 100 % en ~66 s. `apps/book/tests/conftest.py` : `book_dirs` (répertoire de
  processing du module d'import redirigé), `sage_file`, `fake_make_insert`, `make_stat_familly`,
  `make_payment_condition`, `make_contact`, `make_society_bank`, `automate`. 6 tests d'intégration
  (chaîne data_flux réelle) sur BPR, BPS, BPC, adresses, codes contacts, banques.
  Code mort supprimé : `apps/book/__init__.py` (323 lignes de POST collées), `tests/essais/modifs.py`,
  `sql_files/sql_supplier_cct.sql` (vide, jamais lu).
  Bugs corrigés : `SupplierCct.get_absolute_url` et le retour de `export_list_supplier_cct`
  (NoReverseMatch, la route exige `in_use`) ; écran des identifiants qui plantait (NoReverseMatch
  du gabarit) quand le chargement échouait ; `FamillyAxeCreate` sur statistique inconnue
  (AttributeError -> 404) ; export pré-généré inconnu (TypeError -> 404) ; identifiant cct inconnu
  en changement unitaire (DoesNotExist -> 404) ; tiers inconnu à l'export des identifiants ;
  `check_cct_identifier` comparait `None` avant à `"None"` après (`split_identifiers` commun) ;
  `bp_book_pre_processing` plantait sur un tiers absent du référentiel (ligne ignorée, comme les
  autres pré-traitements) ; `DeleteSupplierFamilyAxesForm` sans champ validait n'importe quel id ;
  gardes ajax `and` -> `or` (2 vues) ; `Contact.__str__` affichait « NoneDurand » ; nom du fichier
  d'export des emails en erreur (copié des RFA) ; script `migrate_ga000_to_lab0001` robuste aux
  identifiants vides et aux tiers sans LAB0001.
  Second passage (2026-10-11, « traite les points de bug ») : import des contacts CRM (ZBICONTCRM)
  routé dans `processing_dict` après les codes contacts, clé d'upsert `{"society", "code"}` conforme
  au `unique_together` du modèle Contact, colonne `code` ajoutée en position 1 du mapping (les autres
  colonnes décalées d'un rang : **hypothèse à valider sur une vraie extraction, aucun exemplaire du
  fichier sur le poste**) ; les trois modules `checks.py`, `book_post_processing.py` et
  `excel_generations.py` n'amorcent plus Django par un chemin codé en dur mais par
  `apps.core.functions.functions_setups` (convention du projet, exécution `python -m`) ;
  `check_emails_to_send` testé sur une vraie facture de vente : fabriques `make_centers_invoices`,
  `make_signboards_invoices`, `make_parties_invoices`, `make_sale_invoice` déplacées telles quelles du
  conftest invoices vers le conftest racine (invoices : 330 tests inchangés). book : 206 tests ;
  projet 1 879 tests à 100 %.
  Restent (choix fonctionnels, non modifiés) : `unit_weight` obligatoire dans le formulaire des
  définitions (modèle `null=True` sans `blank=True`) ; `supplier_cct_identifier` et
  `change_supplier_cct_unit` au-dessus du seuil de complexité cognitive (couvertes, découpage
  possible sans toucher aux tests).

---

## D13 — Tests de `apps/centers_purchasing` `[x]`

- **Appliquer D0** sur la centrale d'achat (centrales mères / filles, enseignes et logos, types de
  facture, regroupements de facturation, dictionnaires axe pro / regroupement et axe pro / tva,
  comptes achat vente par centrale / catégorie / rubrique / axe pro / tva et leur import).
- **Réalisé le 2026-10-11** : 117 tests (8 fichiers), app à 100 % lignes + branches, projet
  1 996 tests à 100 % en ~73 s. Fabriques `make_article_account` et `make_accounts_axe_pro_category`
  déplacées telles quelles du conftest articles vers le conftest racine ; conftest de l'app :
  centrales mères, regroupements, dictionnaires, types de facture, `media_dirs` (media, static,
  IMPORT_ACCOUNTS redirigés), `logo_file` (png Pillow), `star_client`.
  Code mort supprimé : `output_excel_acuitis_axe_list.py` et `output_excel_cosium_axe_list.py`
  (import de modèles inexistants, jamais importés) ; `get_absolute_url` de SignboardModel,
  Translation, SignboardModelTranslate, TranslationParamaters (routes inexistantes, modèles sans
  écran) ; constante `proccessing_dir` inutile de `imports_data`.
  Bugs corrigés : bouton IMPORT des comptes (chemin d'un fichier de 2023 codé en dur, et traduction
  attendant 7 colonnes alors que l'export en produit 14 depuis toujours) -> les classeurs déposés
  dans `settings.IMPORT_ACCOUNTS` sont importés au format de l'export, sans ligne d'entête parasite ;
  l'import d'un compte à rubrique nulle créait un doublon (clé unique SQL inopérante sur NULL) que
  la purge de l'écran supprimait en gardant l'ancien -> la purge garde désormais le plus récent et
  suit immédiatement l'import ; formulaire des comptes : la modification d'une ligne se voyait
  elle-même en doublon (`exclude(pk=self.instance.pk)`) ; liste des comptes : code centrale tronqué
  à 2 caractères par un LPad (« AC - Acuitis ») ; `axe_pro_vat_export_list` se redirigeait sur
  lui-même en cas d'erreur (boucle) ; fixtures des enseignes : champ `language` inexistant sur
  Signboard (TypeError) ; 5 formulaires de suppression sans champ validaient n'importe quel id ;
  gardes ajax `and` -> `or` (5 vues) ; IBAN enregistré avec un espace final ; template des
  centrales filles sur `form.code_swift` au lieu de `form.swift_code` (champ jamais affiché) ;
  libellé de log `axe_grouping_delete` dans la suppression des comptes ; amorçage Django codé en
  dur dans `data_pre_processing_pool.py` et `update_account_article.py` -> `functions_setups`.
  À arbitrer (non modifié) : `AccountAxeList.__init__` purge les doublons à chaque instanciation
  de la vue ; `SignboardForm.img_delete` est un widget posé en attribut de classe (sans effet, la
  case à cocher est écrite dans le gabarit) ; `AxeProGroupingGoods.grouping_goods` nullable en base
  mais obligatoire dans le formulaire.

---

## D14 — Tests de `apps/core` `[x]`

- **Appliquer D0** sur le socle commun (traces de changement, notifications, progression SSE,
  API des listes déroulantes, exports et conversions Excel, imports de fichiers, utilitaires
  dates / SQL / PostgreSQL / chaînes, validateurs Pydantic et formulaires, emails, journaux,
  commande check_celery).
- **Réalisé le 2026-10-11** : core passe de 34 % à 100 % lignes + branches ; projet 2 374 tests à
  100 % en ~73 s. Travail en 4 lots parallèles (bases `TEST_DB_NAME` distinctes), fichiers
  `apps/core/tests/test_lot<n>_*.py` (16 fichiers, 233 tests ajoutés aux 11 fichiers existants).
  Nettoyage préalable : core passe de 12 008 à ~6 300 lignes. 21 fichiers jamais importés
  supprimés (utilitaires mail et FTP, mail_alertes, functions_celery, celery_examples,
  celery_monitoring non routé, forms_explanation, excel_writer en doublon, mini_form_html,
  assembly_formset, validate_file, nbre_lignes_heron, import_model_file, insert_adnims,
  imports_prod_vers_dev, brouillons essais / edi_parsing vides, `exports/__init_.py`, loggers
  postgres dédié qui reconfigurait la journalisation à l'import) ; vue de test `pdf_test` et son
  gabarit retirés ; 126 fonctions sans aucun usage élaguées (dates 51, sql 15, utilitaires 17,
  validateurs pydantic 12, validations 8, postgresql 6, ...) puis `functions_postgresql` ramené de
  842 à 153 lignes (pool, copy_from, upsert maison jamais appelés).
  Bugs corrigés : `validate_date` au retour inatteignable ; `clean_id(None)` (TypeError) ;
  `NullBooleanField` DRF (TypeError non intercepté -> 500) ; `NullZeroDecimalField` et
  `TvaInterson` / `TvaWidex` aux branches inatteignables ; `ChangeTraceMixin` avec `mark_delete`
  posait un objet User hors champ dans la trace (JSON impossible -> 500) ; `excel_xhtml_to_csv`
  écrivait un caractère par colonne ; `GenericExcel.write_rows` sans style ou avec une liste de
  styles trop courte ; `IterFileToInsert` à une seule colonne découpait la valeur caractère par
  caractère ; `ModelFormInsertion` ne mettait jamais à jour sur clé unique ; message de log de
  `query_dict`.
  Second passage (« corrige les bugs ») : `get_active_jobs` trie les jobs en cours (démarrage le
  plus récent d'abord) puis les jobs en attente ; `functions_http.get_limit` remplace `int(GET)`
  dans `get_user_jobs` et `notifications_list` (valeur absente, non numérique ou non positive ->
  défaut 50, plus de 500) ; `IterFileToInsert` complète par des champs vides les lignes vides
  (`all_lines`) ou courtes au lieu de lever IndexError (`_padded`, `_is_excluded`). Tests de preuve :
  `apps/core/tests/test_bugs_limites_et_lignes_vides.py` ; un test du lot 3 qui figeait l'ancien tri
  mis à jour. Projet 2 386 tests, 100 %.
  Reste volontairement : branches `except ExcelToCsvError` de `functions_excel` mortes en pratique
  (couvertes par doublure, propagation conservée car `articles` compte dessus).

---

## D15 — Tests de `apps/countries` `[x]`

- **Appliquer D0** sur les pays (modèles pays / langues / devises / taux de change / règles de
  validation, import Sage ZBICRY et sa boucle, fixtures de pays).
- **Réalisé le 2026-10-11** : 42 tests (2 fichiers), app à 100 % lignes + branches ; projet
  2 428 tests à 100 % en ~74 s.
  Bugs corrigés : `Country.file_import_sage()` renvoyait `ZBIADDR_journalier.heron` (fichier des
  adresses des tiers) au lieu de `ZBICRY_journalier.heron` utilisé par la boucle ; `fixtures_pays`
  ne pouvait pas fonctionner (10 clés dont `country` en double pour 8 colonnes : le nom du pays
  allait dans la clé de 3 caractères, le nom de la devise dans un entier) -> mapping aligné sur le
  fichier (nom, code, sigle et nom et code de devise, indicatif, cee ; le rang de devise, sans
  champ, est ignoré), `get_or_create` sur le code : un pays déjà présent n'est pas modifié, la
  première ligne d'un code répété (US, GB) est conservée.

---

## D16 — Tests de `apps/data_flux` `[x]`

- **Appliquer D0** sur le socle des imports (chargeur de fichiers csv / excel, chargeur et parseur
  EDI OPTO 33, validation par formulaire Django / sérialiseur DRF / schéma Pydantic avec traces,
  upsert PostgreSQL par table temporaire, fonction `make_insert`, traces, vue d'import).
- **Réalisé le 2026-10-11** : data_flux passe de 45 % à 100 % lignes + branches ; projet 2 576
  tests à 100 % en ~76 s. Travail en 3 lots parallèles (bases `TEST_DB_NAME` distinctes),
  fichiers `apps/data_flux/tests/test_lot_<a|b|c>_*.py` (8 fichiers, 147 tests).
  Nettoyage préalable : registre de cache Redis jamais utilisé (`cache.py`), chargeurs d'API json
  et xml inachevés (TODO, jamais appelés), ancien module `test_loaders.py` entièrement commenté et
  ses constantes `test_fixtures/`, exceptions sans usage (`PathUnzipError`, `OptoMontError`).
  Bugs corrigés : chargeur de fichiers (`params_dict` absent -> AttributeError ; `load("data_list")`
  appelait `read` ; une seule colonne demandée découpée caractère par caractère ; fichier vide ->
  StopIteration brute ; exclusion sur une colonne absente -> IndexError) ; chargeur OPTO 33 (champs
  ajoutés à la volée sortaient toujours « None » ; source non Path -> AttributeError) ;
  `make_insert` (`add_fields_dict` absent, `trace.comment` None) ; upsert PostgreSQL (erreur
  d'`execute_batch` jamais signalée, DEALLOCATE qui masquait l'erreur d'origine, `kwargs_prepared`
  None, `table` référencée avant définition dans les gestionnaires d'exception, mode
  `pre_validation` inutilisable, mode inconnu -> TypeError) ; validation (messages bruts passés au
  formateur d'erreurs, validations Django et DRF inutilisables : instanciation `validator(**data)`,
  `Config.include` inexistant, `errors` au lieu de l'objet ; `ValidationError` Pydantic sans
  `errors()` ; `get_validation_instance` : `len(None)` et contrôle de type sans effet ; champ
  `passed_numbers_records` inexistant sur Trace).
  Constaté, non modifié : une instance d'`Opto33Loader` ne se lit qu'une fois (flux parsé en
  générateur, la chaîne d'import ne fait qu'un `read_dict`) ; les contrôles du nombre de factures
  et de lignes du parseur OPTO sont désactivés par commentaires (fournisseurs non conformes) ;
  `FileLoader` compte `first_line` en lignes physiques (retour à la ligne dans une cellule quotée
  d'entête). Comparaisons réordonnées par `ruff --fix` (SIM300) dans 13 tests d'autres apps, sans
  changement de sens.

---

## D20 — Tests de `apps/od` `[x]`

- **Appliquer D0** sur les OD à passer (import csv, validations montants / comptes / axes / cct /
  tiers, numérotation Sage, export X3 sur le journal ODINV). App sans vue ni route : outil lancé
  en script.
- **Réalisé le 2026-10-11** : 29 tests (1 fichier, 9 d'intégration data_flux et SQL réel), app à
  100 % lignes + branches ; projet 2 668 tests à 100 %.
  Bugs corrigés : `update_blank_facture_heron` n'était jamais appelée, une OD sans facture Héron
  gardait NULL, ne recevait pas de numéro Sage (`where facture_heron = NULL`) et sortait de l'export
  avec un numéro de pièce nul -> appelée avant la numérotation ; messages « est pas déséquilibrée »
  et parenthèse parasite dans le détail des axes. `sql_files/essai_sql.sql` (copie d'essai) supprimé.
  Branches toujours vraies simplifiées (`queryset.exists()` après un jeu d'identifiants non vide,
  `if not file.closed`).
  Constaté : l'indicateur d'entête des fichiers ODINV est « G » (comme l'export odana d'invoices).

---

## D21 — Tests de `apps/parameters` `[x]`

- **Appliquer D0** sur le paramétrage (catégories / rubriques, axes par défaut, fonctions de
  facturation, numérotations, natures, emails types, taux de change, contrôles de refacturation).
- **Réalisé le 2026-10-11** : 99 tests (conftest + 4 fichiers : config/modèles/formulaires/
  fixtures/excel, bin, vues, compteurs existants), app à 100 % lignes + branches ; suite complète
  relancée sur base dédiée `test_heron_params` (une autre suite tournait sur la base par défaut),
  projet 2 743 tests à 100 %.
  Bugs corrigés : suppression d'une numérotation toujours refusée (`CounterNums` en FK PROTECT,
  journalisée « inexistante ») -> compteur courant supprimé avec elle ; `ExchangeUpdate`/
  `ExchangeCreate` : `rate_month` et `curency_base` repris du POST et écrasés à `None`
  (`set_exchanges_sales_cosium` avec `sale_month = 'None'`) -> champs `disabled` dans
  `ExchangeRateForm`, attributs posés après validation, get-or-create dans `ExchangesList` ;
  `set_base_exchange_rate` ne créait jamais le taux par défaut d'un mois dès qu'une devise avait un
  taux sur un autre mois (Exists sans `rate_month`) ; `SubCategoryCreate` sur catégorie inconnue ->
  404 au lieu d'AttributeError ; gardes ajax `and` -> `or` (5 vues) ; formulaires de suppression
  `fields=("id",)` sans champ réel -> `ModelChoiceField` ; export des axes par défaut redirigeait
  vers `book:societies_list` ; `Nature.__str__` renvoyait `None` sans `to_display` ;
  `Counter.clean` plantait sur `lpad_num` nul ; orientation « landscapa » ; log
  « delete_invoice_purchase » dans `delete_sub_category`.
  Code mort supprimé : `BaseAdressesTable`, `get_folder_num`, `parameters/counters_parameters.py`,
  branche `except ActionInProgress.DoesNotExist` inatteignable, copie du `get_queryset` de ListView.

---

## D22 — Tests de `apps/periods`, `apps/permissions`, `apps/traces` `[x]`

- **Appliquer D0** sur les trois petites apps (formulaire de période mois, squelette permissions,
  écran paginé des traces EDI et son export Excel).
- **Réalisé le 2026-10-12** : 16 tests (periods 9, permissions 1, traces 6), les trois apps à
  100 % lignes + branches ; projet 2 755 tests à 100 % (2 899 avec D23-D25).
  Bugs corrigés : `traces` export plantait sur une trace sans commentaire (`html2text(None)`) ;
  `permissions` configuration `PermitionsConfig` -> `PermissionsConfig`.
  `periods` : `YearForm` était un ModelForm sans modèle (inutilisable) qui reprenait les choix de
  mois -> réécrit à la demande de l'utilisateur en `forms.Form` sur `get_year_choices()` (Y-10..Y+10,
  initial = année en cours, valeur = année sur 4 chiffres), prêt à l'emploi comme `MonthForm`.
  `get_year_passed_choices` (années facturées) plantait sans facture (`[0]` sur liste vide) ->
  `aggregate(Min)` avec repli sur l'année en cours, et nouveau `YearPassedForm` associé.
  Code mort supprimé : docstring dédoublée de `excel_edi_traces`.
  Conservé : modèle `Periode` + `fixtures_periodes` (csv de 737 périodes, testé), stub `permissions`.

---

## D23 — Tests de `apps/validation_sales` `[x]`

- **Appliquer D0** sur les écrans de contrôle des ventes (16 routes, 15 écrans encore statiques,
  un export réel : ventes Héron non finalisées via `sql_files/sales_not_final.sql`).
- **Réalisé le 2026-10-12** : 22 tests, app à 100 % lignes + branches ; projet 2 777 tests à 100 %.
  Bugs corrigés : configuration nommée `TracesConfig` (copie) -> `ValidationSalesConfig`.
  Code mort supprimé : `views/views_etape_2_1.py` (vide) et `views_etape_2_3.py` (fonction sans
  corps, jamais importée).
  Fabrique `make_sale_invoice_detail` déplacée du conftest d'invoices vers le conftest racine
  (validation_purchases garde la sienne dans `helpers_excel_2`).
  Constaté, non modifié : les écrans « Export Excel » et de détails (`'AF001'` codé en dur) sont
  des gabarits statiques sans menu actif (liens commentés dans `menu_principal.html`).

---

## D24 — Tests de `apps/rfa` `[x]`

- **Appliquer D0** sur les RFA (6 écrans CRUD d'exclusions / taux / sections, exports Excel,
  contrôles préalables, génération par tâche celery et SQL d'insertion).
- **Réalisé le 2026-10-12** (fork dédié) : 72 tests (conftest + 3 fichiers), app à 100 % lignes
  + branches (892 lignes, 60 branches).
  Bugs corrigés : `models.py` `limit_choices_to={'type_x3': (1, 2)}` (tuple sur FK, aucune maison
  proposée à l'exclusion client) -> `type_x3__in` (migration `0007_alter_clientexclusion_cct.py`
  générée, répertoire `migrations/` non suivi par git) ; `rfa_controls.have_rfa_to_be_invoiced`
  jointures `<> exclusion` (produit cartésien : aucun fournisseur si une table d'exclusion vide,
  exclusions inopérantes) -> `exists`/`not exists` identiques à `SQL_RFA_INSERTION`, + exclusion
  client/fournisseur manquante, RFA déjà générées par fournisseur ; `rfa_views.py` résultat de
  `redirect_validation()` ignoré et contrôles non joués au POST (génération possible malgré les
  contrôles) ; export clients/fournisseurs `.values("cct__cct")` sur un champ `maison`
  (`FieldError`, export toujours KO) ; `AxeRfaForm` ModelForm sur SectionSage avec `initial=(x, x)`
  -> `forms.Form` initialisé sur la période en cours ; 6 gardes ajax `and` -> `or` ; 6 formulaires
  de suppression sans champ réel ; `TracesConfig` -> `RfaConfig` ; `rfa_loop_pool` `finally` sur
  action nulle ; gabarit `parameter.code` -> `parameter.signboard.code` ; `rfa_post_upadte` renommé.
  Code mort supprimé : `rfa_controls.get_rfa()` (essai WIDE001), 12 `form_invalid` doublons du
  mixin, gardes `trace is not None` toujours vraies dans `tasks.py`.
  Traités ensuite à la demande de l'utilisateur (2026-10-12, 73 tests) : sans `EdiValidation`
  ouverte, `get_sql_kwargs` lève `RfaPeriodError` (message explicite écrit dans la trace et
  renvoyé à l'écran par la tâche, au lieu d'un `AttributeError` masqué « consulter les logs »), et
  la vue refuse le lancement (`get_open_period()`) ; `supplier_ident` vide au lieu de « None » si
  l'identifiant de centrale n'est pas renseigné ; amorçage Django à l'import de `rfa_loop_pool`
  (`BASE_DIR` par nom de machine, `django.setup()`) supprimé : le module n'est importé que par la
  vue, jamais lancé en script ; bloc `__main__` d'essai (WIDE001) de `rfa_insertions` supprimé.

---

## D25 — Tests de `apps/users` `[x]`

- **Appliquer D0** sur les utilisateurs (connexion, profil, groupes, intégrations en masse des
  staffs et utilisateurs par fichiers).
- **Réalisé le 2026-10-12** (fork dédié) : 48 tests (conftest + 3 fichiers), app à 100 % lignes
  + branches (643 instructions, 130 branches) ; projet 2 897 tests à 100 %.
  Bugs corrigés : `update_user_groupes` `User.objects.get_object_or_404` (500 systématique) ;
  `modification_groupes` `Group.objects.get(pk__in=chaîne)` et `except UsersError` jamais levé ;
  `profil_view` écrivait `user.fonction` (champ `function`, jamais enregistré) ; redirections vers
  la route inexistante `dashboard` -> `home` ; `InsertStaffs` enregistrait les csv staff en
  `type_insert=0` (mélange des deux intégrations), téléversement sans fichier -> message ;
  `_create_registered_user` sans `code_child_center` ; intégrations en masse inutilisables
  (`chunk_file` inexistant, `create_user(fonction=)`, `str(uuid.uuid4)` sans parenthèses,
  `make_csv()[0]` passé en chemin) ; serializer sur `"fonction"` ; `UserRegisterForm` SQL sur la
  table inexistante `auth_group_name` -> ORM, `validate_password(None)` ;
  `AuthGroupAccessStaff.__str__` renvoyait un objet.
  Code mort supprimé : `backend.py` (hors AUTHENTICATION_BACKENDS), `change_user_password` +
  `all_users_choices` + `ChangePasswordForm` + `change_pass_form.html` (route commentée),
  `User.save` sans effet, `UserManager.num`, `except IntegrityError` inatteignable.
  Traité ensuite à la demande de l'utilisateur (2026-10-12) : `check_next_page` (core) s'appuie
  sur `url_has_allowed_host_and_scheme` (urls relatives internes acceptées, donc le `?next=` de
  `login_required` est suivi ; domaine étranger, `//hôte`, `javascript:` ramenés à `/`) et
  `register_view` passe son `next` par le même contrôle (plus de redirection ouverte) ; le test
  core qui figeait le refus des urls relatives a été mis à jour.
  Non modifié (arbitrage) : `User.__str__` à double espace ;
  validateur antivirus de `UploadStaffsForm` dépendant de `DEBUG` à l'import ;
  `*_integrations` renvoient toujours `od: False`.
- **Bilan D12-D25** : toutes les apps de `apps/` sont couvertes à 100 % lignes + branches
  (2 897 tests, `uv run pytest --cov`).
  Les répertoires `apps/clients_invoices`, `clients_validations`, `suppliers_invoices`,
  `suppliers_validations` (vides, hors INSTALLED_APPS) et le squelette `apps/permissions` sont
  **réservés à des développements futurs** : à conserver (consigne du 2026-10-12).

---

## D26 — Tests du paquet `heron` (projet) `[x]`

- **Appliquer D0** au paquet projet : vues racine, middleware de connexion, processeurs de contexte,
  filtres de gabarits, tables abstraites, loggers, celery, utilitaires de répertoires, commande
  `init_directories`, points d'entrée ASGI / WSGI, URLconf. Hors mesure (`omit`) : `heron/settings/*`
  (configuration par machine), `heron/bin/*` et `heron/env/*` (scripts de poste à effets de bord),
  migrations.
- **Réalisé le 2026-10-12** : 62 tests (`heron/tests/`, 4 fichiers), paquet à 100 % lignes +
  branches (couverture initiale 60 %) ; `heron` ajouté au `source` coverage et `heron/tests` aux
  `testpaths`.
  Bugs corrigés : `numbers_format` plantait (`ValueError` au dépaquetage) sur un entier ou un texte
  sans partie décimale ; `groupes_processor` créait à chaque requête des gabarits vides
  `templates/heron/<groupe>.html` dans l'arborescence source (jamais inclus) -> supprimé ;
  `init_directories` testait `hasattr(settings, "STATICFILES_DIRS")` (toujours vrai).
  Code mort supprimé : `heron/views.py` (module masqué par le paquet `heron/views/`, copie
  intégrale), `home()` dupliqué dans `users_views`, `heron/forms.py` (`DateInputDate`) et son
  gabarit `date_input_form.html`, `heron/secure_files.py` (jamais routé), `safe_open` /
  `safe_write_text` / `safe_write_bytes` (sans usage), 23 filtres de gabarit qu'aucun gabarit
  n'utilise (`left_trunc`, `right_align`, `right_trunc`, `bool_and`, `bool_in`, `get_bool_value`,
  `get_background_date_lt`, `replace_space_splash`, `html_to_text`, `strip_value`, `get_dict_keys`,
  `numbers_point`, `rangex`, `format`, `encode_b64_list`, `due_dates`, `string_agg`,
  `string_agg_uniques`, `addition`, `get_third_party`, `get_account`, `get_in_child_center`,
  `right_align_`) ; filtres numériques factorisés (`_split_number`, `_group_thousands`).
  Gabarits exercés par les tests : accueil, déconnexion par email, réactivation (valide / invalide),
  parcours complet de réinitialisation de mot de passe (4 écrans + email texte), menus via les vues
  des apps. Non modifié : `print()` de `heron/settings/__init__.py` (sélection des réglages par
  machine), `DbTableAuthorisation` (table sans usage, conservée).
- **Complément du 2026-10-12** : `apps/invoices/bin/conf.py` supprimé (amorçage `django.setup()` à
  l'import, `BASE_DIR` par nom de machine, `DOMAIN` homonyme du domaine d'emails ; en local hors
  `MSI` il pointait sur le serveur de production). Remplacé par le réglage `PDF_STATIC_DOMAIN`
  (`heron/settings/base.py`, défaut `http://127.0.0.1:3000` ; `production.py` : `http://10.9.2.109`
  ou `:8080` pour l'instance formation ; surchargeable dans `.env`, documenté dans `env/env.txt`),
  lu à l'appel par les dix générateurs PDF (`"domain": settings.PDF_STATIC_DOMAIN`). Tests invoices
  adaptés (fixture `pdf_domain` pose le réglage, test de rechargement de `conf` remplacé).

---

## D27 — Sonar PyCharm, lot du 2026-10-12 `[x]`

- **Source** : capture du plugin SonarQube (8 nouvelles alertes sur 4 fichiers, 153 anciennes sur
  86 fichiers dont une vingtaine visibles).
- **Nouvelles alertes, traitées** : `production.py` S1313/S5332 (IP et http codés dans le défaut
  de `PDF_STATIC_DOMAIN`) -> plus de défaut en production, la variable est **obligatoire dans le
  `.env` du serveur** (`PDF_STATIC_DOMAIN=http://10.9.2.109`, `:8080` pour l'instance formation),
  sinon `UndefinedValueError` au démarrage ; `rfa_views.rfa_generation` S3776 (17) -> découpée en
  `_have_new_articles`, `_set_message`, `_launch_generation` ; S5778 (plusieurs invocations dans un
  `pytest.raises`) dans `test_app_models_forms.py` (2) et `test_periods.py` (1).
- **Anciennes alertes visibles, traitées** : `check_celery.handle` S3776 (16) -> `_wait_until_idle`,
  `_write_status`, `_write_details` ; `accountancy/validations/djantic_sage.py` (module d'essai :
  `main()`, `essai_SectionSagechema`, bloc `__main__` sur un chemin Windows, 52 lignes commentées)
  supprimé avec son test ; `emails.prepare_mail` S1172 : le paramètre `email_text` est désormais
  utilisé (partie texte fournie par l'appelant, formatée avec le contexte, repli sur le texte
  extraite du html) ; S125 : `# sql_maison` (edi_post_processing_pool), `# ...`
  (essais_import_sage) et **101 lignes `# print(...)` / `# LOGGER_EXPORT_EXCEL.exception(mogrify)`**
  supprimées dans 33 modules (exports Excel de validation_purchases et autres).
- **Reste** : `ruff --select ERA001` signale encore 279 commentaires « code » (dont beaucoup de faux
  positifs : dictionnaires de colonnes commentés dans `function_imports`, `familles_stat_fixtures`,
  `opto_33_parser`) ; fonctions de complexité > 15 restantes (script
  `uv run --with cognitive-complexity`) : `book/views/identifiers_views.supplier_cct_identifier` (21),
  `core/functions/functions_excel.make_csv` (34), `core/validations/pydantic_validators_base.input_format_date`
  (16), `data_flux/make_inserts.make_insert` (16), `data_flux/opto_33_parser.line_parser` (34),
  `heron/management/commands/init_directories.handle` (25). À traiter sur la liste Sonar complète.

---

## D28 — Sonar PyCharm, lot du 2026-10-12 (anciennes alertes, 2e capture) `[x]`

- **Source** : capture « 123 older issues in 64 files », partie visible (fichiers a..i) : 30 alertes
  dans 20 fichiers.
- **Traité** : S1481 variables `test_a` / `to_print` inutilisées -> `_` (`export_od_inv`,
  `export_x3_odana_invoices`, `countries/loops/imports_loop`) ; S112 exceptions génériques ->
  `ExportX3Error` (`invoices/bin/export_x3`) et `FileNotFoundError` (`functions_postgresql`) ;
  S1542/S117 nommage -> `generate_exports_x3` (le nom de route `invoices:generate_exports_X3` est
  conservé), variable locale `supplier_cct_formset` ; S125 code commenté retiré
  (`familles_stat_fixtures`, `core/bin/import_files`, `import_ventes_cosium`, bloc `'''` de 30
  lignes de code mort en fin de `function_imports`) ; S108 bloc `if POST: pass` de
  `files_import_views` ; S7500/S8519 compréhensions et `list(...)[0]` -> `list(...)` /
  `next(iter(...))` (`users/forms`, `function_imports`, `functions_excel`) ; S5799 chaînes
  concaténées implicitement (`functions_excel`) ; S4790 `hashlib.md5(..., usedforsecurity=False)`
  (clé de cache, `functions_excel_optimized`) ; S7498 `dict()` -> `{}` ; S7512 boucle sur le
  dictionnaire ; S8786 expression régulière de `separate_edi` sans retour arrière
  (`UNA.{6}\n?` : le segment UNA est de longueur fixe, 6 caractères de service après « UNA » ;
  l'ancien `(?=UNA:\+).*[\n|']` avalait toute la ligne jusqu'au dernier « ' », donc tous les
  segments d'un fichier EDI écrit sur une seule ligne) ; S3776 `functions_excel.make_csv` (34) -> `_csv_file_name` + `_convert_file`,
  `identifiers_views.supplier_cct_identifier` (21) -> `_apply_cct_identifiers`.
- **Volontairement non modifié** : cookie `download_complete_<token>` (S3330/S2092) : il est lu
  par le JavaScript de la page (donc pas `HttpOnly`) et l'application est servie en http interne
  (donc pas `secure`) ; il ne porte aucune donnée ; commentaire ajouté dans
  `functions_http_response.py`.
- **Reste** (non visible sur la capture, mesuré au script) : complexité > 15 pour
  `pydantic_validators_base.input_format_date` (16), `data_flux/make_inserts.make_insert` (16),
  `opto_33_parser.line_parser` (34), `heron/.../init_directories.handle` (25) ; ERA001 : 272.

---

## D29 — Sonar PyCharm, lot du 2026-10-12 (anciennes alertes, 3e capture, fichiers e..n) `[x]`

- **Traité** : S125 code commenté (`essais_import_sage`, `familles_stat_fixtures` : fonction
  commentée de 70 lignes, `invoice_reassignment_views` `# import pdb`, `imports_loop_pool` et
  `invoices_insertions` : blocs `__main__` de débogage avec email et date codés (S930 appel à
  `invoices_insertion` sans `job_id`), `articles/models`, `od/models`, `make_inserts`) ; S3776
  `init_directories.handle` (25) -> `_module_paths`, `_directories_to_create`, `_create` ;
  `make_inserts.make_insert` (16) -> choix du modèle des colonnes sans `if/else` ; S112
  `InvoicesInsertionError` (`invoices_insertions`) ; S1135 : les deux `TODO` d'`invoices_insertions`
  (pré-contrôle non joué, champs manquants non contrôlés) deviennent des commentaires « Limitation
  connue », reportés ci-dessous ; S5886/S5655 annotations fausses (`get_loader_params_dict -> dict`,
  `set_data(flow_name: str)`) ; S8519 `next(iter(...))` (`data_flux/loader`) ; S7519
  `dict.fromkeys` ; S1066 `if` fusionnés (`login_middleware`) ; S117 `user_model`
  (`notifications`) ; S1940 `!=` (`numberings_views`) ; S1313 adresses IP : `local.py` lit
  `LOCAL_HOSTS` du `.env` (`INTERNAL_IPS` et `DOMAINS_WHITELIST`), `production.py` construit
  `DOMAINS_WHITELIST` depuis `ALLOWED_HOSTS` + `DOMAINS_WHITELIST` du `.env` (hôtes avec port).
  **Bug corrigé au passage** : `production.DOMAINS_WHITELIST` contenait la liste `WHITELIST`
  imbriquée comme élément (jamais comparable, et `set()` impossible depuis D25). Variables
  ajoutées au `.env` local et documentées dans `env/env.txt` ; en production, sans
  `DOMAINS_WHITELIST` dans le `.env`, seuls les hôtes d'`ALLOWED_HOSTS` sont acceptés pour un
  `?next=` absolu (les `?next=` relatifs ne sont pas concernés).
- **Limitations connues (ex-TODO d'`invoices_insertions`)** : le pré-contrôle n'est pas joué dans
  `invoices_insertion` ; pas de contrôle des champs éventuellement manquants (TVA, régime, collectif).
- **Non modifié** : cookie `download_complete_<token>` (voir D28).
- **Reste** : complexité > 15 : `pydantic_validators_base.input_format_date` (16),
  `opto_33_parser.line_parser` (34).
- **Méthode** : l'IDE reformate les fichiers modifiés (guillemets doubles, listes multi-lignes) pendant
  le travail : relire le fichier juste avant chaque remplacement.

---

## D30 — Sonar PyCharm, lot du 2026-10-12 (anciennes alertes, 4e capture, fichiers f..o) `[x]`

- **Traité** : S7496 `set([...])` -> ensembles en compréhension (`od/imports/od_a_passer`, 4) ;
  `data_flux/opto_33_parser` : S125 (amorçage `sys.path` commenté, import commenté, bloc
  `__main__` de débogage sur un fichier de Téléchargements), S3776 `line_parser` (33) ->
  `_split_qualifier` + `_parse_article_element`, S5886 `cmd_nad` / `cmd_rff` renvoient `{}` au lieu
  de `""` quand il n'y a rien à extraire (comme `parse_qualifier`, trois assertions de tests
  adaptées), S6659 `text.startswith("UNA")`, S5713 `except (OptoLinesError, Exception)` ->
  `except Exception`, S5655 `extract_entries(lines: list)`. Dernière fonction au-dessus du seuil
  de complexité traitée aussi : `pydantic_validators_base.input_format_date` (16) -> boucle sur
  `DATE_FORMATS` ; **plus aucune fonction du projet au-dessus de 15**.
- **Non modifié** : cookie `download_complete_<token>` (voir D28).
- **Environnement** : `pyproject.toml` modifié par l'utilisateur le 2026-10-12 à 11:36
  (`requires-python = "==3.14"`, pytest-django 4.14, pylint-django 2.8) : `uv run` refuse désormais
  le venv 3.11 ; les vérifications de ce lot sont passées par `.venv/bin/python -m pytest`,
  `.venv/bin/ruff` et `uv run --no-project --python 3.11`.

---

## D31 — Environnement : retour à Python 3.11 et nouvelle configuration outillage `[x]`

- **Constat du 2026-10-12** : `pyproject.toml` passé par l'utilisateur à `requires-python ~=3.14`
  (+ pytest 9.1.1, pytest-django 4.14, pytest-cov 7.1, coverage 7.16, ruff 0.17 avec ~45 familles
  de règles, black 26, pylint 4.1, mypy 2.4 + plugin pydantic, bandit, pre-commit). `uv sync` a
  recréé le venv en 3.14 et échoué sur `python-calamine` ; vérifié : **Django 3.2.25 ne démarre
  pas sous Python 3.13+** (`django/http/request.py` importe `cgi`, module supprimé). Python 3.14
  impliquerait Django 5.2 LTS et le relèvement de 7 paquets sans roue 3.14 (calamine, psycopg2,
  lxml 6, pyyaml, pandas 2.3, pendulum 3, pydantic 1.10) : chantier D6 élargi, non lancé.
- **Décision de l'utilisateur** : retour à 3.11. `requires-python = ">=3.11"`, `target-version =
  "py311"`, `mypy python_version = "3.11"`, `uv python pin 3.11`, `uv sync` ; les nouvelles versions
  des outils de dev sont conservées. Suite complète : 2 963 tests, 100 % lignes + branches.
- **Effet de bord corrigé** : la règle isort (`I`) de la nouvelle configuration, appliquée par l'IDE,
  a réordonné `apps/accountancy/models/__init__.py` (`pieces` avant `sage`) -> import circulaire,
  Django ne démarrait plus hors pytest. `pieces.py` importe désormais `CodePlanSage` depuis
  `apps.accountancy.models.sage` (indépendant de l'ordre du `__init__`). Les autres `__init__`
  de paquets (views, forms) ont aussi été réordonnés : la suite passe, mais tout nouvel import
  intra-paquet doit viser le sous-module, pas le paquet.
- **Mesures avec la nouvelle configuration** : `ruff check apps heron conftest.py` : 40 395 alertes
  (S101 assert dans les tests 6 696, ANN001 5 837, D400/D415 4 133 chacune, ANN201 3 366, W291 2 624,
  PIE800 1 569, D205, D212, D103…) ; `mypy apps heron conftest.py` : le plugin `pydantic.mypy` de
  pydantic 1.9.0 ne sait pas lire la version « 2.4.0 » de mypy (plantage immédiat) ; sans le
  plugin : 501 erreurs dans 141 fichiers (no-any-return 104, assignment 75, union-attr 73,
  var-annotated 44, valid-type 40, arg-type 38 ; fichiers les plus touchés : api_gmail/config.py 28,
  invoices_insertions.py 17, core/bin/echeances.py 15, api_get_models.py 14). À arbitrer :
  périmètre des règles ruff (exclure S101/ANN/D des tests au minimum) et retrait du plugin pydantic
  tant que pydantic < 1.10.

---

## D32 — Pipeline qualité (`scripts/pre_check.py`, pre-commit, mypy, xenon) `[x]`

- **Constat du 2026-10-12** : `scripts/pre_check.py` et `.pre-commit-config.yaml` ajoutés par
  l'utilisateur depuis un autre projet (cibles `src tests`, inexistantes ici) ; `uv sync` cassé par
  un `[build-system] uv_build` (disposition `src/` attendue) ; `uv run ruff format .` et
  `uv run ruff check . --fix` déjà appliqués par l'utilisateur sur 661 fichiers (suite relancée :
  2 963 tests, 100 %, rien de cassé).
- **Fait** : `[tool.uv] package = false` (application, pas de paquet à construire) ; cibles du
  script et de pre-commit -> `apps heron conftest.py scripts`, mypy sans argument (cibles dans
  `[tool.mypy].files`) ; `ignore = ["E501", "D203", "D213"]` (règles incompatibles avec D211/D212,
  plus d'avertissement) ; `[tool.mypy]` : plugins pydantic (version de mypy illisible par pydantic
  1.9) et Django (`Query.get_select_mask` absent de Django 3.2, plantage interne) désactivés avec
  explication, `django-stubs==6.1.2` dans un groupe de dépendances `typing` non installé par
  défaut (sans plugin : 2 090 erreurs au lieu de 487, dont 1 332 `var-annotated` sur les champs de
  modèles) ; xenon : seuils `--max-absolute C --max-modules B --max-average A`, tests / migrations /
  essais exclus (les seuils B/A/A du script d'origine signalaient 160 modules, dont 60 fichiers de
  tests) ; les deux modules restés en rang C découpés : `core/bin/import_files.import_file_process`
  (`_call_hook`, `_translated_file`, `_cleanup_translated`, `_archive_source`, `_finish_trace`,
  messages inchangés) et `data_flux/make_inserts.make_insert` (`_insert_file`, familles
  d'exceptions regroupées, journal `<NomClasse> : ...` inchangé). Pipeline : `uv pip check` OK,
  mypy 487 erreurs (à traiter), ruff 36 039 alertes avec la configuration étendue (à arbitrer),
  xenon OK.
- **Blocs encore en rang C hors tests (radon, 16)** : `has_change`, `trace_mark_delete`,
  `PersonalizedDjangoJSONEncoder` (core), `generate_facturx_invoice`, `finalize_period`,
  `build_facturx_invoice`, `launch_celery_send_invoice_mails_gmail` (invoices), `Maison.clean`,
  `get_row` (book stats), `cmd_nad`, `PostgresDjangoUpsert.insertion`,
  `Validation.get_validation_instance` (data_flux), `imports_loop.process` (accountancy),
  `_write_sheet` (core) : sous le seuil retenu, à découper au fil de l'eau.
- **Périmètre ruff des tests (décision du 2026-10-12)** : `per-file-ignores` pour `conftest.py`,
  `apps/*/tests/*`, `heron/tests/*` : `S101`, `ANN`, `D`, puis `PLR2004`, `PLC0415`, `SLF001`,
  `PLR0913`, `PLR0917`, `EM101`, `TRY003` (règles de production sans objet dans les tests) ;
  bit exécutable retiré de 999 fichiers `.py` (`EXE002`, `manage.py` conservé). Résultat :
  36 039 -> 14 892 alertes au total, 274 dans les tests (ICN001 `datetime` -> `dt` 77, ERA001 75,
  DTZ001/DTZ011 29, FBT 36, RUF043 11, S108 `/tmp` 6, S106 6, S608 5…), à traiter ensuite.
- **Corrections mécaniques du code (2026-10-12)** : espaces en fin de ligne retirés partout, y
  compris dans les chaînes SQL et docstrings (`W291/W293 --unsafe-fixes`, 2 642) ; docstrings :
  point final ajouté aux résumés (`D400/D415`, ~5 000), ligne vide insérée après le résumé
  (script AST, 1 732 docstrings dans 485 fichiers, puis `D205 --unsafe-fixes`), `D212/D200/D209/
  D210` ; `D401` ignoré (mode impératif anglais, docstrings en français). Suite complète relancée :
  2 963 tests, 100 %. Total : 14 891 -> 5 657 alertes.

---

## D33 — Sonar PyCharm, lot du 2026-10-12 (anciennes alertes, 5e capture, fichiers p..v) `[x]`

- **Traité** : S125 code commenté (`postgres_save` prints, `edi/tasks` `post_vacuum`,
  `production.py` : options https commentées remplacées par un commentaire en prose) ; S1135 : les
  trois `TODO` (`postgres_save` validation des clés existantes, `set_hand_invoices` ligne créée
  malgré l'échec des fonctions suivantes, `validation` clés étrangères / unicité) deviennent des
  « Limitation connue » ; S5332 `processors.domain_site` prend le schéma de la requête
  (`request.scheme`), `domain_debug` lit `settings.DOMAIN_DEBUG` (défaut `PDF_STATIC_DOMAIN`) ;
  S3358 conditionnelles imbriquées des trois validateurs de troncature -> `_truncated(value,
  max_length)` ; S1172 `GmailSender.create_message` utilise `body_text` (partie texte fournie,
  repli sur le texte du html, comme `prepare_mail`) ; **S2077 corrigé pour de bon** :
  `add_news_cct_sage` interpolait `third_party_num` dans le SQL (`select '{third_party_num}'`),
  désormais paramètre `%(third_party_num)s` ; S2208 `transfert_receptions` importe le module
  d'amorçage explicitement ; S6559 `fields = "__all__"` : `validation_by_serializers.py` (module
  d'essai, `DjangoForm` « test », `main()`) supprimé avec ses 2 tests, `EdiImportAllForm` (sans
  usage applicatif) supprimé avec son assertion de test ; S3752 `trace_edi_list` décorée
  `require_http_methods(["GET"])`.
- Tests touchés (changement de comportement ou code supprimé) : `heron/tests/test_processors.py`
  (`domain_site` reçoit une requête), `apps/edi/tests/test_validations.py`,
  `apps/validation_purchases/tests/test_forms.py`.

---

## D34 — Fin de téléchargement des exports sans cookie (S3330 / S2092) `[x]`

- **Constat** : dernière alerte Sonar restante : le cookie `download_complete_<jeton>` posé par
  `response_file` pour que le JavaScript des écrans « ventes / achats à finaliser » arrête
  l'indicateur de téléchargement ne pouvait être ni `HttpOnly` (lu par le JavaScript) ni `secure`
  (http interne).
- **Fait le 2026-10-12** : plus de cookie. `response_file(..., download_token=, session=)` pose
  un marqueur `download_complete_<jeton>` dans la session (stockée en base, donc partagée entre les
  processus gunicorn, contrairement au cache locmem) ; nouvelle vue `core:download_status/<jeton>/`
  (`GET` seulement) qui renvoie `{"complete": bool}` et consomme le marqueur ; les deux gabarits
  (`sage_heron_purchases.html`, `sage_heron_sales.html`) interrogent cette vue toutes les 500 ms
  (`$.getJSON`) au lieu de lire `document.cookie` ; les vues d'export passent `request.session`.
  Tests adaptés (`core` lot 3 et 4, `validation_sales`, `validation_purchases` étape 5) + test de
  la vue de statut (consommation unique, 405 en POST).

---

## D35 — mypy à zéro erreur `[x]`

- **Point de départ (2026-10-12)** : 481 erreurs dans 127 fichiers avec la configuration ajoutée par
  l'utilisateur (`warn_return_any`, `warn_unreachable`, etc.).
- **Configuration** (`[tool.mypy]`, commentée dans le pyproject) : `warn_return_any = false` tant que
  l'ORM Django n'est pas typé (sans plugin tout QuerySet / dict renvoie `Any` : 104 faux positifs) ;
  `exclude` étendu à `heron/bin/` et `heron/env/` ; pendulum 2 traité comme non typé
  (`follow_imports = "skip"` : ses stubs déclarent `parse()` en `Date | Time | Duration` et
  `pendulum.date` / `instance` ne sont pas des types, ~50 faux positifs).
- **Codemods** : `no_implicit_optional` (paramètres `x: str = None` -> `str | None`, ~60 sites) ;
  **`AnyStr` remplacé par `str`** dans 51 fichiers : `typing.AnyStr` est un TypeVar `bytes | str`
  et non « n'importe quelle chaîne », d'où des dizaines d'erreurs `str-bytes-safe`, `type-var`,
  `arg-type`.
- **Corrections manuelles (~120 sites)** : annotations invalides (`-> X.objects` -> `QuerySet`,
  `-> iter` -> `Iterator` / `list`, `-> (a, b)` et `-> [a, b]` -> `tuple[a, b]`, `: datetime` /
  `: pendulum` / `: os.path` modules, `-> fonction`, listes de classes en annotation dans
  `validation.py` -> `tuple` / `Any`) ; `urlpatterns: list = []` dans les apps sans route ;
  conteneurs vides annotés (`extra_context: dict`, `lines: list`…) ; gardes `None`
  (`caller_frame()` partagé dans `change_traces` pour `inspect.currentframe().f_back`, `self.object`,
  `edi_objects or []`, `assert self.creds is not None` dans l'authentification Gmail,
  `active_action` dans la boucle RFA) ; accès `dict["clé"]` au lieu de `.get()` quand la clé est
  obligatoire (`checks.py`, `set_hand_invoices`, chemins des PDF) ; `exclude_update_fields=set()` ;
  générateurs PDF annotés `-> None` et `pdf_path: Path` ; `-> None` sur trois fonctions
  d'`invoices_insertions` qui ne renvoyaient rien malgré `-> bool` ; `ChildCenterMixin.model:
  type | None` ; `constr(...)` de pydantic v1 ignoré dans un test (`type: ignore[valid-type]`) ;
  `_BoomPath(PosixPath)` dans les tests heron. Résultat : **`uv run mypy` : Success, 1 215
  fichiers**, suite complète 2 962 tests à 100 %.
- **Complément : corps des fonctions non annotées** (`check_untyped_defs = true` pour le code de
  production ; désactivé par surcharge pour `apps.*.tests`, `heron.tests`, `conftest` dont les
  doubles et `SimpleNamespace` sont volontairement non typés). Les 14 notes « annotation-unchecked »
  disparaissent et 86 erreurs supplémentaires ont été corrigées : attributs de vue déclarés dans les
  mixins (`request: HttpRequest`, `object: Any`, `model: Any`, plus de `= None` typé `None` : 141
  fausses erreurs `"None" has no attribute "user"`), `processing_dict[file.name](file)` au lieu de
  `.get()(file)` dans les trois boucles d'import, `sql_file.open("r") as sql_file` (variable `Path`
  écrasée par le fichier ouvert) renommée dans 4 exports, conteneurs typés (`context`, `dic`,
  `base_dict: dict[str, Any]`, `CATEGORIES_DICT`, `MODEL_DICT: dict[str, Callable]`,
  `columns_*: list[dict[str, Any]]`), accès obligatoires en `[...]`, `TRUE_VALUES` / `FALSE_VALUES`
  / `NULL_VALUES` étendus au niveau de la classe `NullBooleanField` (plus de mutation d'attributs de
  classe à chaque appel), `super().post/form_valid/form_invalid` du mixin en `type: ignore[misc]`,
  ligne `seek(0)` dupliquée supprimée dans `Validation.validate`. `uv run mypy` : Success.

---

## D36 — ruff : arbitrage du périmètre et traitement ERA001 / BLE001 / E402 / F403 `[x]`

- **Décisions de l'utilisateur (2026-10-12)** : `RUF012` (listes de classe des Meta Django) et
  `D104` (paquets vides) ignorés ; `ANN` différé au chantier Django 4.2 (ignoré avec date) ;
  `ERA001`, `BLE001`, `E402`, `F403` à traiter.
- **E402 (134 -> 0)** : tous dans des scripts autonomes (loops, bin, imports, data_fixtures,
  `functions_setups`, `heron/settings/test.py`) où `django.setup()` précède les imports du projet :
  `per-file-ignores` par motif de répertoire, avec commentaire.
- **F403 (166 -> 0)** : uniquement des `__init__.py` qui ré-exportent leurs modules par import
  étoile (views, forms, models) : `"**/__init__.py" = ["F403", "F401"]`.
- **BLE001 (171 -> 0)** : `logger-objects` déclare les quatorze loggers de `heron.loggers`, ce qui
  rend conformes les `except Exception` suivis de `LOGGER_X.exception(...)` (154 cas) ; les 17
  restants : `.error(...)` -> `.exception(...)` (trace conservée : SSE, jauges, Gmail),
  exceptions précises (`OSError`, `ValueError`) pour le chargement / la sauvegarde du token Gmail et
  la création de répertoires, `contextlib.suppress` avant la relance dans `edi/tasks`, un `noqa`
  motivé sur la boucle de réessai d'envoi Gmail.
- **ERA001 (204 -> 0)** : classe commentée de 160 lignes en fin de `function_imports.py` et fichier
  `apps/core/tests/test_function_imports.py` (entièrement commenté, couverture assurée par
  `test_lot2_function_imports.py`) supprimés ; blocs commentés retirés (contrôles désactivés
  d'`opto_33_parser` remplacés par un commentaire en prose, `mogrify` de débogage, `__main__` de
  `edi_pre_processing_pool` à chemins Windows / Téléchargements, catégorie « rfa » de la saisie
  manuelle, routes SSE commentées d'`invoices/urls`, ancienne version du middleware, `pprint_dict`,
  divers appels et clés commentés) ; cinq commentaires en prose reformulés (faux positifs : parenthèses
  ou deux-points pris pour du code).
- Résultat : ruff 5 643 -> 1 830 alertes (voir statistiques ci-dessous), mypy Success, suite
  complète 2 962 tests à 100 %.

---

## D37 — ruff lot 2 : journalisation (G004 / TRY401 / LOG004), UP045, PTH123 `[x]`

- **Décisions de l'utilisateur (2026-10-12)** : `ruff check --fix` lancé sur tout le périmètre
  (corrections sûres seulement, les 166 « unsafe » ne sont pas appliquées) ; `TRY003`, `EM101`,
  `EM102` (messages littéraux dans les `raise`), `ICN001` (alias d'import imposés) et `PLR2004`
  (valeurs littérales dans les comparaisons) ajoutés aux `ignore` avec commentaire.
- **G004 (223 -> 0)** : les f-strings passées aux loggers sont converties en formatage différé
  `%s` / `%r` par un script AST (arguments extraits dans l'ordre, expressions conservées) ; le
  rendu des messages est inchangé.
- **TRY401 (22 -> 0)** : l'exception n'est plus répétée dans le message des
  `LOGGER_X.exception(...)` (la trace la porte déjà) : messages raccourcis en libellé fixe
  (`"TypeError"`, `"Erreur mise à jour progression"`, `"wsau_file"`,
  `"Exception Générale RFA: %s"` avec le fournisseur).
- **LOG004 (25 -> 0)** : `.exception(...)` hors d'un bloc `except` remplacé par `.error(...)`
  (il n'y a pas de trace à joindre).
- **UP045** : `Optional[X]` -> `X | None` par correction automatique.
- **PTH123 (13 fichiers -> 0)** : `open(chemin)` -> `Path(chemin).open(...)` ; dans les tests
  Gmail le `patch` vise désormais `pathlib.Path.open`.
- **mypy** : l'attribut `get_object` fourni par la vue est déclaré sur `ChangeTraceMixin`
  (`get_object: Callable[..., Any]`) après que `ruff --fix` a remplacé le `getattr`.
- **Tests adaptés (changement de comportement des messages de log, signalé)** :
  `core/test_lot4_import_files.py` (libellé `"TypeError"`), `articles/test_bin.py` et
  `centers_purchasing/test_data_fixtures_excel.py` (exception lue dans `record.exc_info`),
  `edi/test_imports_pool.py`
  (`"wsau_file"`), `edi/test_tasks.py` (messages sans suffixe `: verrou impossible`),
  `invoices/test_api_gmail.py` (`Path.open`), `rfa/test_bin.py` (deux assertions lisent
  l'exception dans `record.exc_info` au lieu du message), `heron/test_views_middleware.py`
  (`message % args`).
- Résultat : ruff 1 830 -> 1 035 alertes (G004, TRY401, LOG004, UP045, PTH123 à 0), mypy
  Success, suite complète 2 962 tests à 100 % (lignes et branches).
- **Reste ruff (top)** : D100 125, D101 69, RET504 63, ARG002 55, FBT002 49, SLF001 44,
  D102 41, D106 37, RUF005 36, D107 34, PLR0913 30, PLR0917 29, FBT001 26, DTZ001 20, D103 19.

---

## D38 — ruff lot 3 : docstrings manquantes (D100 / D101 / D102 / D103 / D106 / D107) `[x]`

- **Périmètre** : 325 docstrings ajoutées dans 172 fichiers, rédigées une par une en français
  (une phrase, point final) : 125 modules (D100), 69 classes (D101), 41 méthodes (D102),
  19 fonctions (D103), 37 classes imbriquées `Meta` / `Config` (D106), 34 `__init__` (D107).
- **Méthode** : script AST (`docstrings_add.py`, job tmp) qui insère la docstring devant la
  première instruction du corps (`node.body[0]`, indentation respectée) ; textes de convention
  pour les motifs répétitifs (`apps.py`, `admin.py`, `urls.py`, `Meta` de formulaire ou de
  modèle, `Config` djantic, vues `views_etape_x_y` de validation_purchases), texte rédigé à la
  main pour tout le reste (formulaires, modèles users, validateurs pydantic, filtres de templates,
  `__init__` de formulaires et de classes utilitaires).
- **Modules vides ou squelettes Django** (`# Create your views here.`, `loggers.py` vides,
  `heron/settings/clients.py`, `staging.py`, `heron/tasks.py`) : docstring « réservé » ou
  « aucun pour l'instant », fichiers conservés (apps réservées, cf. mémoire).
- `ruff format` relancé sur les fichiers touchés (ligne vide après la docstring de classe) ;
  aucun test modifié, aucun comportement changé.
- Résultat : ruff 1 035 -> 710 alertes, mypy Success, xenon OK, suite complète 2 962 tests à
  100 %.
- **Reste ruff (top)** : RET504 63, ARG002 55, FBT002 49, SLF001 44, RUF005 36, PLR0913 30,
  PLR0917 29, FBT001 26, DTZ001 20, N805 18, DTZ005 15, DTZ011 14, D105 14, D400/D415 14.

---

## D39 — ruff lot 4 : RET504, ARG002, FBT001 / FBT002 (/ FBT003) `[x]`

- **RET504 (63 -> 0)** : correctif ruff « unsafe » appliqué après relecture du diff : la variable
  intermédiaire assignée juste avant le `return` disparaît (`queryset = ... ; return queryset` ->
  `return ...`) ; deux `return` remontent dans un bloc `with` (curseur), sans changement de
  comportement.
- **ARG002 (55 -> 0)** : 32 `form_valid(self, form, **kwargs)` ramenés à la signature Django
  `form_valid(self, form)` ; `get_queryset(self, **kwargs)` -> `get_queryset(self)` ;
  `Form.clean(self, *args, **kwargs)` -> `clean(self)` ; paramètres imposés par Django mais
  inutilisés préfixés d'un tiret bas (`_request`, `*_args`, `**_kwargs`, `_cleaned_data`,
  `_value` des champs à valeur par défaut, `**_options` des commandes) ; les trois loaders OPTO 33
  (`read`, `read_list`, `read_dict`) gardent `all_lines` pour l'interface commune avec un `noqa`
  motivé.
- **FBT001 / FBT002 (26 / 49 -> 0)** : les paramètres booléens deviennent *keyword-only* (`*,`
  inséré avant le premier booléen) dans 23 fonctions et méthodes de production ; appels
  positionnels corrigés : `_account_lines`, `_content_errors`, `_finish_trace`, `_rows_to_insert`,
  `excel_excel_to_csv` / `excel_xhtml_to_csv` (depuis `ExcelToCsv.make_csv`), `self.read*(all_lines)`
  des loaders, `_create_user(..., is_superuser=True, is_staff=True)`. Les appels des vues, des
  tâches et des tests utilisaient déjà des mots-clés.
- **FBT003** : un appel positionnel corrigé dans le `__main__` d'`od_a_passer`.
- **Décision (à confirmer)** : `FBT001` / `FBT002` / `FBT003` ajoutés aux `per-file-ignores` des
  tests (`conftest.py`, `apps/*/tests/*`, `heron/tests/*`) : les fabriques et doubles de test
  portent légitimement des drapeaux booléens (`in_progress=False`, `fail=False`, `with_a=True`), et
  la consigne est de ne pas réécrire les tests.
- **Changement d'API interne (signalé)** : les fonctions ci-dessus n'acceptent plus leurs booléens
  en positionnel ; aucun test modifié, la suite complète les couvre à 100 %.
- Résultat : ruff 710 -> 500 alertes, mypy Success, xenon OK, suite complète 2 962 tests à 100 %.
- **Reste ruff (top)** : SLF001 44, RUF005 36, PLR0913 30, PLR0917 27, DTZ001 20, N805 18,
  DTZ005 15, DTZ011 14, D105 14, D400/D415 14, TRY301 13, SIM105 13.

---

## D40 — ruff lot 5 : SLF001, RUF005, PLR0913 / PLR0917 `[x]`

- **SLF001 (44 -> 0)** : toutes les alertes visent `Model._meta` et `Model._default_manager`,
  API publiques documentées de Django : `[tool.ruff.lint.flake8-self] ignore-names`, avec
  commentaire. Aucun autre accès à un membre privé dans le code de production.
- **RUF005 (36 -> 0)** : correctif ruff « unsafe » (`a + [b]` -> `[*a, b]`) puis retrait des
  `list()` devenus redondants dans les `Config.include` djantic (`[*model.get_columns_import(),
  "created_at", ...]`) ; les `urlpatterns` de quatre `urls.py` (listes par bloc commenté
  concaténées par `+`) réécrits en une liste avec dépaquetage `*[...]` comme `heron/urls.py`, dont
  le `+ static(...)` final devient `*static(...)` ; `MIDDLEWARE` des settings sans `[] +`. Une
  assertion de test (`edi/test_pre_processing.py`) réécrite à l'identique par le correctif
  (`[*header[:16], "vat_regime"]`), signalée.
- **PLR0913 / PLR0917 (30 / 27 -> 0)** : les signatures à six paramètres sont des aides
  xlsxwriter (classeur, feuille, ligne, colonne, valeurs, format) et des imports de fichiers
  (modèle, flux, source, trace, validateur, paramètres), appelées positionnellement par le code et
  par les tests (non modifiables) : `[tool.ruff.lint.pylint] max-positional-args = 6`,
  `max-args = 8`, commentés. Au-delà, les options passent en mots-clés : `make_insert(..., *,
  extend_model, insert_mode)` (six appels de `book/imports/imports_sage.py` passent
  `extend_model=`), `_insert_file` ramené à huit paramètres (il renvoie les lignes en erreur, le
  compte rendu est composé par `make_insert`, texte identique), `send_mail(server, mail_to,
  subject, *, email_text, email_html, context, attachement_file_list)`,
  `get_pagination_buttons(acutal_page, nbre_pages, *, nbre_boutons, ...)`.
- Résultat : ruff 500 -> 363 alertes, mypy Success, xenon OK, suite complète 2 962 tests à
  100 %.
- **Reste ruff (top)** : DTZ001 20, N805 18, DTZ005 15, DTZ011 14, D105 14, D400/D415 14,
  TRY301 13, SIM105 13, PLR0915 8, PLR0911 4.

---

## D41 — ruff lot 6 : dates naïves DTZ001 / DTZ005 / DTZ011 `[x]`

- **Contexte** : `USE_TZ = True`, `TIME_ZONE = "Europe/Paris"` ; les appels naïfs de production
  passent par `django.utils.timezone` : `timezone.localtime()` (heure locale consciente) pour les
  horodatages de logs et les boucles qui testent l'heure et la minute de lancement (cinq scripts
  `loops`), `timezone.localdate()` pour la date du jour (préfixe de fichier `date_debut_nom_fichier`,
  `DefaultDateTodayField`, processeurs de contexte `date_du_jour` / `annee_du_jour`,
  `date_string_series`), `timezone.now()` pour les calculs de durée.
- **Changement de comportement (signalé)** : `time_string_series` compte désormais les secondes
  écoulées depuis le 01/01/2000 00:00 **UTC** à partir d'un `now` conscient (auparavant horloge
  murale locale naïve, décalée d'une heure selon l'heure d'été) ; la fonction n'est appelée que par
  son test, adapté au même calcul (`heron/core/tests/test_lot1_dates_sql.py`).
- **Sentinelle Sage** : `DEFAULT_DATE = datetime.datetime(1900, 1, 1)` des schémas djantic reste
  naïve à dessein (écrite telle quelle dans les colonnes date par COPY, une valeur consciente
  serait décalée au fuseau de la connexion) : `noqa: DTZ001` commenté.
- **Tests** : `DTZ` ajouté aux `per-file-ignores` des tests (dates de fixtures naïves comparées aux
  sorties, `date.today()` dans les assertions), consigne de ne pas réécrire les tests.
- **Non traité** : `DTZ007` (7) : `strptime` de dates sans heure (formats Sage, Excel, OPTO 33),
  naïves par nature.
- Résultat : ruff 363 -> 314 alertes, mypy Success, xenon OK, suite complète 2 962 tests à 100 %.
- **Reste ruff (top)** : N805 18, D105 14, D400/D415 14, TRY301 13, SIM105 13, RUF043 11,
  G003 11, S608 10, RUF015 8, PLR0915 8, DTZ007 7.

---

## D42 — ruff lot 7 : N805, D105, D400 / D415 `[x]`

- **N805 (18 -> 0)** : les méthodes visées sont des validateurs pydantic v1 (`@validator`), qui
  reçoivent `cls` : `pydantic.validator`, `pydantic.root_validator` et le ré-export
  `apps.core.validations.pydantic_validators_base.validator` (ruff ne suit pas les ré-exports)
  ajoutés à `classmethod-decorators`, commentés.
- **D105 (14 -> 0)** : docstrings des méthodes magiques : `__str__` des modèles (« Texte renvoyé
  dans les selects et à l'affichage de l'objet. »), `__enter__` / `__exit__` du chronomètre
  `Timer`, `__str__` de `FacturXClientError`.
- **D400 / D415 (14 -> 0)** : première ligne des docstrings terminée par un point au lieu de
  « : » ou « ; », la suite commence par une majuscule ; docstring vide « FR : / EN : » de
  `AccountingTypeSage` (conteneur réservé) remplacée par une phrase ; coquille « postgesql »
  corrigée.
- Résultat : ruff 314 -> 254 alertes, mypy Success, xenon OK, suite complète 2 962 tests à 100 %.
- **Reste ruff (top)** : TRY301 13, SIM105 13, RUF043 11, G003 11, S608 10, RUF015 8, PLR0915 8,
  DTZ007 7.

---

## D43 — ruff lot 8 : zéro alerte sur `uv run ruff check --fix apps heron conftest.py scripts` `[x]`

- **Commande de référence** (demande de l'utilisateur) : `uv run ruff check --fix apps heron
  conftest.py scripts` doit rendre « All checks passed! » ; 254 alertes traitées en deux vagues.
- **Tests : `per-file-ignores`** (consigne de ne pas réécrire les tests) : `RUF043` (motifs
  `pytest.raises`), `S105`/`S106`/`S107`/`S108` (mots de passe, jetons et chemins factices),
  `S301`/`S608` (pickle et SQL d'insertion de fixtures), `S603`/`S607` (sous-processus de
  contrôle), `PLW0108`, `C901`, `C416`, `FURB171` (doubles de test).
- **Configuration justifiée** : `N818` ignoré (noms d'exceptions historiques `*Exception`
  importés par les tests) ; `N999` ignoré pour `apps/users/Exceptions.py` et les modules
  `views_etape_*A/B.py` (importés par les tests et l'URLconf) ; `allowed-confusables` pour les
  tables d'homoglyphes de `functions_utilitaires`.
- **`noqa` motivés** : `DTZ007` (7 `strptime` de dates sans heure), `S101` (4 gardes de type
  mypy), `S301` (pickle d'un fichier produit par l'application), `PLC0415` (import différé des
  settings dans `init_directories`), `E741` (attribut `l` du module de fixtures articles, remplacé
  par les tests), `PTH207` (`glob.glob` de `ExcelToCsv.make_csv`, remplacé par les tests).
- **Points d'injection des tests conservés** : les vues articles appellent
  `articles_update_account.update_articles_accounts()` et
  `articles_without_account.import_articles_without_account()` par leur module (les tests
  remplacent l'attribut du module) ; `import_maisons_bi` compte les lignes avec `len(rows)`.
- **Corrections de code (sans changement de comportement)** : RUF036, UP031, INT001 (`_("…%s") %`),
  E741, EXE001 (shebang retiré), B007/PLW2901 (variables de boucle), N806 (variables locales en
  minuscules), PLW0127 (`functions_setups` ré-exporte via `__all__`), PLW0603 (`traceback`
  devient local), RET503/RET504, RUF015 (`cursor.fetchall()[0]`), PTH (`Path` dans
  `functions_excel`, `functions_logs`, `functions_utilitaires`), D205/D210/D301/D419, INP001
  (`heron/templatetags/__init__.py`), S108 (`tempfile.gettempdir()`), PERF401 (compréhensions),
  PLC0415 (imports remontés en tête), B904 (`raise … from error`), TRY300 (`else:`), TRY400
  (`.exception` sans répéter l'erreur), G003 (formatage `%s` des logs), SIM102/103/105/108/117/118/212,
  FURB110, F841.
- **S608** : les requêtes des exports Excel (`GetRows`) et de `add_news_cct_sage` sont composées
  avec `psycopg2.sql` (`sql.Identifier` pour les tables, `sql.SQL` pour les fragments constants).
- **TRY301** : les `raise` sortent des blocs `try` vers des fonctions dédiées
  (`_date_format`, `_require_prepared_kwargs`, `_require_columns`, `_raise_file_errors`,
  `_require_function`, `_check_export_type`, `_check_inside`), comportement identique.
- **PLR0911** : les quatre vues `*_launch` de compta partagent `_launch_post` (contrôles, jauge
  SSE, thread) ; seule `royalties_launch` dépose aussi l'erreur de formulaire en session
  (`session_form_error=True`), comme avant.
- **PLR0915 / C901** : `invoices_insertion` (124 instructions) découpée en `_prepare_insertion`,
  `_InsertionSteps` (journal, jauge, chronométrage), `_run_insertion_steps`, `_insert_purchases`,
  `_insert_sales` : mêmes messages de jauge, mêmes journaux, mêmes transactions ;
  `set_sales_invoices` -> `_sales_line` ; `finalize_period` -> `_finalize_blocking_redirect` ;
  `generate_facturx_invoice` -> `_facturx_server_status` ; `insert_users` -> `_insert_one_user` ;
  encodeur JSON -> `_datetime_to_json` / `_time_to_json` ; exports X3 -> `open_export_file`
  (base_export_x3_functions).
- **Racine du dépôt** (`scripts/pre_check.py` lance `ruff check . --fix`) : docstrings sur
  `essais.py` (vide, bit exécutable retiré) et `main.py` (gabarit `uv init`), `noqa: PLC0415`
  sur l'import différé du `manage.py` standard de Django, `files/` (données) ajouté à
  `extend-exclude`.
- **mypy sans notes** : `disable_error_code = ["annotation-unchecked"]` sur la surcharge des
  tests (corps non annotés non vérifiés, la note était sans effet) ; motif `pendulum.*` retiré de
  la surcharge pendulum (section inutilisée, seul le paquet est importé).
- Résultat : ruff 254 -> 0 (`ruff check .` et `scripts/pre_check.py` au vert), mypy Success,
  xenon OK, suite complète 2 962 tests à 100 %.

---

## D44 — Sonar JavaScript : jeton de téléchargement des templates Sage `[x]`

- `sage_heron_purchases.html` et `sage_heron_sales.html` : `generateToken` sort de
  `$(document).ready` (S7721) et le jeton est tiré de `crypto.getRandomValues` au lieu de
  `Math.random` (S2245) ; format accepté par la route `core:download_status/<str:token>/`.

---

## D45 — Dépendances : django-celery-results 2.6.0, django-dynamic-preferences 1.16.0 `[x]`

- **Motif** : deux `RemovedInDjango41Warning` (`default_app_config`) émis par ces paquets au
  chargement des applications.
- **django-celery-results 2.2.0 -> 2.6.0** (exige Django >= 3.2.25) : `default_app_config` n'est
  plus déclaré sous Django 3.2 ; **quatre migrations à appliquer en production** (`0011` à `0014` :
  `periodic_task_name`, `date_started`, index, statut) par `manage.py migrate django_celery_results`.
- **django-dynamic-preferences 1.12.0 -> 1.16.0** (dernière version compatible Django 3.2, la 1.17
  exige Django 4.2 ; entraîne persisting-theory 1.0) : déclare encore `default_app_config`, la
  dépréciation est filtrée dans `[tool.pytest.ini_options].filterwarnings` jusqu'au chantier
  Django 4.2 (sans effet avant Django 4.1). Aucune migration en attente.
- Résultat : `uv pip check` OK, suite complète 2 962 tests à 100 %, zéro avertissement.

---

## D46 — Sonar S5779 : plus d'`assert` dans un `try` qui attrape `AssertionError` `[x]`

- `GmailAuthenticator._refresh_token` reçoit les credentials en paramètre (l'appelant les a déjà
  contrôlés), `rfa_generation_launch` interroge l'action puis boucle tant qu'elle est en cours :
  les deux `assert` de rétrécissement de type disparaissent sans branche supplémentaire.
- Les deux autres `assert` (hors `try`) sont retirés aussi : `get_credentials` travaille sur une
  variable locale `creds` (`_run_oauth_flow` renvoie les credentials), `_send_once` obtient le
  service par `_ensure_service()` qui le renvoie désormais. Plus aucun `assert` dans le code de
  production, `S101` n'a plus de `noqa`.

---

## D47 — Sonar Web:S5256 / S5257 / S6819 : gabarits PDF WeasyPrint hors analyse `[x]`

- Essai `role="presentation"` sur les 31 `<table>` des gabarits `invoices/pdf_*.html` : S5256 se
  tait mais S5257 (« remplacer la table de mise en page par du CSS ») et S6819 se déclenchent sur
  chaque table (62 alertes) ; essai annulé, HTML d'origine rétabli à l'identique.
- Les trois règles ne peuvent être satisfaites qu'en changeant le balisage (`<th>`, mise en page
  CSS), ce qui modifie le rendu WeasyPrint des factures : décision de ne pas toucher aux gabarits.
- **Décision** : ces gabarits ne sont jamais servis au navigateur, ils sortent de l'analyse web.
  `sonar-project.properties` porte déjà `sonar.exclusions=**/templates/invoices/pdf_*.html` ;
  à reporter dans l'outil qui analyse réellement : SonarQube for IDE (PyCharm, Settings ->
  Tools -> SonarQube for IDE -> File Exclusions, motif `**/templates/invoices/pdf_*.html`) en
  mode autonome, ou la portée d'analyse du projet côté serveur en mode connecté.

---

## Suivi

| Directive | État | Date | Commentaire |
|-----------|------|------|-------------|
| D0 accountancy / core / centers_clients / articles | x | 2026-10-10 | 589 tests, 100 % |
| D10 (6 modules) | ~ | 2026-10-10 | reste chrono_direct.py + functions_postgresql.py |
| D1 | x | 2026-10-10 | 606 tests, 100 % ; URLconf importable sans base |
| D2 | x | 2026-10-10 | 349 tests edi, projet 968 tests, 100 % |
| D3 | x | 2026-10-11 | compta 88 + invoices 327 + validation_purchases 202 tests ; projet 1 604, 100 % (après retrait fpdf2/playwright) |
| D4 | | | |
| D5 | x | 2026-10-11 | 51 appels remplacés, garde-fou en test |
| D6 | | | |
| D7 | x | 2026-10-11 | 31 modules, fixture heron_settings supprimée ; lint des tests propre |
| D8 | x | 2026-10-11 | 132 print -> loggers, 108 except nus ciblés |
| D9 | x | 2026-10-11 | générique multi-feuilles ; 62/62 exports migrés, 2 doublons supprimés |
| D11 | x | 2026-10-11 | imports, formulaires, templates orphelins, pylint centralisé, test réécrit |
| D12 book | x | 2026-10-11 | 206 tests, 100 % ; projet 1 879 tests, 100 % |
| D13 centers_purchasing | x | 2026-10-11 | 117 tests, 100 % ; projet 1 996 tests, 100 % |
| D14 core | x | 2026-10-11 | core 34 % -> 100 %, 4 lots parallèles ; projet 2 386 tests, 100 % |
| D15 countries | x | 2026-10-11 | 42 tests, 100 % ; projet 2 428 tests, 100 % |
| D16 data_flux | x | 2026-10-11 | 45 % -> 100 %, 3 lots parallèles, 147 tests ; projet 2 576 tests, 100 % |
| D17 formations | x | 2026-10-11 | squelette vide : config renommée FormationsConfig, 21 tests ; projet 2 597 tests, 100 % |
| D18 groups | x | 2026-10-11 | squelette vide (URLconf vide routée), 21 tests ; projet 2 618 tests, 100 % |
| D19 import_files | x | 2026-10-11 | 2 modèles sans usage (sha512 des fichiers), __str__ corrigés (None / instance), 21 tests ; projet 2 639 tests, 100 % |
| D20 od | x | 2026-10-11 | 29 tests, 100 % ; facture_heron nulle jamais normalisée ; projet 2 668 tests, 100 % |
| D21 parameters | x | 2026-10-11 | 99 tests, 100 % ; 10 bugs corrigés (numérotation insupprimable, taux de change) ; projet 2 743 tests, 100 % |
| D22 periods / permissions / traces | x | 2026-10-12 | 16 tests, 100 % ; YearForm réécrit, YearPassedForm ajouté ; export traces sans commentaire ; projet 2 755 tests, 100 % |
| D23 validation_sales | x | 2026-10-12 | 22 tests, 100 % ; projet 2 777 tests, 100 % |
| D24 rfa | x | 2026-10-12 | 73 tests, 100 % ; contrôles RFA (produit cartésien), exclusion client, redirection ignorée ; projet 2 897 tests (avec D25), 100 % |
| D25 users | x | 2026-10-12 | 48 tests, 100 % ; 12 bugs (groupes, profil, intégrations en masse) ; projet 2 897 tests, 100 %, toutes les apps couvertes |
| D26 heron (paquet projet) | x | 2026-10-12 | 62 tests, 100 % ; 23 filtres morts, vues dupliquées, numbers_format ; projet 2 968 tests, 100 % |
| D27 Sonar lot 3 | x | 2026-10-12 | 8 nouvelles + anciennes visibles ; PDF_STATIC_DOMAIN obligatoire en prod ; projet 2 963 tests, 100 % |
| D28 Sonar lot 4 | x | 2026-10-12 | 30 anciennes alertes (a..i) ; make_csv et supplier_cct_identifier découpées ; projet 2 963 tests, 100 % |
| D29 Sonar lot 5 | x | 2026-10-12 | anciennes alertes (e..n) ; DOMAINS_WHITELIST de production corrigée ; projet 2 963 tests, 100 % |
| D30 Sonar lot 6 | x | 2026-10-12 | anciennes alertes (f..o) ; line_parser et input_format_date découpées, plus de fonction > 15 ; projet 2 963 tests, 100 % |
| D31 environnement 3.11 | x | 2026-10-12 | retour à 3.11 après tentative 3.14 (Django 3.2 incompatible) ; import circulaire accountancy corrigé ; ruff 40 395 / mypy 501 avec la nouvelle config ; projet 2 963 tests, 100 % |
| D32 pipeline qualité | x | 2026-10-12 | pre_check/pre-commit adaptés, package = false, xenon C/B/A hors tests OK, mypy 487 ; projet 2 963 tests, 100 % |
| D33 Sonar lot 7 | x | 2026-10-12 | anciennes alertes (p..v) ; injection SQL add_news_cct_sage corrigée ; projet 2 961 tests, 100 % |
| D34 téléchargement sans cookie | x | 2026-10-12 | marqueur en session + vue core:download_status ; dernière alerte Sonar levée ; projet 2 962 tests, 100 % |
| D35 mypy | x | 2026-10-12 | 481 -> 0 erreurs (AnyStr -> str, no_implicit_optional, annotations, gardes None) ; projet 2 962 tests, 100 % |
| D36 ruff lot 1 | x | 2026-10-12 | ERA001/BLE001/E402/F403 à 0, RUF012/D104 ignorés, ANN différé ; ruff 5 643 -> 1 830 ; projet 2 962 tests, 100 % |
| D37 ruff lot 2 | x | 2026-10-12 | G004/TRY401/LOG004/UP045/PTH123 à 0, ruff --fix appliqué, TRY003/EM10x/ICN001/PLR2004 ignorés ; ruff 1 830 -> 1 035 ; projet 2 962 tests, 100 % |
| D38 ruff lot 3 docstrings | x | 2026-10-12 | 325 docstrings (D100/D101/D102/D103/D106/D107) dans 172 fichiers ; ruff 1 035 -> 710 ; projet 2 962 tests, 100 % |
| D39 ruff lot 4 | x | 2026-10-12 | RET504/ARG002/FBT001/FBT002 à 0 (booléens keyword-only, signatures Django rétablies), FBT ignoré dans les tests ; ruff 710 -> 500 ; projet 2 962 tests, 100 % |
| D40 ruff lot 5 | x | 2026-10-12 | SLF001 (_meta ignoré), RUF005 (dépaquetage, urls.py), PLR0913/0917 (seuils 8/6, options en mots-clés) ; ruff 500 -> 363 ; projet 2 962 tests, 100 % |
| D41 ruff lot 6 dates | x | 2026-10-12 | DTZ001/005/011 à 0 via django.utils.timezone (localtime/localdate/now), DTZ ignoré dans les tests, DEFAULT_DATE naïve justifiée ; ruff 363 -> 314 ; projet 2 962 tests, 100 % |
| D42 ruff lot 7 | x | 2026-10-12 | N805 (validateurs pydantic en classmethod-decorators), D105 et D400/D415 à 0 ; ruff 314 -> 254 ; projet 2 962 tests, 100 % |
| D43 ruff lot 8 | x | 2026-10-12 | `ruff check --fix apps heron conftest.py scripts` à 0 alerte (254 traitées : refactorings invoices_insertion / vues compta, psycopg2.sql, ignores tests justifiés) ; projet 2 962 tests, 100 % |
| D44 Sonar JS | x | 2026-10-12 | generateToken hors du ready, crypto.getRandomValues (S7721/S2245) dans les deux templates Sage |
| D45 dépendances | x | 2026-10-12 | django-celery-results 2.6.0 (4 migrations à passer en production), django-dynamic-preferences 1.16.0 (dépréciation filtrée) ; projet 2 962 tests, 100 %, 0 avertissement |
| D46 Sonar S5779 | x | 2026-10-12 | plus aucun assert en production (paramètre creds, boucle while, creds local, _ensure_service renvoie le service) ; projet 2 962 tests, 100 % |
| D47 Sonar gabarits PDF | x | 2026-10-12 | role="presentation" annulé (62 alertes S5257/S6819) ; gabarits pdf_*.html à exclure de l'analyse (IDE ou serveur), HTML inchangé |
