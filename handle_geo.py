from dadata import Dadata
from geojson2osm import geojson2osm as _geo2osm
import json


# Чтение токена из файла, запрос к Dadata и создание идентификатора из цифр токена
with open('.\\source\\dadata_token', 'r') as tf:
    token = tf.read()
    dadata = Dadata(token)
    digits_in_token = int(''.join([i for i in token if i in '0123456789']))


def close_dadata_socket():
    dadata.close()


def print_line():
    print('-' * 50)


# Выбор из списка опций
def select_option(options_list):
    count = 1
    print_line()
    for i in options_list:
        print(f'    {count}. {i}')
        count += 1
    print_line()
    while True:
        try:
            num = int(input('Выберите один из вариантов: '))
            if 0 < num < count:
                return num - 1
            else:
                raise ValueError
        except ValueError:
            print('Некорректный ввод!')


# Поиск города в Dadata
def find_city(city):
    data = dadata.suggest('address', city)
    city_variants, geo_c_variants = [], []
    for i in data:
        if i['data']['city'] and i['data']['fias_level'] == '1' and city.title() in i['data']['city']:
            return [i['data']['city']], [(i['data']['geo_lon'], i['data']['geo_lat'])]
        if i['data']['city'] and i['data']['fias_level'] == '4' and city.title() in i['data']['city']:
            city_variants.append(i['data']['city'])
            geo_c_variants.append((i['data']['geo_lon'], i['data']['geo_lat']))
    return city_variants, geo_c_variants


# Поиск адреса в Dadata
def find_address(address):
    data = dadata.suggest('address', address)
    address_variants, geo_a_variants = [], []
    for i in data:
        if i['data']['fias_level'] in ['7', '8']:
            address_variants.append(i['value'])
            geo_a_variants.append((i['data']['geo_lon'], i['data']['geo_lat']))
    return address_variants, geo_a_variants


# Создание geojson-файла
def create_geojson(filename, address_list, geo_list):
    template_caption = '{"type": "FeatureCollection","metadata": {"creator": %s},"features": [' \
                       % (hash(digits_in_token))
    template_end = ']}'
    geojson_file = open(f'.\\source\\geojson_osm\\{filename}.geojson', 'w', encoding="utf-8")
    geojson_file.write(template_caption)
    for i in range(len(address_list)):
        description = address_list[i]
        x, y = geo_list[i]
        result_row = '{"type":"Feature","geometry":{"type":"Point","coordinates":[%s,%s]},' \
                     '"properties":{"description":"%s"}},' % (x, y, description)
        if i == len(address_list) - 1:
            result_row = result_row[:-1]
        geojson_file.write(result_row)
    geojson_file.write(template_end)
    geojson_file.close()


# Конвертация geojson-файла в osm
def convert_to_osm(filename):
    geojson_file = open(f'.\\source\\geojson_osm\\{filename}.geojson', encoding='utf-8')
    geojson_data = json.load(geojson_file)
    osm_xml = _geo2osm(geojson_data)
    geojson_file.close()
    with open(f'.\\source\\geojson_osm\\{filename}.osm', 'w', encoding='utf-8') as output_file:
        output_file.write(osm_xml)


# Проверка создателя osm-файла
def check_creator(filename):
    with open(f'.\\source\\geojson_osm\\{filename}.osm', 'r', encoding='utf-8') as file:
        if str(hash(digits_in_token)) in file.read():
            return True
