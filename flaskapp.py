from flask import Flask, render_template, jsonify
from flask_cors import CORS
import json
import requests

app = Flask(__name__)
CORS(app)

file_path = "test.json"

# Load JSON data from file
with open(file_path, 'r') as file:
    data = json.load(file)
    print(data)

def check_video_status(url):
    try:
        response = requests.head(url)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request exception for {url}: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    try:
        markers = []

        for key in data['time']:
            try:
                latitude = float(data['latitude'][key])
                longitude = float(data['longitude'][key])
                city = data['city'][key]
                message = data['message'][key]
                title = data['title'][key]
                date = data['date'][key]
                time = data['time'][key]
                video = data['video'][key]

                # Check video link status
                video_status = check_video_status(video)

                marker = {
                    'latitude': latitude,
                    'longitude': longitude,
                    'city': city,
                    'message': message,
                    'title':  title, # Adding title attribute for the sidebar
                    'date':  date,
                    'time':  time,
                    'video links': video
                    #'video_status': video_status  # Add video status to marker data
                }
                markers.append(marker)
            except KeyError as e:
                print(f"Missing key: {e}")
            except ValueError as e:
                print(f"Invalid value for lat/lon: {e}")

        return jsonify(markers)

    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"})


if __name__ == '__main__':
    app.run(debug=True)