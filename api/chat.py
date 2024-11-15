from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    conversations = data.get("conversations", [])
    
    # Add system prompt if not present
    if not any(c["role"] == "system" for c in conversations):
        conversations.insert(0, {"role": "system", "content": "You are a helpful assistant."})

    # Example response logic
    response = {"reply": "Hello from the chatbot! How can I help you today?"}
    return jsonify(response)

# Export the app for Vercel
def handler(request, *args, **kwargs):
    return app(environ=request.environ, start_response=kwargs.get('start_response'))
