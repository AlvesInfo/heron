# pylint: disable=E0401,W0718,E0633,W1203
"""
FR : Module de génération des factures pdf de ventes sous task Celery
EN : Module for generating pdf sales invoices under task Celery

Commentaire:

created at: 2022-06-07
created by: Paulo ALVES

modified at: 2023-06-07
modified by: Paulo ALVES
"""
# import time
#
# from celery import shared_task
#
# from heron.loggers import LOGGER_INVOICES
# from apps.users.models import User
# from apps.invoices.bin.generate_invoices_pdf import invoices_pdf_generation, Maison
#
#
# @shared_task(name="invoices_insertions")
# def launch_invoices_insertions(user_pk):
#     """
#     Insertion des factures définitives achats et ventes
#     :param user_pk: uuid de l'utilisateur qui a lancé le process
#     """
#
#     start_initial = time.time()
#
#     error = False
#     trace = None
#     to_print = ""
#
#     try:
#         user = User.objects.get(pk=user_pk)
#         # trace, to_print = invoices_pdf_generation(cct)
#         trace.created_by = user
#     except TypeError as except_error:
#         error = True
#         to_print += f"TypeError : {except_error}\n"
#         LOGGER_INVOICES.exception(f"TypeError : {except_error!r}")
#
#     except Exception as except_error:
#         error = True
#         LOGGER_INVOICES.exception(
#             f"Exception Générale: launch_invoices_insertions\n{except_error!r}"
#         )
#
#     finally:
#         if error and trace:
#             trace.errors = True
#             trace.comment = (
#                 trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
#             )
#
#         if trace is not None:
#             trace.invoices = True
#             trace.save()
#
#     LOGGER_INVOICES.warning(
#         to_print
#         + f"launch_invoices_insertions : {time.time() - start_initial} s"
#         + "\n\n======================================================================="
#         "======================================================================="
#     )
#
#     return {"launch_invoices_insertions : ": f"{time.time() - start_initial} s"}
#
#
# @shared_task(name="generate_pdf_invoices")
# def launch_generate_pdf_invoices(cct: Maison.cct, user_pk):
#     """
#     Génération des pdf des factures de ventes
#     :param cct: cct de la facture pdf à générer
#     :param user_pk: uuid de l'utilisateur qui a lancé le process
#     """
#
#     start_initial = time.time()
#
#     error = False
#     trace = None
#     to_print = ""
#
#     try:
#         user = User.objects.get(pk=user_pk)
#         trace, to_print = invoices_pdf_generation(cct)
#         trace.created_by = user
#     except TypeError as except_error:
#         error = True
#         to_print += f"TypeError : {except_error}\n"
#         LOGGER_INVOICES.exception(f"TypeError : {except_error!r}")
#
#     except Exception as except_error:
#         error = True
#         LOGGER_INVOICES.exception(
#             f"Exception Générale: launch_generate_pdf_invoices : {cct}\n{except_error!r}"
#         )
#
#     finally:
#         if error and trace:
#             trace.errors = True
#             trace.comment = (
#                 trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
#             )
#
#         if trace is not None:
#             trace.invoices = True
#             trace.save()
#
#     LOGGER_INVOICES.warning(
#         to_print
#         + f"Génération du pdf {cct} in : {time.time() - start_initial} s"
#         + "\n\n======================================================================="
#         "======================================================================="
#     )
#
#     return {"Generation facture pdf : ": f"cct : {cct} - {time.time() - start_initial} s"}
