"""Parse micromeritics xls output files.
@author Chris Murdock,
@modified Paul Iacomi

adapted from
https://github.com/Micromeritics/micromeritics/tree/master/micromeritics
"""

import re
from itertools import product
import dateutil.parser

import numpy as np
import xlrd
import pandas as pd

_NUMBER_REGEX = re.compile(r'^(-)?\d+(.|,)?\d+')

_FIELDS = {
    'material': {
        'text': ['sample:', 'echantillon:'],
        'name': 'sample_id',
        'row': 0,
        'column': 1,
        'type': 'string'
    },
    'adsorbate': {
        'text': ['analysis ads'],
        'name': 'adsorbate',
        'row': 0,
        'column': 1,
        'type': 'string'
    },
    'temperature': {
        'text': ['analysis bath'],
        'name': 'temperature',
        'row': 0,
        'column': 1,
        'type': 'number'
    },
    'user': {
        'text': ['operator', 'analyste', 'Operator:'],
        'name': 'user',
        'row': 0,
        'column': 1,
        'type': 'string'
    },
    'date': {
        'text': ['started',"Started:"],
        'name': 'date',
        'row': 0,
        'column': 1,
        'type': 'string'
    },
    'sample_mass': {
        'text': ['sample mass'],
        'name': 'mass',
        'row': 0,
        'column': 1,
        'type': 'string'
    },
    'apparatus': {
        'text': ['micromeritics instrument'],
        'name': 'apparatus',
        'row': 1,
        'column': 0,
        'type': 'string'
    },
    'comment': {
        'text': ['comments'],
        'name': 'comment',
        'row': 0,
        'column': 0,
        'type': 'string'
    },
    'isotherm_data': {
        'text': ['isotherm tabular'],
        'type': 'isotherm_data',
        'labels': {
            'Absolute': 'pressure',
            'Relative': 'pressure_relative',
            'Saturation': 'pressure_saturation',
            'Quantity': 'loading',
            'Elapsed': 'time',
        }
    },
    'primary_data': {
        'text': ['primary data'],
        'type': 'error',
        'row': 1,
        'column': 0,
        'name': 'errors'
    },
    'cell_value': {
        'header': {
            'row': 2
        },
        'datapoints': {
            'row': 3
        }
    }
}


def parse(path):
    """
    Parse an xls file generated by micromeritics software.
    Parameters
    ----------
    path: str
        the location of an xls file generated by a micromeritics instrument.
    Returns
    -------
    dict
        A dictionary containing report information.
    """
    workbook = xlrd.open_workbook(path, encoding_override='latin-1')
    sheet = workbook.sheet_by_index(0)
    data = {}
    errors = []
    for row, col in product(range(sheet.nrows), range(sheet.ncols)):
        cell_value = str(sheet.cell(row, col).value).lower()
        try:
            field = next(
                v for k, v in _FIELDS.items()
                if any([cell_value.startswith(n) for n in v.get('text', [])])
            )
        except StopIteration:
            continue
        if field['type'] == 'number':
            val = sheet.cell(row + field['row'], col + field['column']).value
            data[field['name']] = _handle_numbers(field, val)
        elif field['type'] == 'string':
            val = sheet.cell(row + field['row'], col + field['column']).value
            data[field['name']] = _handle_string(val)
        elif field['type'] == 'isotherm_data':
            for i, item in enumerate(_get_data_labels(sheet, row, col)):
                points = _get_datapoints(sheet, row, col + i)
                _assign_data(item, field, data, points)
        elif field['type'] == 'error':
            errors += _get_errors(sheet, row, col)
    if errors:
        data['errors'] = errors
    _check(data, path)

    #if parser fails at instrument try getting instrument from relative position
    if "apparatus" not in data:
        data['apparatus'] = (str(sheet.cell(1,0).value))

    # get units of mass
    data["adsorbent_unit"]  = data["mass"].split()[-1]
    data["mass"] = float(data["mass"].split()[0])

    # convert to expected format
    data["temperature_unit"] = "K"
    if data["date"] == '':
        data["date"] = str(sheet.cell(11,1).value)
    data['date'] = dateutil.parser.parse(data['date']).isoformat()
    columns = [
        c for c in _FIELDS['isotherm_data']['labels'].values() if c in data
    ]

    #remove time for now because it can lead to uneven columns
    if "time" in columns:
        columns.remove("time")

    # for cases where there is few press
    if len(data['pressure_saturation']) != len(data["loading"])+1:
        columns.remove("pressure_saturation")

    data_arr = np.array([data.pop(c) for c in columns]).T

    # create pandas dataframe of adsorption and desorption data
    data_arr = pd.DataFrame(data_arr, columns=columns)
    
    #if absolute pressure not present
    if "pressure" not in data_arr:
        data_arr["pressure"] = data_arr["pressure_relative"]*data["pressure_saturation"][0]


    # split ads / desorption branches
    turning_point = data_arr["pressure"].argmax()+1

    return (
        data,
        data_arr[:turning_point],
        data_arr[turning_point:]
    )


