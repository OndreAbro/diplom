from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.exc import OperationalError
import geoalchemy2
from process_geo import select_option


def connect_to_db():
    while True:
        print('Введите данные для подключения к БД:')
        database = input('Database: ')
        user = input('User: ')
        password = input('Password: ')
        base = declarative_base()
        engine = create_engine(f'postgresql://{user}:{password}@localhost:5432/{database}', echo=False)
        try:
            base.metadata.reflect(engine)
            return Base, engine
        except OperationalError:
            print('Не удается подключиться, используя введенные данные!')


def get_table(base):
    table_list = list(base.metadata.tables.keys())
    if not table_list:
        print('В базе отсутствуют данные!')
        raise ImportError
    table_name = table_list[select_option(table_list)]
    base.metadata.clear()
    return table_name


def get_data(table, base, engine):
    class PostgisGeom(base):
        __tablename__ = table
        id = Column(Integer, primary_key=True)
        description = Column(String)
        geometry = Column(geoalchemy2.Geometry(geometry_type='POINT', srid=4326))

    base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    address_list = [row[0] for row in session.query(PostgisGeom.description).all()]
    geo_query = session.query(geoalchemy2.functions.ST_AsGeoJSON(PostgisGeom.geometry)).all()

    geo_list = [tuple(eval(str(row[0]))['coordinates']) for row in geo_query]

    return address_list, geo_list


def insert_data(address_list, geo_list):
    base, engine = connect_to_db()
    base.metadata.clear()

    class PostgisGeom(base):
        __tablename__ = input('Введите название таблицы: ')
        id = Column(Integer, primary_key=True)
        description = Column(String)
        geometry = Column(geoalchemy2.Geometry(geometry_type='POINT', srid=4326))

    base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    for i in range(len(address_list)):
        insert_geom = geoalchemy2.functions.ST_GeomFromText(f'POINT({geo_list[i][0]} {geo_list[i][1]})')
        session.add(PostgisGeom(description=address_list[i], geometry=insert_geom))
    session.commit()
