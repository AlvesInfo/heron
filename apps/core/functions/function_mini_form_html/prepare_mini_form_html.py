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


INITIAL_HTML = """
<div class="ui segment">
  <div class="ui equal width grid center">
    <div class="one wide column"></div>
"""


def construct_html():
    file = Path("mini_form_html.csv")

    with file.open("r") as csv_file:
        csv_reader = csv.reader(
            csv_file,
            delimiter=";",
            quotechar='"',
            lineterminator="",
            quoting=csv.QUOTE_NONNUMERIC,
        )
        html = INITIAL_HTML
        column, width_column, index, width, read_only, champ, label = next(csv_reader)
        test_column = column

        field_html = f"""
            <div class="{WIDTH_DICT.get(width)} wide field">
              <label for="id_{champ}">{label}&nbsp;:</label>
        """
        if read_only == "o":
            field_html += f"""
                <input type="text" name="{champ}"
                     value="{{ form.{champ}.value }}"
                     required=""
                     id="id_{champ}"
                     readonly
                     style="background-color: cornsilk;font-weight: bold;">            
            """
        else:
            field_html += f"""
            """


        html += f"""
    <div class="{WIDTH_DICT.get(width_column)} wide column">
      <div class="ui segment">
        <h4 class="ui floated header">{column}</h4>
        <div class="ui clearing divider"></div>
        <div class="ui mini form" style="font-size: 12px;font-weight:bold;">
          <div class="fields">      
        """

        for row in csv_reader:
            print(row)


if __name__ == "__main__":
    construct_html()
