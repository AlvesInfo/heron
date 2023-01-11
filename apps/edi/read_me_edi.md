Module por l'intégration des factures fournisseur au format EDI ou Propriétaire.
---
Pour ajouter de nouvelles intégrations, il faut :

1. Créer un Path de création automatique, pour le répertoire en metant le path dans le fichier heron.settings.suppliers.
---
2. Créer l'espace de nom et les paramètre du fichier du founisseur (model: SupplierDefinition):
   - table_name : Nom du namespace souhaité
   - header_line : Première ligne du fichier à lire
   - delimiter : Délimiteur au sens csv ex.: ";"
   - encoding : Encoding du fichier fournisseur
   - escapechar : Caractère d'échapement de la base de donnée ex.: "
   - lineterminator : caractère de fin de ligne du fichier ex.: "\n"
   - quotechar : Quote au sens csv ex.: "
   - supplier_name : Nom du fournisseur pour affichage si il ne vient pas dans le fichier
   - supplier_siret : Siret du fournisseur au cas où il ne vienne pas dans le fichier, pour des besoins d'identification du founisseur du fichier
   - directory : Répertoire de dépôt des fichiers de facture (après la base : file/processing/suppliers_invoices_files)
---
3. Création des associations entre les colonnes de la table EdiImport et les colonnes du fichier (model: ColumnDefinition). Pour les colonnes du fichier il faut les sanitaze avec l = ["Code Adhérent", "Nature", "DocNum", "DOcdate", "ItemCode", "Dscription", "Quantity", "Code TVA sur CA", "prix Brut", "prix Net", "prix TTC", "U_NUMSER"]
from apps.data_flux.loader import FileLoader
FileLoader._get_sanitaze(l):
   - attr_name : Nom du champ dans la table du model EdiImport
   - file_column : Nom de la colonne dans le fichier ou position par numéro (commence à 0)
   - ranking : Classement de l'ordre des colonnes souhaité
   - input_format : Format type à l'entrée
   - function : fonction à appliquer avant validation
   - exclude_rows_dict : Si le champ est à exclure
   - unique : Si le champ est unique seule ou par compoistion
---
4. Création d'un Schema (Djantic ou Pydantic), d'un formulaire Django ou d'un serializer DRF, dans le fichier apps.edi.forms.forms_djantic.invoices. Il faut prendre pour modèle ceux qui sont déjà éxistants. Veillez à ce que les champs ne doivent pas être mappés ou validés par un validateur spécifique. Si c'est le cas alors il faut créer le validateur, dans le fichier apps.core.validations.pydantic_validators_base.
---
5. Vérifier les formats de type dates, tva, nombres, etc..., dans le fichier pour création d'un pré-validateur éventuel.
---
6.  Créer une fonction pour l'import, dans le fichier apps.edi.imports_suppliers_invoices_pool. Prendre exemple sur les fonctions déjà existantes.
---
7. Rajouter dans le dictionnaire des process, la fonction précédemment créée, dans le fichier apps.edi.loops.imports_loop.
___
8. QTY = 1 si Null