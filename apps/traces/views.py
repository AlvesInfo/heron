import pendulum
from django.shortcuts import redirect, reverse, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.functions.functions_http import get_pagination_buttons
from apps.data_flux.models import Trace
from apps.traces.excel_outputs.edi_traces_exports import excel_edi_traces


def trace_edi_list(request):
    """Affichage de toutes les traces présentes en base par pagination de 50"""
    limit = 50
    paginator = Paginator(Trace.objects.all().order_by("-created_at"), limit)
    page = request.GET.get("page")

    try:
        traces = paginator.page(page)
    except PageNotAnInteger:
        traces = paginator.page(1)
    except EmptyPage:
        traces = paginator.page(paginator.num_pages)

    context = {
        "traces": traces,
        "pagination": get_pagination_buttons(
            traces.number, paginator.num_pages, nbre_boutons=5, position_color="cadetblue"
        ),
        "num_items": paginator.count,
        "num_pages": paginator.num_pages,
        "start_index": (traces.start_index() - 1) if traces.start_index() else 0,
        "end_index": traces.end_index(),
    }
    return render(request, "traces/edi_traces.html", context=context)


def edi_traces_export(request, start_index, end_index):
    """Export Excel de la liste des traces affichées à l'écran des traces EDI avec la pgination
    :param start_index: index initial slicing queryset
    :param end_index: index final slicing queryset
    :param request: Request Django
    :return: response_file
    """

    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = f"LECTURES_TRACES_{today.format('Y_M_D')}{today.int_timestamp}.xlsx"

            return response_file(
                excel_edi_traces, file_name, CONTENT_TYPE_EXCEL, start_index, end_index
            )

    except:
        LOGGER_VIEWS.exception("view : edi_traces_export")

    return redirect(reverse("traces:edi_traces"))
