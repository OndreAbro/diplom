from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, create_engine, sql
from sqlalchemy.exc import OperationalError
import geoalchemy2
from process_geo import select_option


with open('.\\source\\db_pass', 'r') as db:
    user, password, database = db.read().split(' ')


def connect_to_db():
    base = declarative_base()
    engine = create_engine(f'postgresql://{user}:{password}@localhost:5432/{database}', echo=False)
    try:
        base.metadata.reflect(engine)
        return base, engine
    except OperationalError:
        print('Не удается подключиться, используя введенные данные!')


def check_postgis_extension(engine):
    with engine.connect() as con:
        result = con.execute(sql.text("SELECT * FROM pg_extension WHERE extname LIKE 'postgis%'"))
        ext_list = result.all()
        if not ext_list:
            con.execute(sql.text("CREATE EXTENSION postgis_topology CASCADE"))
            con.commit()


def get_table(base):
    table_list = [key for key in base.metadata.tables.keys() if key not in ('spatial_ref_sys', 'topology', 'layer')]
    if not table_list:
        print('В базе отсутствуют данные!')
        raise ImportError
    print('\nВыберите таблицу:')
    table_name = table_list[select_option(table_list)]
    base.metadata.clear()
    return table_name


def return_from_db(table, base, engine):
    class PostgisGeom(base):
        __tablename__ = table
        id = Column(Integer, primary_key=True)
        description = Column(String)
        geometry = Column(geoalchemy2.Geometry(geometry_type='POINT', srid=4326))

    base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    address_list = [row[0] for row in session.query(PostgisGeom.description).all()]
    geo_query = session.query(geoalchemy2.functions.ST_AsGeoJSON(PostgisGeom.geometry)).all()

    geo_list = [tuple(json.loads(str(row[0])).get('coordinates')) for row in geo_query]

    return address_list, geo_list


def insert_data(tablename, address_list, geo_list):
    base, engine = connect_to_db()
    base.metadata.clear()
    check_postgis_extension(engine)

    class PostgisGeom(base):
        __tablename__ = tablename
        id = Column(Integer, primary_key=True)
        description = Column(String)
        geometry = Column(geoalchemy2.Geometry(geometry_type='POINT', srid=4326))

    base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    for i in range(len(address_list)):
        insert_geom = geoalchemy2.functions.ST_GeomFromText(f'POINT({geo_list[i][0]} {geo_list[i][1]})')
        session.add(PostgisGeom(description=address_list[i], geometry=insert_geom))
    session.commit()
