import time

from flask import Flask, render_template, request, jsonify, Response, make_response
from flask_assets import Environment
from webassets import Bundle

import app_service
from octane_service import OctaneService

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
    stream_enabled = True if stream == "true" else False
    instance = OctaneService.get_instance()
    data = jsonify({'response': instance.chat(user_message)})
    resp = make_response(data)
    app_service.set_or_check_session_id(request, resp)
    session_id = app_service.set_or_check_session_id(request=request, response=resp)
    instance_store[session_id] = instance
    message_store[session_id] = user_message
    return resp


@app.route("/stream/<session_id>", methods=["GET"])
def chat_with_stream(session_id):
    if session_id not in message_store:
        return "Invalid session ID", 400

    instance = instance_store.get(session_id)
    user_message = message_store[session_id]

    return Response(instance.chat_with_streaming(user_message), content_type="text/event-stream")


@app.route('/chat/clear_history', methods=['DELETE'])
def new_topic():
    session_id = request.args['session_id']
    instance = instance_store.get(session_id)
    response = instance.clear_history()
    return jsonify({'response': response})


if __name__ == '__main__':
    app.run()
