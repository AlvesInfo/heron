from django.urls import path

from apps.traces.views import (
    trace_edi_list,
    edi_traces_export
)

app_name = "apps.traces"

urlpatterns = [
        # Traces du dataflux edi
        path(
            "edi_traces/",
            trace_edi_list,
            name="edi_traces",
        ),
        path(
            "edi_traces_export/<int:start_index>/<int:end_index>/",
            edi_traces_export,
            name="edi_traces_export",
        ),
]
