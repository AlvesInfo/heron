from pathlib import Path
import csv
import os
import sys
import platform

import django
from django.db import connection, connections
from django.db.utils import IntegrityError

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

WIDTH_DICT = {
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
    "10": "ten",
    "11": "eleven",
    "12": "twelve",
    "13": "thirteen",
    "14": "fourteen",
    "15": "fifteen",
    "16": "sixteen",
}


def get_html_field(
    width: str, read_only: str, if_create: str, champ: str, label: str, prefix: str
) -> str:
    """Fonction qui renvoie le html pour le champ d'un mini form semantic ui"""

    field_html = f"""
              <div class="{WIDTH_DICT.get(width)} wide field">
                <label for="id_{champ}" style="text-align: left;">{label}&nbsp;:</label>"""

    if if_create == "o":
        field_html += (
            """
                {% if create %}
                    {{"""
            f"{prefix}.{champ}"
            """}}
                {% else %}"""
        )

    if read_only == "o":
        field_html += (
            f"""
                    <input type="text" 
                           name="{champ}"
                           """
            """value="{{ """
            f"""{prefix}.{champ}"""
            """.value }}" """
            f"""
                           required=""
                           id="id_{champ}"
                           readonly
                           style="background-color: #efefff;font-weight: bold;">"""
        )

        if if_create == "o":
            field_html += """
                {% endif %}"""

    else:
        field_html += (
            """
                {{"""
            f" {prefix}.{champ} "
            "}}"
        )

    field_html += """
              </div>"""
    return field_html


def construct_html() -> str:
    """Fonction qui renvoie le html d'un form semantic ui"""
    file = Path("mini_form_html.csv")

    with file.open("r", encoding="utf8") as csv_file:
        csv_reader = csv.reader(
            csv_file,
            delimiter=";",
            quotechar='"',
            lineterminator="",
            quoting=csv.QUOTE_NONNUMERIC,
        )
        column, width_column, index, width, read_only, if_create, champ, label, prefix = next(
            csv_reader
        )
        test_column = column
        test_index = index
        html = f"""
    <div class="{WIDTH_DICT.get(width_column)} wide column" style="padding: 0;margin: 10px;">
      <div class="ui segment" style="padding-bottom: 0;">
        <h3 class="ui floated header" style="margin-bottom: 5px;">{column}</h3>
        <div class="ui clearing divider"></div>
        <div class="ui mini form" style="font-size: 12px;font-weight:bold;">
        
          <div class="fields">"""

        html += get_html_field(width, read_only, if_create, champ, label, prefix)

        for row in csv_reader:
            column, width_column, index, width, read_only, if_create, champ, label, prefix = row

            if test_column != column:
                test_column = column
                test_index = index
                html += f"""
          </div>
        </div>
      </div>
    </div>

    <div class="{WIDTH_DICT.get(width_column)} wide column" style="padding: 0;margin: 10px;">
      <div class="ui segment" style="padding-bottom: 0;">
        <h3 class="ui floated header" style="margin-bottom: 5px;">{column}</h3>
        <div class="ui clearing divider"></div>
        <div class="ui mini form" style="font-size: 12px;font-weight:bold;">
          
          <div class="fields"> 
        """

            if test_index != index:
                html += """
                
          </div>
          
          <div class="fields"> 
                """
                test_index = index

            html += get_html_field(width, read_only, if_create, champ, label, prefix)

        html += """

          </div>
        </div>
      </div>
    </div>"""
        print(html)


def extract_fields():
    """Extraction du nom des champs et des verboses names"""
    from apps.centers_purchasing.models import (
        PrincipalCenterPurchase,
        ChildCenterPurchase,
        Signboard,
        SignboardModel,
        Translation,
        SignboardModelTranslate,
        TranslationParamaters,
    )

    object_list = [
        PrincipalCenterPurchase,
        ChildCenterPurchase,
        Signboard,
        SignboardModel,
        Translation,
        SignboardModelTranslate,
        TranslationParamaters,
    ]

    for objectName in object_list:
        print(f"{objectName} =====================================================================")

        for field in objectName._meta.fields:
            print(field.name, field.verbose_name.capitalize(), sep="\t")

        print("===================================================================================")


if __name__ == "__main__":
    construct_html()
    # extract_fields()
