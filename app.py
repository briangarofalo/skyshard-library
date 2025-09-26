import json
import re

from flask import Flask, render_template, request
import requests

app = Flask(__name__)
unit_data_file = 'data/unit_data.json'
main_data_file = 'data/main.json'

index_output_file = 'docs/index.html'
table_output_file = 'docs/units_summary.html'
units_details_directory = 'docs/units'

unit_data = None
main_data = None


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
    unit_data = None
    main_data = None
    read_unit_data()
    read_main_data()

    with open(index_output_file, 'wb') as file:
        file.write(bytes(index(), 'utf-8'))

    with open(table_output_file, 'wb') as file:
        file.write(bytes(table(), 'utf-8'))

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
def table():
    return render_template('units_table.html', unit_data=read_unit_data(), main=read_main_data())

@app.route('/unit')
def unit_detail_endpoint():
    unit_id = request.args.get('id')
    return unit_detail(unit_id)


def unit_detail(unit_id):
    for unit in read_unit_data():
        if unit['ID'] == int(unit_id):
            return render_template('unit_detail.html', unit=unit, main=read_main_data())
    return "Unit ID not found: " + unit_id


def read_unit_data():
    global unit_data
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
                            if entry['value'] == int(value_key_list[1]):
                                unit[entry['var']] = value_key_list[0]
                                unit[entry['var'] + '_RAW'] = entry['value']
                                found_map = True
                                break
                    if not found_map:
                        unit[entry['var']] = entry['value']
                else:
                    unit[entry['var']] = entry['value']

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