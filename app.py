import json
import string
import random
import httplib2
import requests
from datetime import datetime
from flask import (
    Flask, request, render_template,
    session, make_response, jsonify,
    url_for, redirect
)
from sqlalchemy import create_engine, MetaData, asc, update
from sqlalchemy.orm import sessionmaker
from functools import wraps
from libs.database_setup import Base, Catagory, CatalogItem, User


app = Flask(__name__, template_folder='./static/templates')


engine = create_engine('sqlite:///catalog.db?check_same_thread=False')
Base.metadata.bind = engine


DBSession = sessionmaker(bind=engine)
db_session = DBSession()


new_catagory = Catagory(
    name='Socks'
)
new_item = CatalogItem(
    name='Item1',
    description='I am awesome',
    catagory_id=1,
    added=datetime.now(),
    user_id=1
)
db_session.add(new_catagory)
db_session.add(new_item)
db_session.commit()


def create_user(user_dict):
    newUser = User(
        name=user_dict['username'],
        email=user_dict['email']
    )
    db_session.add(newUser)
    db_session.commit()
    user = db_session.query(User).filter_by(email=user_dict['email']).one()
    return user.id


def get_user_id(email):
    try:
        user = db_session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None


def get_user_id_that_created_item(name):
    try:
        item = db_session.query(CatalogItem).filter_by(name=name).one()
        return item.user_id
    except Exception:
        return None


@app.route('/login')
def show_login():
    state = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits
        ) for x in range(32)
    )
    session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/googlelogin', methods=['POST'])
def google_login():
    data = request.form
    if request.args.get('state') != session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    user = dict()
    user['provider'] = 'google'
    user['username'] = data.get("username", "")
    user['email'] = data.get("email", "")
    user['google_id'] = data.get("id", "")
    user['access_token'] = data.get("access_token", "")

    # see if user exists
    user_id = get_user_id(user['email'])
    if not user_id:
        user_id = create_user(user)
    user['user_id'] = user_id
    session['user'] = user
    return '<h1>Welcome, {} !</h1>'.format(user['username'])


@app.route('/googlelogout')
def google_logout():
    user = session.get('user', {})
    requests.post(
        'https://accounts.google.com/o/oauth2/revoke',
        params={'token': user.get('access_token')},
        headers={'content-type': 'application/x-www-form-urlencoded'}
    )
    session.pop('user', None)
    return redirect(url_for('home'))


def is_logged(endpoint_func):
    @wraps(endpoint_func)
    def check_is_logged(*args, **kwargs):
        if 'user' not in session:
            return "You need to log in first"
        user_id = get_user_id(session['user']["email"])
        if 'item' in kwargs:
            user_id_item = get_user_id_that_created_item(kwargs['item'])
        if 'item' in kwargs and user_id != user_id_item:
            return "You are not the owner of the item"
        return endpoint_func(*args, **kwargs)
    return check_is_logged


@app.route('/')
def home():
    catagories = db_session.query(Catagory).order_by(asc(Catagory.name))
    items = db_session.query(CatalogItem).order_by(asc(CatalogItem.name))
    return render_template(
        'index.html',
        catagories=catagories,
        items=items,
        logged='user' in session
    )


@app.route('/<catagory>/items')
def items_by_catagory(catagory):
    '''
    Displays all items in a catagory
    params:
    @catagory: str - the catagory to list
    '''
    catagories = db_session.query(Catagory).order_by(asc(Catagory.name))
    catagory_id = (
        db_session.query(Catagory)
        .filter(Catagory.name == catagory)
        .one()
        .id
    )
    items = (
        db_session.query(CatalogItem)
        .order_by(asc(CatalogItem.name))
        .filter(CatalogItem.catagory_id == catagory_id)
    )
    return render_template(
        'catagory_list.html',
        selected_catagory=catagory,
        catagories=catagories,
        items=items
    )


@app.route('/catalog/<item_group>/<item>')
def view_item(item_group, item):
    '''
    Displays an item
    params:
    @item_group: str - the item catagory
    @item: str - the name of the item
    '''
    selected_item = (
        db_session.query(CatalogItem)
        .filter(Catagory.name == item_group)
        .filter(CatalogItem.name == item)
        .one()
    )
    return render_template(
        'view_item.html',
        item=selected_item,
        logged='user' in session
    )


@app.route('/catalog/<item>/edit', methods=['GET', 'POST'])
@is_logged
def edit_item(item):
    '''
    Edit an item
    params:
    @item: str - the item to edit
    '''
    if request.method == 'POST':
        catagory = (
            db_session.query(Catagory)
            .filter(Catagory.name == request.form['catagory'])
            .first()
        )
        if not catagory:
            catagory = Catagory(
                name=request.form['catagory']
            )
            db_session.add(catagory)
            db_session.commit()
        item_to_update = (
            db_session.query(CatalogItem)
            .filter_by(id=request.form['id'])
            .first()
        )
        item_to_update.name = request.form['name']
        item_to_update.description = request.form['description']
        item_to_update.catagory_id = catagory.id
        db_session.commit()
        return redirect(url_for('home'))
    else:
        selected_item = (
            db_session.query(CatalogItem)
            .filter(CatalogItem.name == item)
            .one()
        )
        return render_template(
            'edit_item.html',
            item=selected_item
        )


@app.route('/catalog/<item>/delete', methods=['GET', 'POST'])
@is_logged
def delete_item(item):
    '''
    Delete an item
    params:
    @item: str - the item to delete
    '''
    if request.method == 'POST':
        # delete item and catagory if it is now empty
        catagory_id = (
            db_session.query(CatalogItem)
            .filter(CatalogItem.id == request.form['id'])
            .one()
            .catagory_id
        )
        (
            db_session.query(CatalogItem)
            .filter(CatalogItem.id == request.form['id'])
            .delete()
        )
        db_session.commit()
        try:
            (
                db_session.query(CatalogItem)
                .filter(CatalogItem.id == catagory_id)
                .first()
            )
        except Exception:
            (
                db_session.query(Catagory)
                .filter(Catagory.id == catagory_id)
                .delete()
            )
            db_session.commit()
        return redirect(url_for('home'))
    else:
        selected_item = (
            db_session.query(CatalogItem)
            .filter(CatalogItem.name == item)
            .one()
        )
        return render_template(
            'delete_item.html',
            item=selected_item
        )


@app.route('/catalog/additem/', methods=['GET', 'POST'])
@is_logged
def add_item():
    '''
    Add an item to the catalog
    '''
    if request.method == 'POST':
        # add item and create catagory if needed
        catagory = (
            db_session.query(Catagory)
            .filter(Catagory.name == request.form['catagory'])
            .first()
        )
        if not catagory:
            catagory = Catagory(
                name=request.form['catagory']
            )
            db_session.add(catagory)
            db_session.commit()
        new_item = CatalogItem(
            name=request.form['name'],
            description=request.form['description'],
            catagory_id=catagory.id,
            added=datetime.now(),
            user_id=session['user']['user_id']
        )
        db_session.add(new_item)
        db_session.commit()
        return redirect(url_for('home'))
    else:
        return render_template(
            'add_item.html'
        )


@app.route('/<item>/catalog.json')
def catalog_json(item):
    '''
    Get JSON rep of one item
    params:
    @item: str - the name of the item
    '''
    item = (
        db_session.query(CatalogItem)
        .filter(CatalogItem.name == item)
        .one()
    )
    return jsonify(items=item.serialize)


if __name__ == '__main__':
    app.secret_key = 'jim_is_the_best'
    app.run(host='0.0.0.0', port=8000, debug=True)
