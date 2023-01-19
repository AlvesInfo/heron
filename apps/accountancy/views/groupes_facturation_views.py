# pylint: disable=R0903
"""
Views
"""
import os
from pathlib import Path
import hashlib
from datetime import timedelta, date

import pendulum
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.views.generic.edit import FormView
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, UpdateView, CreateView
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q

from heron import settings
from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL

from apps.accountancy.models import (
    GroupingGoods,
    DefaultAxeProAricleAcuitis,
    DefaultAxeProAricleCosium,
)