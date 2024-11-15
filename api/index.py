from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/api/chat', methods=['POST'])
def chat():
    return jsonify({"reply": "Hello from Vercel!"})
