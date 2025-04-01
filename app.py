import time

from flask import Flask, render_template, request, jsonify, Response
from flask_assets import Environment
from webassets import Bundle
from chatservice import ChatUtil
from livereload import Server

app = Flask(__name__)
app.config['DEBUG'] = True
assets = Environment(app)

# SCSS Compilation
scss = Bundle('scss/style.scss', output='css/style.css', filters='libsass')
assets.register('scss_all', scss)
scss.build()  # This compiles SCSS into CSS


@app.route('/')
def hello_world():  # put application's code here
    return render_template('index.html', time=int(time.time()))


@app.route('/chat', methods=['POST'])
def chat():  # put application's code here
    user_message = request.json.get('message')
    instance = ChatUtil.get_instance()
    response = instance.chat(user_message)
    return jsonify({'response': response})


@app.route('/chat/new_topic', methods=['DELETE'])
def new_topic():
    instance = ChatUtil.get_instance()
    response = instance.new_topic()
    return jsonify({'response': response})


if __name__ == '__main__':
    if __name__ == "__main__":
        server = Server(app.wsgi_app)
        server.watch('templates/*.html')  # Watch HTML files
        server.watch('static/*.*')  # Watch CSS/JS files
        server.serve(debug=True, port=5000)
