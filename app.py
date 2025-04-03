import time
import uuid

from flask import Flask, render_template, request, jsonify, Response
from flask_assets import Environment
from webassets import Bundle
from chatservice import ChatUtil
app = Flask(__name__)
assets = Environment(app)

# SCSS Compilation
scss = Bundle('scss/style.scss', output='css/style.css', filters='libsass')
assets.register('scss_all', scss)
scss.build()  # This compiles SCSS into CSS

message_store = {}


@app.route('/')
def hello_world():  # put application's code here
    return render_template('index.html', time=int(time.time()))


@app.route('/chat', methods=['POST'])
def chat():  # put application's code here
    user_message = request.json.get("message")
    stream = request.json.get("stream")
    session_id = str(uuid.uuid4())
    message_store[session_id] = user_message

    if stream:
        return jsonify({"response": session_id})
    else:
        instance = ChatUtil.get_instance()
        return jsonify({'response': instance.chat(user_message)})


@app.route("/stream/<session_id>", methods=["GET"])
def chat_with_stream(session_id):
    if session_id not in message_store:
        return "Invalid session ID", 400

    instance = ChatUtil.get_instance(stream=True)
    user_message = message_store[session_id]

    return Response(instance.chat_with_stream(user_message), content_type="text/event-stream")


@app.route('/chat/new_topic', methods=['DELETE'])
def new_topic():
    stream = request.args['stream']
    instance = ChatUtil.get_instance(stream=stream)
    response = instance.new_topic()
    return jsonify({'response': response})


if __name__ == '__main__':
    app.run()
