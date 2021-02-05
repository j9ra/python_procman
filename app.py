from flask import Flask, request
from datetime import datetime
import re
import procman
import os

app = Flask(__name__)

proc_man = procman.ProcessManager(os.getcwd(),init_logging=True)

@app.route("/")
def home():
    return "ProcMan web endpoint"

@app.route("/service", methods=["GET", "POST"])
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
    
