from openpyxl import load_workbook
from process_geo import *


def set_row(num):
    return f'A{num}'


def add_city(city, filename):
    wb = load_workbook(filename)
    sheet = wb.active
    for row in range(1, sheet.max_row + 1):
        cell = set_row(row)
        if not sheet[cell].value:
            continue
        if city + ',' not in sheet[cell].value:
            sheet[cell] = city + ',' + sheet[cell].value
    wb.save(filename)


def fill_coordinates(filename):
    wb = load_workbook(filename)
    sheet = wb.active
    not_found_addr = 0
    print('Поиск координат по адресу...')
    for row in range(1, sheet.max_row + 1):
        cell = set_row(row)
        if not sheet[cell].value:
            continue
        print(f'Поиск: ' + sheet[cell].value)
        address_variants, geo_variants = find_address(sheet[cell].value)
        if address_variants:
            num = select_option(address_variants) if len(address_variants) > 1 else 0
            sheet[cell] = geo_variants[num][1]
            sheet[cell] = geo_variants[num][0]
            sheet[cell] = address_variants[num]
        else:
            print('По адресу: ' + sheet[row].value + ' данные не найдены!')
            not_found_addr += 1
    wb.save(filename)
    print(f'Общее число объектов на входе: {sheet.max_row}\nЧисло объектов на выходе: {sheet.max_row - not_found_addr}')


def return_from_file(filename):
    address_list, geo_list = [], []
    wb = load_workbook(filename)
    sheet = wb.active
    for cell in range(1, sheet.max_row + 1):
        address = sheet[f'E{cell}'].value
        x = sheet[f'C{cell}'].value
        y = sheet[f'B{cell}'].value
        if address:
            address_list.append(address)
        if x and y:
            geo_list.append((x, y))
    return address_list, geo_list
