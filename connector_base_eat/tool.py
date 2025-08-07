# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
import datetime
from lxml import objectify, etree
import json
import io
import logging
from requests.utils import parse_header_links

_logger = logging.getLogger(__name__)

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None

try:
    import xlsxwriter
except ImportError:
    _logger.debug("Can not import xlsxwriter`.")

DEFAULT_SERVER_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_SERVER_TIME_FORMAT = "%H:%M:%S"
DEFAULT_SERVER_DATETIME_FORMAT = "%s %s" % (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_TIME_FORMAT)


def date_now():
    # we use utc as general now date
    return datetime.datetime.utcnow()


def date_before_hours(hours):
    return date_now() - datetime.timedelta(hours=hours)


def date_diff_days(date1, date2):
    if date1 > date2:
        return False
    date_diff = date2 - date1
    return date_diff.days


def plus_days(date, days):
    return date + datetime.timedelta(days=days)


def build_process_properties(process_config):
    properties = process_config.properties
    items = {}
    if properties:
        for pro in properties.split('\n'):
            item = pro.split(':')
            if len(item) > 1:
                items[item[0]] = item[1]
    return items


def object_map_object(items, source):
    return object_map_object_default(items, source, {})


def object_map_object_default(items, source, target):
    """
    be careful with the target scope, if we set default value target={} in arguments and doesn't pass the
     value, the scope will be bigger, in that case you will get crazy result
     eg:
     for i in range(4):
       result = object_map_object([('a','aa'), ('b', 'bb')], {'a':'a','b':'b'})
       print(result)
       print(id(result))
    :param items:
    :param source:
    :param target:
    :return:
    """
    for item in items:
        if len(item) == 3:
            k, v, c = item
            if isinstance(source, dict):
                value = source.get(k, False)
                if value:
                    target[v] = c(value)
                else:
                    target[v] = False
            else:
                target[v] = c(source[k])
        else:
            k, v = item
            if isinstance(source, dict):
                target[v] = source.get(k, False)
            else:
                target[v] = source[k]
    return target


def xml_attributes_mapping(items, element):
    for key, value in items:
        element.set(key, value)


def xml_build_element_mapping_append(items, parent_node, append_empty):
    """
    item like (k, v) or (k,v,c) or (k,v,c,attrs)
    :param items:
    :param parent_node:
    :param append_empty append the empty value node
    :return:
    """
    for item in items:
        if len(item) == 4:
            key, v, c, attrs = item
        elif len(item) == 3:
            key, v, c = item
            attrs = None
        else:
            key, v = item
            c = str
            attrs = None
        if v:
            etree.SubElement(parent_node, key, attrs).text = c(v)
        else:
            if append_empty:
                etree.SubElement(parent_node, key, attrs).text = ''
            elif attrs is not None and attrs:
                etree.SubElement(parent_node, key, attrs)


def xml_build_element_mapping(items, parent_node):
    xml_build_element_mapping_append(items, parent_node, False)


def parse_date(date_str, fmt='%Y-%m-%dT%H:%M:%S'):
    try:
        return datetime.datetime.strptime(date_str, fmt)
    except:
        return date_str


def format_date(date, fmt='%Y-%m-%dT%H:%M:%S'):
    try:
        return date.strftime(fmt)
    except:
        return False


def float_convert(value):
    if value:
        tools.float_round(float(value), 2)
    return .0


def adjust_data(env, datas, adjust_fun, id_name, line_name):
    ##
    #
    # waiting the next time to process the data, if end, use the outside for to handle
    #
    # #
    reference = False
    line_datas = []
    result_data = []
    for order in datas:
        current_reference = order[id_name]
        if not reference or reference != current_reference:
            reference = current_reference
            merge_order = merge_data(env, line_datas, adjust_fun, line_name)
            if merge_order:
                result_data.append(merge_order)
            line_datas = []
        line_datas.append(order)
    merge_order = merge_data(env, line_datas, adjust_fun, line_name)
    if merge_order:
        result_data.append(merge_order)
    return result_data


def merge_data(env, line_datas, adjust_fun, line_name):
    if not line_datas:
        return False
    if len(line_datas) == 1:
        return adjust_fun(env, line_datas[0])
    first_data = line_datas[0]
    order_lines = []
    for data in line_datas:
        order_lines.extend(data.pop(line_name))
    first_data[line_name] = order_lines
    return adjust_fun(env, first_data)


class ObjectDict(dict):
    """
    Extension of dict to allow accessing keys as attributes.

    Example:
    >>> a = ObjectDict()
    >>> a.fish = 'fish'
    >>> a['fish']
    'fish'
    >>> a['water'] = 'water'
    >>> a.water
    'water'
    """

    def __init__(self, initd=None):
        if initd is None:
            initd = {}
        dict.__init__(self, initd)

    def __getattr__(self, item):
        node = self.__getitem__(item)

        if isinstance(node, dict) and 'value' in node and len(node) == 1:
            return node['value']
        return node

    # if value is the only key in object, you can omit it
    def __setstate__(self, item):
        return False

    def __setattr__(self, item, value):
        self.__setitem__(item, value)

    def getvalue(self, item, value=None):
        """
        Old Python 2-compatible getter method for default value.
        """
        return self.get(item, {}).get('value', value)


