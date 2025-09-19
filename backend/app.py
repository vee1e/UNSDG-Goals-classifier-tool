from flask import Flask, jsonify, request
from flask_cors import CORS
from classify import main as classify_text

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello, World!'})



@app.route('/api/classify', methods=['POST'])
def classify():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    result = classify_text(url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)