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
            return choice if 0 < choice < 8 else int('')
        except ValueError:
            print('Некорректный ввод, требуется ввести число от 1 до 7!')


    def get_file(source_dir):
        file_list = [file for file in os.listdir(source_dir)]
        if not file_list:
            print('Не найдено соответствующих файлов!')
            raise ImportError
        print('\nВыберите файл: ')
        return file_list[select_option(file_list)]


    def get_city():
        city_variants, geo_variants = [], []
        while not city_variants:
            city_variants, geo_variants = find_city(input('Введите название города: '))
            if not city_variants:
                not_found_menu()
        num = select_option(city_variants) if len(city_variants) > 1 else 0
        return city_variants[num], geo_variants[num]


    def set_filename():
        return datetime.now().strftime('%Y-%m-%d %H_%M_%S')


    def not_found_menu():
        answer = input('Данные не найдены! Попробовать снова? [Д/Н]:').upper()
        if answer != 'Д':
            if answer == 'Н':
                raise ImportError
            else:
                not_found_menu()


    def repeat_menu(text):
        answer = input(text).upper()
        if answer != 'Д':
            if answer == 'Н':
                raise AssertionError
            else:
                repeat_menu(text)


    def suggest_to_save():
        while True:
            answer = input('Сохранить список адресов в базу данных? [Д/Н]:').upper()
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


    def create_geo_files(filename, address_list, geo_list):
        create_geojson(filename, address_list, geo_list)
        convert_to_osm(filename)

    def remove_temp_files():
        os.remove('.\\source\\geojson_osm\\temp.geojson')
        os.remove('.\\source\\geojson_osm\\temp.osm')


    def create_route_map(filename, city_name, city_geo, points):
        tsp_list = solve_tsp(points)
        print('Построение маршрутов...')
        routes_to_nearest_node, routes_between_points = build_optimal_routes(city_name, points, tsp_list)
        print('Сохранение карты...')
        create_map(filename, city_geo, points, routes_to_nearest_node, routes_between_points)
        os.system(f'start .\\source\\maps\\"{filename}".html')


    def handle_first_command(source):

        try:
            working_file = source + get_file(source)

            city_name, city_geo = get_city()

            address_list, geo_list = handle_file(city_name, working_file)
            depot_address, depot_geo = manual_input(city_name, 'Введите ваш текущий адрес: ')
            address_list, geo_list = [depot_address] + address_list, [depot_geo] + geo_list

            city_name = translate_city(city_name)
            save_graphml_to_file(city_name)

            filename = set_filename()

            if suggest_to_save():
                insert_to_db(filename, address_list[1:], geo_list[1:])

            create_geo_files(filename, address_list, geo_list)

            points = load_geom(filename)

            create_route_map(filename, city_name, city_geo, points)

        except ImportError:
            print_line()


    def handle_second_command(source):

        try:
            working_file = get_file(source).split('.')[0]
            if f'{working_file}.osm' not in os.listdir(source):
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

            create_route_map(set_filename(), city_name, city_geo, points)

        except ImportError:
            print_line()


    def handle_third_command():

        try:

            address_list, geo_list = handle_db()

            city_name, city_geo = get_city()
            while not city_name + ',' in address_list[0]:
                print('Введенный город не совпадает с указанным в базе данных!')
                city_name, city_geo = get_city()

            depot_address, depot_geo = manual_input(city_name, 'Введите ваш текущий адрес: ')
            address_list, geo_list = [depot_address] + address_list, [depot_geo] + geo_list

            city_name = translate_city(city_name)
            save_graphml_to_file(city_name)

            filename = set_filename()

            create_geo_files(filename, address_list, geo_list)

            points = load_geom(filename)

            create_route_map(filename, city_name, city_geo, points)

        except ImportError:
            print_line()


    def handle_fourth_command():

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
                repeat_menu('Добавить еще один адрес? [Д/Н]:')

        except ImportError:
            print_line()

        except AssertionError:
            filename = set_filename()

            if suggest_to_save():
                insert_to_db(filename, address_list[1:], geo_list[1:])

            create_geo_files(filename, address_list, geo_list)

            points = load_geom(filename)

            create_route_map(filename, city_name, city_geo, points)


    def handle_fifth_command(source):

        try:
            while True:
                working_file = get_file(source).split('.')[0]
                if f'{working_file}.osm' not in os.listdir(source):
                    convert_to_osm(working_file)

                points = load_geom(working_file)
                print(points)
                print_line()

                repeat_menu('Просмотреть другой файл? [Д/Н]:')

        except (ImportError, AssertionError):
            print_line()

    def handle_sixth_command():

        try:
            while True:
                address_list, geo_list = handle_db()

                create_geo_files('temp', address_list, geo_list)

                points = load_geom('temp')
                print(points)
                print_line()

                remove_temp_files()

                repeat_menu('Просмотреть другую таблицу? [Д/Н]:')

        except (ImportError, AssertionError):
            print_line()

    def main():
        choice = main_menu()

        while choice != 7:

            if choice == 1:

                handle_first_command('.\\source\\xls\\')

            elif choice == 2:

                handle_second_command('.\\source\\geojson_osm\\')

            elif choice == 3:

                handle_third_command()

            elif choice == 4:

                handle_fourth_command()

            elif choice == 5:

                handle_fifth_command('.\\source\\geojson_osm\\')

            elif choice == 6:

                handle_sixth_command()

            choice = main_menu()

        close_dadata_socket()


    main()

else:
    os.system('.\\venv\\Scripts\\python.exe main.py')
