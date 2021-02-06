from flask import Flask, request
from functools import wraps
import re
import procman
import os

app = Flask(__name__)

proc_man = procman.ProcessManager(os.getcwd(),init_logging=True)


def login_checkauth(username, password):
    env_user = os.getenv('PROCMAN_USER')
    env_pass = os.getenv('PROCMAN_PASSWORD')
    if username == env_user and password == env_pass:
        return True
    else:
        return False

def login_required(f):
    @wraps(f)
    def wrapped_view(**kwargs):
        auth = request.authorization
        if not (auth and login_checkauth(auth.username, auth.password)):
            return ('Unauthorized', 401, {
                'WWW-Authenticate': 'Basic realm="Login Required"'
            })

        return f(**kwargs)

    return wrapped_view


@app.route("/")
def home():
    return "ProcMan web endpoint"

@app.route("/service", methods=["GET", "POST"])
@login_required
def service_manager():
    # handle POST 
    if request.method == "POST":
        content = request.json
        # {'service': 'service_name', 'command': 'operation: start/stop/status'}
        service_name = content.get("service","")
        operation = content.get("command","")
        # execute
        result = None
        if not (service_name and service_name in proc_man.list()):
            return {"result": "service_unknown", "status": "error"}

        if not operation in ("start","stop","status"):
            return {"result": "operation_unknown", "status": "error"}

        if operation == "start":
            result = proc_man.start(service_name)
        elif operation == "stop":
            result = proc_man.stop(service_name)
        elif operation == "status":
            result = proc_man.status(service_name)

        if result:
            return {"result": result, "status": "success"}
        else:
            msg = "false" if result==False else "failed"
            return {"result": msg, "status": "error"}
    # handle GET
    else:
        return {"services": proc_man.list()}
    


