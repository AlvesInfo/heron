from pathlib import Path
import csv

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


def get_html_field(width: str, read_only: str, if_create: str, champ: str, label: str) -> str:
    """Fonction qui renvoie le html pour le champ d'un mini form semantic ui"""

    field_html = f"""
              <div class="{WIDTH_DICT.get(width)} wide field">
                <label for="id_{champ}" style="text-align: left;">{label}&nbsp;:</label>"""

    if if_create == "o":
        field_html += (
            """
                {% if create %}
                    {{"""
            f"form.{champ}"
            """}}
                {% else %}"""
        )

    if read_only == "o":
        field_html += (
            f"""
                    <input type="text" 
                           name="{champ}"
                           """
            """value="{{ form."""
            f"""{champ}"""
            """.value }}" """
            f"""
                           required=""
                           id="id_{champ}"
                           readonly
                           style="background-color: cornsilk;font-weight: bold;">"""
        )

        if if_create == "o":
            field_html += """
                {% endif %}"""

    else:
        field_html += (
            """
                {{"""
            f" form.{champ} "
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
        column, width_column, index, width, read_only, if_create, champ, label = next(csv_reader)
        test_column = column
        test_index = index
        html = f"""
    <div class="{WIDTH_DICT.get(width_column)} wide column" style="padding: 0;margin: 10px;">
      <div class="ui segment">
        <h4 class="ui floated header">{column}</h4>
        <div class="ui clearing divider"></div>
        <div class="ui mini form" style="font-size: 12px;font-weight:bold;">
        
          <div class="fields">"""

        html += get_html_field(width, read_only, if_create, champ, label)

        for row in csv_reader:
            column, width_column, index, width, read_only, if_create, champ, label = row

            if test_column != column:
                test_column = column
                test_index = index
                html += f"""
          </div>
        </div>
      </div>
    </div>

    <div class="{WIDTH_DICT.get(width_column)} wide column" style="padding: 0;margin: 10px;">
      <div class="ui segment">
        <h4 class="ui floated header">{column}</h4>
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

            html += get_html_field(width, read_only, if_create, champ, label)

        html += """

          </div>
        </div>
      </div>
    </div>"""
        print(html)


if __name__ == "__main__":
    construct_html()
