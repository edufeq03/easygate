"""Main module."""

from flask_appbuilder import (
    action,
    aggregate_count,
    BaseView,
    expose,
    GroupByChartView,
    has_access,
    ModelView,
)
from flask import Blueprint, request, jsonify, Response, session
from flask_appbuilder.views import MultipleView, SimpleFormView, PublicFormView
import os
from copy import deepcopy

TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), "templates")
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), "static")
STATIC_URL_PATH = "/static/coreui"


# Use the Flask Blueprint to create an appized app and setup our routing
# https://flask.palletsprojects.com/en/2.0.x/blueprints/#templates
# You must register this blueprint on your app!

coreui_bp = Blueprint(
    "coreui_theme",
    __name__,
    template_folder=TEMPLATE_FOLDER,
    static_folder=STATIC_FOLDER,
    static_url_path=STATIC_URL_PATH,
)

extra_args = {
    'include_sidebar' : True,
    'include_top_menu': True,
    'include_top_bar_toggle': True,
    'include_account_menu': True,
    'breadcrumbs_submenu': True,
}


class CoreUIBaseView(BaseView):
    template_folder = TEMPLATE_FOLDER
    static_folder = STATIC_FOLDER
    static_url_path = STATIC_URL_PATH
    extra_args = deepcopy(extra_args)


class CoreUIModelView(ModelView):
    template_folder = TEMPLATE_FOLDER
    static_folder = STATIC_FOLDER
    static_url_path = STATIC_URL_PATH
    extra_args = deepcopy(extra_args)
    form_template = "coreui/general/model/edit.html"
    edit_template = "coreui/general/model/edit.html"
    list_template = "coreui/general/model/list.html"
    show_template = "coreui/general/model/show.html"
    add_template = "coreui/general/model/add.html"


class CoreUISimpleFormView(SimpleFormView):
    template_folder = TEMPLATE_FOLDER
    static_folder = STATIC_FOLDER
    static_url_path = STATIC_URL_PATH
    extra_args = deepcopy(extra_args)
    form_template = "coreui/general/model/edit.html"


class CoreUIPublicFormView(PublicFormView):
    template_folder = TEMPLATE_FOLDER
    static_folder = STATIC_FOLDER
    static_url_path = STATIC_URL_PATH
    extra_args = deepcopy(extra_args)
    form_template = "coreui/general/model/edit.html"
