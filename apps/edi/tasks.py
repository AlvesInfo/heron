# pylint: disable=
"""
FR : Module des tâches asynchrone d'import des factures edi
EN : Asynchronous task module for importing edi invoices

Commentaire:

created at: 2022-12-26
created by: Paulo ALVES

modified at: 2022-12-26
modified by: Paulo ALVES
"""
from celery import shared_task
from apps.edi.loops.imports_loop_pool import main as edi_main


@shared_task()
def start_edi_import():
    """Lancement de la tâche edi import"""
    edi_main()