def read_excel(source):
    book = xlrd.open_workbook(file_contents=source)
    sheet = book.sheet_by_index(0)
    # emulate Sheet.get_rows for pre-0.9.4
    for rowx, row in enumerate(map(sheet.row, range(sheet.nrows)), 1):
        values = []
        for colx, cell in enumerate(row, 1):
            if cell.ctype is xlrd.XL_CELL_NUMBER:
                is_float = cell.value % 1 != 0.0
                values.append(
                    str(cell.value)
                    if is_float
                    else str(int(cell.value))
                )
            elif cell.ctype is xlrd.XL_CELL_DATE:
                is_datetime = cell.value % 1 != 0.0
                # emulate xldate_as_datetime for pre-0.9.3
                dt = datetime.datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode))
                values.append(
                    dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    if is_datetime
                    else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                )
            elif cell.ctype is xlrd.XL_CELL_BOOLEAN:
                values.append(u'True' if cell.value else u'False')
            elif cell.ctype is xlrd.XL_CELL_ERROR:
                raise ValueError(
                    _("Invalid cell value at row %(row)s, column %(col)s: %(cell_value)s") % {
                        'row': rowx,
                        'col': colx,
                        'cell_value': xlrd.error_text_from_code.get(cell.value, _("unknown error code %s") % cell.value)
                    }
                )
            else:
                values.append(cell.value)
        if any(x for x in values if x.strip()):
            yield values


def read_csv(source):
    csv_iterator = tools.pycompat.csv_reader(
        io.BytesIO(source),
        quotechar='"',
        delimiter=',')
    return (
        row for row in csv_iterator
        if any(x for x in row if x.strip())
    )


def sheet_rows_to_iterator(rows):
    headers = next(rows)
    result = []
    for row in rows:
        row_item = {}
        col_idx = 0
        for header in headers:
            row_item[header] = row[col_idx]
            col_idx = col_idx + 1
        result.append(row_item)
    return result


def xml_to_object(source):
    return objectify.fromstring(source)


def object_to_xml(source):
    root = _dict_to_xml(source, False)
    return etree.tostring(root)


def _dict_to_xml(source, parent=False):
    if not source:
        return False
    for name, values in source.items():
        if isinstance(values, (list, tuple)):
            if not parent:
                parent = etree.Element(name)
            leaf_name = name[:len(name) - 1]
            for value in values:
                leaf_ele = etree.SubElement(parent, leaf_name)
                _dict_to_xml(value, leaf_ele)
        elif isinstance(values, dict):
            if not parent:
                parent = etree.Element(name)
            _dict_to_xml(values, parent)
        else:
            leaf_ele = etree.SubElement(parent, name)
            leaf_ele.text = str(values)
    return parent


def json_to_object(source):
    return json.loads(source)


def object_to_json(source):
    return json.dumps(source)


def xlsx_to_object(source):
    rows = read_excel(source)
    return sheet_rows_to_iterator(rows)


def object_to_xlsx(source):
    fp = io.BytesIO()
    with xlsxwriter.Workbook(fp, {'in_memory': True}) as workbook:
        worksheet = workbook.add_worksheet()
        headers = False
        for row_index, item in enumerate(source):
            if not headers:
                headers = item.keys()
                for col, field_name in enumerate(headers):
                    worksheet.write(0, col, field_name)
            data = item.values()
            for cell_index, cell_value in enumerate(data):
                if isinstance(cell_value, (list, tuple)):
                    cell_value = tools.pycompat.to_text(cell_value)
                # set to empty instead of the false
                if not cell_value:
                    cell_value = ''
                worksheet.write(row_index + 1, cell_index, cell_value)
    fp.seek(0)
    return fp


def csv_to_object(source):
    rows = read_csv(source)
    return sheet_rows_to_iterator(rows)


def object_to_csv(source):
    fp = io.BytesIO()
    writer = tools.pycompat.csv_writer(fp, quoting=1)
    headers = False
    for item in source:
        if not headers:
            headers = item.keys()
            writer.writerow(headers)
        data = item.values()
        row = []
        for d in data:
            # Spreadsheet apps tend to detect formulas on leading =, + and -
            if isinstance(d, str) and d.startswith(('=', '-', '+')):
                d = "'" + d
            row.append(tools.pycompat.to_text(d))
        writer.writerow(row)
    fp.seek(0)
    return fp


def object_to_object(source):
    return source


CONVERT_DICT = {'xml_': xml_to_object, 'json_': json_to_object, 'csv_': csv_to_object, 'xlsx_': xlsx_to_object,
                '_xml': object_to_xml, '_json': object_to_json, '_csv': object_to_csv, '_xlsx': object_to_xlsx,
                '_object': object_to_object, 'object_': object_to_object}


def build_import_code_context(tool, env, source, mapper):
    return {'tool': tool, 'env': env, 'source': source, 'mapper': mapper}


def parse_header_link(header):
    lnk = {}
    if header:
        links = parse_header_links(header)
        for link in links:
            key = link.get('rel') or link.get('url')
            lnk[key] = link
    return lnk
