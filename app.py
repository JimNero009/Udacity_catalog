from flask import Flask, request
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from libs.database_setup import Base, Catagory, CatalogItem

app = Flask(__name__)


engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine


DBSession = sessionmaker(bind=engine)
session = DBSession()


new_catagory = Catagory(
    name='Socks',
    id=1
)
new_item = CatalogItem(
    name='test',
    description='I am awesome',
    catagory_id=1
)
session.add(new_catagory)
session.add(new_item)
session.commit()


@app.route('/')
def home():
    try:
        catagory = session.query(Catagory).first()
        items = session.query(CatalogItem).filter_by(catagory_id=catagory.id)
        output = ''
        for i in items:
            output += i.name
        return output
    except AttributeError:
        return 'No data'


@app.route('/<item_group>')
def item_group(item_group):
    return 'TODO'


@app.route('/<item_group>/<item>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def item(item_group, item):
    if request.method == 'POST':
        pass
    elif request.method == 'PUT':
        pass
    if request.method == 'DELETE':
        pass
    if request.method == 'GET':
        return 'TODO'


@app.route('/json')
def json():
    return 'TODO'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)