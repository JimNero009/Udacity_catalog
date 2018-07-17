import json
import string
import random
import httplib2
from datetime import datetime
from flask import Flask, request, render_template, session, make_response, flash
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from functools import wraps
from libs.database_setup import Base, Catagory, CatalogItem, User


app = Flask(__name__, template_folder='./static/templates')


engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine


DBSession = sessionmaker(bind=engine)
db_session = DBSession()


new_catagory = Catagory(
    name='Socks',
    id=1
)
new_item = CatalogItem(
    name='test',
    description='I am awesome',
    catagory_id=1,
    added=datetime.now(),
    user_id=1
)
db_session.add(new_catagory)
db_session.add(new_item)
db_session.commit()


def create_user(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email']
    )
    db_session.add(newUser)
    db_session.commit()
    user = db_session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_user_id(email):
    try:
        user = db_session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def get_user_id_that_created_item(name):
    try:
        item = db_session.query(CatalogItem).filter_by(name=name).one()
        return item.user_id
    except:
        return None


@app.route('/login')
def show_login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/fblogin', methods=['POST'])
def fb_login():
    if request.args.get('state') != session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data


    app_id = json.loads(open('static/data/fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('static/data/fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    session['provider'] = 'facebook'
    session['username'] = data["name"]
    session['email'] = data["email"]
    session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    session['access_token'] = token

    # see if user exists
    user_id = get_user_id(session['email'])
    if not user_id:
        user_id = create_user(session)
    session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += session['username']
    output += '!</h1>'

    flash("Now logged in as %s" % session['username'])
    return output


@app.route('/fblogout')
def fb_logout():
    facebook_id = session['facebook_id']
    # The access token must me included to successfully logout
    access_token = session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    h.request(url, 'DELETE')
    return "You have been logged out"


def is_logged(endpoint_func):
    @wraps(endpoint_func)
    def check_is_logged(*args, **kwargs):
        if 'username' not in session or 'email' not in session:
            return "You need to log in first"
        if 'item' in kwargs:
            if get_user_id(session["email"] != get_user_id_that_created_item(kwargs['item'])):
                return "You are not the owner of the item"
        return endpoint_func(*args, **kwargs)
    return check_is_logged


@app.route('/')
def home():
    # this should show login/logout button
    # and list of catogories and latest added items
    return 'HOME'


@app.route('/catalog/<item_group>/<item>')
def get_item(item_group, item):
    # this should show the item description
    return 'ITEM DESCRIPTION'


@app.route('/catalog/<item>/edit')
@is_logged
def edit_item(item):
    # this show a form to edit an item
    return 'ITEM EDIT'


@app.route('/catalog/<item>/delete')
@is_logged
def delete_item(item):
    # this show a form to edit an item
    return 'DELETE AN ITEM'


@app.route('/catalog.json')
def catalog_json():
    return 'TODO'


if __name__ == '__main__':
    app.secret_key = 'jim_is_the_best'
    app.run(host='0.0.0.0', port=8000, debug=True)