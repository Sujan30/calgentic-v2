import os
import main
from flask import Flask, send_from_directory, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/prompt/<prompt>')
def onboard(prompt):
    response = main.promptToEvent(prompt)
    eventParams = response['eventParams']
    if(response['action_type'] == 'create'):
        if main.formatEvent(eventParams):
            message = response['eventCompletion']
            return jsonify(message)
        else:
            return jsonify('error')
    #get details about a certain day
    elif response['action_type'] == 'view':
        query_details = response['query_details']
        main.findEvent(query_details=query_details)

        
    


    