def _handle_numbers(field, val):
    """
    Removes any extra information (such as units) to return only the number as a float.
    Input is a cell of type 'number'.
    """
    if val:
        ret = float(_NUMBER_REGEX.search(val.replace(',', '')).group())
        if field['name'] == 'temperature' and '°C' in val:
            ret = ret + 273.15
        return ret
    else:
        return None


def _handle_string(val):
    """
    Replaces Comments: and any newline found.
    Input is a cell of type 'string'.
    """
    return val.replace('Comments: ', '').replace('\r\n', ' ')


def _convert_time(points):
    """Convert time points from HH:MM format to minutes."""
    minutes = []
    for point in points:
        hours, mins = str(point).split(':')
        minutes.append(int(hours) * 60 + int(mins))
    return minutes


def _get_data_labels(sheet, row, col):
    """Locate all column labels for data collected during the experiment."""
    final_column = col
    header_row = _FIELDS['cell_value']['header']['row']
    # Abstract this sort of thing
    header = sheet.cell(row + header_row, final_column).value
    while any(
        header.startswith(label)
        for label in _FIELDS['isotherm_data']['labels']
    ):
        final_column += 1
        header = sheet.cell(row + header_row, final_column).value

    if col == final_column:
        # this means no header exists, can happen in some older files
        # the units might not be standard! TODO should check
        return [
            "Relative Pressure (P/Po)", "Absolute Pressure (kPa)",
            "Quantity Adsorbed (cm³/g STP)", "Elapsed Time (h:min)",
            "Saturation Pressure (kPa)"
        ]

    return [
        sheet.cell(row + header_row, i).value
        for i in range(col, final_column)
    ]


def _get_datapoints(sheet, row, col):
    """Return all collected data points for a given column."""
    rowc = _FIELDS['cell_value']['datapoints']['row']
    # Data can start on two different rows. Try first option and then next row.
    if sheet.cell(row + rowc, col).value:
        start_row = row + rowc
        final_row = row + rowc
    else:
        start_row = row + (rowc + 1)
        final_row = row + (rowc + 1)
    point = sheet.cell(final_row, col).value
    while point:
        final_row += 1
        point = sheet.cell(final_row, col).value
        # sometimes 1-row gaps are left for P0 measurement
        if not point:
            final_row += 1
            point = sheet.cell(final_row, col).value
    return [
        sheet.cell(i, col).value
        for i in range(start_row, final_row)
        if sheet.cell(i, col).value
    ]


def _assign_data(item, field, data, points):
    """
    Add numeric data to the data dictionary.
    For each column of the Excel file, read to the bottom,
    then assign it depending on the label of the column (first point).
    """
    name = next(f for f in field['labels'] if item.startswith(f))
    if field['labels'][name] == 'time':
        data['time'] = _convert_time(points)[1:]
    elif field['labels'][name] == 'loading':
        data['loading'] = points
        data["loading_unit"] = re.split(r'\(|\)', item)[1]
        
    elif field['labels'][name] == 'pressure':
        data['pressure'] = points
        for (u, c) in (
            ('(mmHg', 'torr'),
            ('(torr', 'torr'),
            ('(kPa', 'kPa'),
            ('(bar', 'bar'),
            ('(mbar', 'mbar')
        ):
            if u in item:
                data['pressure_unit'] = c
    elif field['labels'][name] == 'pressure_relative':
        data['pressure_relative'] = points
    elif field['labels'][name] == 'pressure_saturation':
        if (len(points)) == 1:
            data['pressure_saturation'] = points
        else:
            data['pressure_saturation'] = points[1:]
        for (u, c) in (
            ('(mmHg', 'torr'),
            ('(torr', 'torr'),
            ('(kPa', 'kPa'),
            ('(bar', 'bar'),
            ('(mbar', 'mbar'),
        ):
            if u in item:
                data['pressure_unit'] = c
    else:
        raise ValueError(
            f"Label name '{field['labels'][name]}' not recognized."
        )


def _get_errors(sheet, row, col):
    """
    Look for all cells that contain errors.
    (are below a cell labelled primary data).
    """
    field = _FIELDS['primary_data']
    val = sheet.cell(row + field['row'], col + field['column']).value
    if not val:
        return []
    final_row = row + field['row']
    error = sheet.cell(final_row, col + field['column']).value
    while error:
        final_row += 1
        error = sheet.cell(final_row, col + field['column']).value
    return [
        sheet.cell(i, col + field['column']).value
        for i in range(row + field['row'], final_row)
    ]


def _check(data, path):
    """
    Check keys in data and logs a warning if a key is empty.
    Also logs a warning for errors found in file.
    """
    if 'loading' in data:
        empties = (k for k, v in data.items() if not v)
        for empty in empties:
            print(f'No data collected for {empty} in file {path}.')
    if 'errors' in data:
        print('Report file contains warnings:')
        print('\n'.join(data['errors']))
