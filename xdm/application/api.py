from xdm.helper import as_json
from flask import Blueprint, current_app, request

api = Blueprint('api', __name__, url_prefix="/api")

@api.route('/index')
@as_json
def index():
    return 'index', None


@api.route('/ping')
@as_json
def ping():
    return 'pong', None


@api.route('/start_task', methods=['POST'])
@as_json
def start_task():
    body = request.json
    task_callable = current_app.get_task(body["task"])
    task = task_callable.delay(
        current_app.db,
        *body.get("args", tuple()),
        **body.get("kwargs", {})
    )

    return {'task_id': task.id}


@api.route('/task/<name>/<task_id>', methods=['GET'])
@as_json
def get_task(name, task_id):
    task = current_app.get_task_status(name, task_id)
    return {'task_state': task.state}
