import threading
import time
import uuid

from flask import Flask, render_template, request, jsonify, Response, make_response
from flask_assets import Environment
from webassets import Bundle

import app_service

app = Flask(__name__)
assets = Environment(app)

# SCSS Compilation
scss = Bundle('scss/style.scss', output='css/style.css', filters='libsass')
assets.register('scss_all', scss)
scss.build()  # This compiles SCSS into CSS

message_store = {}
instance_store = {}


@app.route('/')
def hello_world():  # put application's code here
    return render_template('index.html', time=int(time.time()))


@app.route('/chat', methods=['POST'])
def chat():  # put application's code here
    user_message = request.json.get("message")
    stream = request.json.get("stream")
    if stream == "true" or stream:
        stream_enabled = True
    else:
        stream_enabled = False

    resp = make_response()
    session_id = app_service.set_session_id_to_cookie(request, resp)
    instance = app_service.get_or_set_instance(session_id=session_id, instance_store=instance_store, stream_enabled=stream_enabled)
    data = jsonify({'response': '流模式已打开！'}) if stream_enabled else jsonify(
        {'response': instance.chat(user_message)})
    resp.set_data(data.get_data())
    message_store[session_id] = user_message
    return resp


@app.route("/stream/<session_id>", methods=["GET"])
def chat_with_stream(session_id):
    if session_id not in message_store:
        return "Invalid session ID", 400

    instance = instance_store.get(session_id)
    user_message = message_store[session_id]

    return Response(instance.chat(user_message), content_type="text/event-stream")


@app.route('/chat/clear_history', methods=['DELETE'])
def new_topic():
    session_id = request.args['session_id']
    if session_id == 'undefined':
        return jsonify({'response': '你还没有使用过聊天功能，没有历史记录可以删除！'})
    instance = instance_store.get(session_id)
    response = instance.clear_history()
    return jsonify({'response': response})


def background_task():
    while True:
        print("Running background task...")
        time.sleep(5)


if __name__ == '__main__':
    threading.Thread(target=background_task, daemon=True).start()
    app.run(threaded=True)
