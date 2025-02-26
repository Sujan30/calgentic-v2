import json
import os
import main
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

app = Flask(__name__)


CORS(app, resources={r"/*": {"origins":["http://localhost:5173","http://127.0.0.1:5000" ]}})

main.calendarAuth()

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/prompt/<prompt>', methods=['GET'])
def onboard(prompt):
    response = main.promptToEvent(prompt)
    
    # Check if response contains an error
    if isinstance(response, dict) and 'error' in response:
        return jsonify(response), 400
    
    # No need to parse JSON again since promptToEvent already returns a dictionary
    response_dict = response
    
    if 'action_type' not in response_dict:
        return jsonify({"error": "Missing action_type in response"}), 400

    if response_dict['action_type'] == 'create':
        if 'eventParams' not in response_dict or 'eventCompletion' not in response_dict:
            return jsonify({"error": "Missing eventParams or eventCompletion"}), 400

        eventParams = response_dict['eventParams']
        # Check if eventParams is an array and get the first item
        if isinstance(eventParams, list) and len(eventParams) > 0:
            event_data = eventParams[0]  # Get the first event from the array
            try:
                if main.formatEvent(event_data):
                    message = response_dict['eventCompletion']
                    return jsonify({"message": message, "success": True})
                else:
                    return jsonify({"error": "Failed to format event"}), 400
            except Exception as e:
                return jsonify({"error": f"Exception in formatEvent: {str(e)}"}), 400
        else:
            return jsonify({"error": "eventParams is not in the expected format"}), 400

    elif response_dict['action_type'] == 'view':
        if 'query_details' not in response_dict:
            return jsonify({"error": "Missing query_details"}), 400

        query_details = response_dict['query_details']
        return jsonify(main.findEvent(query_details=query_details))

    return jsonify({"error": "Unknown action_type"}), 400

if __name__ == '__main__':
    app.run(debug=True)
        
    


    


