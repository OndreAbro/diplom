import sys
import os

if 'venv' in sys.executable:
    from process_geo import *
    from process_graph import *
    from process_map import *
    from process_tsp import *
    from process_xls import *
    from process_db import *
    from datetime import datetime


    def main_menu():
        print('''Здравствуйте! Для начала работы с геокодером выберите действие, которое требуется выполнить:
              1. Загрузить данные с файла xls.
              2. Загрузить данные с файла geojson/osmxml.
              3. Загрузить данные из БД.
              4. Ввести данные вручную.
              5. Просмотреть файл geojson/osmxml.
              6. Просмотреть содержимое БД.
              7. Выйти из программы''')
        try:
            choice = int(input('Введите число от 1 до 7, обозначающее пункт меню: '))
            return choice
        except ValueError:
            print('Некорректный ввод, требуется ввести число от 1 до 7!')


    def get_file(source_dir):
        file_list = [file for file in os.listdir(source_dir)]
        if not file_list:
            print('Не найдено соответствующих файлов!')
            raise ImportError
        print('\nВыберите файл: ')
        return file_list[select_option(file_list)]


    def set_filename():
        return datetime.now().strftime('%Y-%m-%d %H_%M_%S')


    def not_found_menu():
        answer = input('Данные не найдены! Попробовать снова? [Д/Н]:').upper()
        if answer != 'Д':
            if answer == 'Н':
                raise ImportError
            else:
                not_found_menu()


    def manual_input_repeat():
        answer = input('Добавить еще один адрес? [Д/Н]:').upper()
        if answer != 'Д':
            if answer == 'Н':
                raise AssertionError
            else:
                manual_input_repeat()


    def repeat_menu(text):
        answer = input(text).upper()
        if answer != 'Д':
            if answer == 'Н':
                raise AssertionError
            else:
                repeat_menu(text)


    def suggest_to_save(text):
        while True:
            answer = input(text).upper()
            if answer == 'Д':
                return True
            elif answer == 'Н':
                return False


    def manual_input(city, text):
        while True:
            address = city + ' ' + input(text)
            address_variants, geo_variants = find_address(address)
            if address_variants:
                num = select_option(address_variants) if len(address_variants) > 1 else 0
                return address_variants[num], geo_variants[num]
            else:
                not_found_menu()


    def get_city():
        city_variants, geo_variants = [], []
        while not city_variants:
            city_variants, geo_variants = find_city(input('Введите название города: '))
            if not city_variants:
                not_found_menu()
        num = select_option(city_variants) if len(city_variants) > 1 else 0
        return city_variants[num], geo_variants[num]


    def translate_city(city_name):
        with open('.\\source\\tdict.txt', 'r', encoding='utf-8') as tdict:
            return eval(tdict.read())[city_name]


    def main():
        choice = main_menu()
        while choice != 7:

            if choice == 1:
                source = '.\\source\\xls\\'
                try:
                    working_file = source + get_file(source)
                    city_name, city_geo = get_city()
                    add_city(city_name, working_file)
                    fill_coordinates(working_file)

                    depot_address, depot_geo = manual_input(city_name, 'Введите ваш текущий адрес: ')
                    address_list, geo_list = [depot_address], [depot_geo]
                    addresses_from_file, geo_from_file = return_from_file(working_file)
                    address_list.extend(addresses_from_file)
                    geo_list.extend(geo_from_file)

                    city_name = translate_city(city_name)
                    save_graphml_to_file(city_name)

                    filename = set_filename()
                    if suggest_to_save('Сохранить список адресов в базу данных? [Д/Н]:'):
                        insert_data(filename, address_list[1:], geo_list[1:])

                    create_geojson(filename, address_list, geo_list)
                    print('Создание файла .geojson...')
                    convert_to_osm(filename)
                    print('Конвертация в osmxml...')
                    points = load_geom(filename)
                    tsp_list = solve_tsp(points)
                    print('Построение маршрутов...')
                    routes_to_nearest_node, routes_between_points = build_optimal_routes(city_name, points, tsp_list)
                    print('Сохранение карты...')
                    create_map(filename, city_geo, points, routes_to_nearest_node, routes_between_points)
                    os.system('start .\\source\\maps\\test_map.html')


                except ImportError:
                    print_line()

            elif choice == 2:
                source = '.\\source\\geojson_osm\\'
                try:
                    working_file = get_file(source).split('.')[0]
                    if f'{working_file}.osm' not in os.listdir('.\\source\\geojson_osm\\'):
                        convert_to_osm(working_file)

                    points = load_geom(working_file)

                    city_name, city_geo = get_city()
                    while not city_name + ',' in points.description[0]:
                        print('Введенный город не совпадает с указанным в файле!')
                        city_name, city_geo = get_city()
                    depot_address, depot_geo = manual_input(city_name, 'Введите ваш текущий адрес: ')

                    city_name = translate_city(city_name)
                    save_graphml_to_file(city_name)

                    points = change_depot(points, depot_address, depot_geo) if check_creator(working_file) \
                        else add_depot(points, depot_address, depot_geo)

                    tsp_list = solve_tsp(points)
                    print('Построение маршрутов...')
                    routes_to_nearest_node, routes_between_points = build_optimal_routes(city_name, points, tsp_list)
                    print('Сохранение карты...')
                    create_map(set_filename(), city_geo, points, routes_to_nearest_node, routes_between_points)
                    os.system('start .\\source\\maps\\test_map.html')

                except ImportError:
                    print_line()

            elif choice == 3:

                try:
                    base, engine = connect_to_db()
                    table = get_table(base)
                    addresses_from_db, geo_from_db = get_data(table, base, engine)

                    city_name, city_geo = get_city()
                    while not city_name + ',' in addresses_from_db[0]:
                        print('Введенный город не совпадает с указанным в базе данных!')
                        city_name, city_geo = get_city()

                    depot_address, depot_geo = manual_input(city_name, 'Введите ваш текущий адрес: ')
                    address_list, geo_list = [depot_address], [depot_geo]
                    address_list.extend(addresses_from_db)
                    geo_list.extend(geo_from_db)

                    city_name = translate_city(city_name)
                    save_graphml_to_file(city_name)

                    filename = set_filename()
                    create_geojson(filename, address_list, geo_list)
                    print('Создание файла .geojson...')
                    convert_to_osm(filename)
                    print('Конвертация в osmxml...')
                    points = load_geom(filename)
                    tsp_list = solve_tsp(points)
                    print('Построение маршрутов...')
                    routes_to_nearest_node, routes_between_points = build_optimal_routes(city_name, points, tsp_list)
                    print('Сохранение карты...')
                    create_map(filename, city_geo, points, routes_to_nearest_node, routes_between_points)
                    os.system('start .\\source\\maps\\test_map.html')

                except ImportError:
                    print_line()

            elif choice == 4:
                try:
                    city_name, city_geo = get_city()
                    city_name = translate_city(city_name)
                    save_graphml_to_file(city_name)
                    depot_address, depot_geo = manual_input(city_name, 'Введите ваш текущий адрес: ')
                    address_list, geo_list = [depot_address], [depot_geo]
                    while True:
                        address, geo = manual_input(city_name, 'Введите адрес объекта: ')
                        address_list.append(address)
                        geo_list.append(geo)
                        manual_input_repeat()
                except ImportError:
                    print_line()
                except AssertionError:
                    filename = set_filename()
                    if suggest_to_save('Сохранить список адресов в базу данных? [Д/Н]:'):
                        insert_data(filename, address_list[1:], geo_list[1:])
                    create_geojson(filename, address_list, geo_list)
                    print('Создание файла .geojson...')
                    convert_to_osm(filename)
                    print('Конвертация в osmxml...')
                    points = load_geom(filename)
                    tsp_list = solve_tsp(points)
                    print('Построение маршрутов...')
                    routes_to_nearest_node, routes_between_points = build_optimal_routes(city_name, points, tsp_list)
                    print('Сохранение карты...')
                    create_map(filename, city_geo, points, routes_to_nearest_node, routes_between_points)
                    os.system('start .\\source\\maps\\test_map.html')


            elif choice == 5:
                source = '.\\source\\geojson_osm\\'
                try:
                    while True:
                        working_file = get_file(source).split('.')[0]
                        if f'{working_file}.osm' not in os.listdir('.\\source\\geojson_osm\\'):
                            convert_to_osm(working_file)
                        points = load_geom(working_file)
                        print(points)
                        print_line()
                        repeat_menu('Просмотреть другой файл? [Д/Н]:')
                except (ImportError, AssertionError):
                    print_line()

            elif choice == 6:
                try:
                    while True:
                        base, engine = connect_to_db()
                        table = get_table(base)
                        address_list, geo_list = get_data(table, base, engine)
                        filename = 'temp'
                        create_geojson(filename, address_list, geo_list)
                        convert_to_osm(filename)
                        points = load_geom(filename)
                        print(points)
                        os.remove('.\\source\\geojson_osm\\temp.geojson')
                        os.remove(f'.\\source\\geojson_osm\\temp.osm')
                        print_line()
                        repeat_menu('Просмотреть другую таблицу? [Д/Н]:')
                except (ImportError, AssertionError):
                    print_line()

            choice = main_menu()
        close_dadata_socket()

    main()

else:
    os.system('.\\venv\\Scripts\\python.exe main.py')
