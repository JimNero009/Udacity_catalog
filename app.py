from flask import Flask, request
app = Flask(__name__)


@app.route('/')
def home():
    return 'Hello!'


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