from flask import Blueprint

index = Blueprint('XDM', __name__, template_folder='../html')

@index.route('/')
def show():
    return "hello world"
