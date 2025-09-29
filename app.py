import json
import re
from typing import Tuple, List, Dict

from flask import Flask, render_template, request
import requests

app = Flask(__name__)
unit_data_file = 'data/unit_data.json'
main_data_file = 'data/main.json'

index_output_file = 'docs/index.html'
table_output_file = 'docs/units_summary.html'
rarity_matrix_output_file = 'docs/unit_rarity_matrix.html'
units_details_directory = 'docs/units'

unit_data = None
main_data = None
hint_values: Dict[str, List[str]] = dict()


@app.route('/update')
def update():
    raw_unit_data = requests.get('https://raw.githubusercontent.com/ItsBen321/SkyShard-Public/refs/heads/main/game_info/unit_data.JSON')
    with open(unit_data_file, 'wb') as file:
        file.write(raw_unit_data.content)
    raw_main_data = requests.get(
        'https://raw.githubusercontent.com/ItsBen321/SkyShard-Public/refs/heads/main/game_info/Main.json')
    with open(main_data_file, 'wb') as file:
        file.write(raw_main_data.content)

    global unit_data
    global main_data
    global hint_values
    unit_data = None
    main_data = None
    hint_values = dict()
    read_unit_data()
    read_main_data()

    with open(index_output_file, 'wb') as file:
        file.write(bytes(index(), 'utf-8'))

    with open(table_output_file, 'wb') as file:
        file.write(bytes(units(), 'utf-8'))

    with open(rarity_matrix_output_file, 'wb') as file:
        file.write(bytes(unit_rarity_matrix(), 'utf-8'))

    for unit in read_unit_data():
        with open(units_details_directory + '/unit_' + str(unit['ID']) + '.html', 'wb') as file:
            file.write(bytes(unit_detail(unit['ID']), 'utf-8'))

    return 'OK'

@app.route('/')
def index():
    sorted_unit_data = sorted(read_unit_data(), key=lambda unit: unit['Name'])
    return render_template('index.html', unit_data=sorted_unit_data, main=read_main_data())

@app.route('/data')
def data():
    return read_unit_data()

@app.route('/units')
def units():
    return render_template('units_table.html', unit_data=read_unit_data(), main=read_main_data())

@app.route('/unit')
def unit_detail_endpoint():
    unit_id = request.args.get('id')
    return unit_detail(unit_id)

@app.route('/unit_rarity_matrix')
def unit_rarity_matrix_endpoint():
    return unit_rarity_matrix()


def unit_rarity_matrix():
    x_vars = ['Faction', 'Role', 'Type']
    y_vars = ['Rarity']
    x_labels, y_labels, matrix_data = create_matrix_data(x_vars, y_vars)
    return render_template('matrix.html', x_labels=x_labels, y_labels=y_labels, matrix_data=matrix_data, main=read_main_data())


def unit_detail(unit_id):
    for unit in read_unit_data():
        if unit['ID'] == int(unit_id):
            return render_template('unit_detail.html', unit=unit, main=read_main_data())
    return "Unit ID not found: " + unit_id


def create_matrix_data(x_vars, y_vars) -> Tuple[List[str], List[str], List[List[str]]]:

    global hint_values
    sorted_unit_data = sorted(read_unit_data(), key=lambda u: u['Name'])

    x_labels = list()
    y_labels = list()
    for x_var in x_vars:
        x_labels.extend(sorted(hint_values.get(x_var)))
    for y_var in y_vars:
        y_labels.extend(sorted(hint_values.get(y_var)))
    x_indices = dict()
    y_indices = dict()
    for idx, value in enumerate(x_labels):
        x_indices[value] = idx
    for idx, value in enumerate(y_labels):
        y_indices[value] = idx

    matrix = list()
    for y_idx in range(0, len(y_labels)):
        matrix.append(list())
        for x_idx in range(0, len(x_labels)):
            matrix[y_idx].append('')


    for unit in sorted_unit_data:
        for x_var in x_vars:
            for y_var in y_vars:
                x_idx = x_indices.get(unit[x_var])
                y_idx = y_indices.get(unit[y_var])
                if matrix[y_idx][x_idx]:
                    matrix[y_idx][x_idx] = matrix[y_idx][x_idx] + "," + unit['Name']
                else:
                    matrix[y_idx][x_idx] = unit['Name']

    return x_labels, y_labels, matrix


def read_unit_data():
    global unit_data
    global hint_values
    if unit_data is None:
        unit_data = list()
        hint_pattern = re.compile(r"^\S+:\d+$")
        with open(unit_data_file, 'r') as file:
            raw_unit_data = json.load(file)
        for raw_unit in raw_unit_data:
            unit = dict()
            for entry in raw_unit:
                unit[entry['var']] = entry['value']
                if ':' in entry['hint']:
                    hints = entry['hint'].split(',')
                    found_map = False
                    for hint in hints:
                        if hint_pattern.match(hint):
                            value_key_list = hint.split(':')
                            var_hint_values: set = hint_values.setdefault(entry['var'], set())
                            var_hint_values.add(value_key_list[0])
                            if entry['value'] == int(value_key_list[1]):
                                unit[entry['var']] = value_key_list[0]
                                unit[entry['var'] + '_RAW'] = entry['value']
                                found_map = True
                                break
                    if not found_map:
                        unit[entry['var']] = entry['value']
                else:
                    unit[entry['var']] = entry['value']
                    if isinstance(entry['value'], (int, str)):
                        var_hint_values: set = hint_values.setdefault(entry['var'], set())
                        var_hint_values.add(entry['value'])

            unit_data.append(unit)

    return unit_data


def read_main_data():
    global main_data
    if main_data is None:
        with open(main_data_file, 'r') as file:
            main_data = json.load(file)
    return main_data



if __name__ == '__main__':
    app.run(debug=True)