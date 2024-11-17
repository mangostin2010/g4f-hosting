import json
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename

import logging
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify
import asyncio
import aiohttp
from typing import List, Dict
from flask_cors import CORS
import json
import nest_asyncio
from flask import Flask, request, jsonify, make_response
import ssl

# Enable nested event loops
nest_asyncio.apply()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


class ChatGPT4oMini:
    def __init__(self):
        self.url = "https://duckduckgo.com"
        self.api_endpoint = "https://duckduckgo.com/duckchat/v1/chat"
        self.model = "gpt-4o-mini"
        self.vqd = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    async def get_vqd(self):
        status_url = "https://duckduckgo.com/duckchat/v1/status"
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept': 'text/event-stream',
            'x-vqd-accept': '1'
        }

        try:
            # Create SSL context
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(status_url, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        vqd = response.headers.get("x-vqd-4")
                        if vqd:
                            return vqd
                        else:
                            raise Exception("VQD token not found in response headers")
                    else:
                        raise Exception(f"Failed to get VQD token: {response.status}")
        except Exception as e:
            logging.error(f"Error in get_vqd: {str(e)}")
            raise

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        try:
            if not self.vqd:
                self.vqd = await self.get_vqd()

            headers = {
                'accept': 'text/event-stream',
                'content-type': 'application/json',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
                'x-vqd-4': self.vqd,
            }

            data = {
                "model": self.model,
                "messages": messages
            }

            # Create SSL context
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            full_response = ""
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=60)

            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.post(self.api_endpoint, json=data, headers=headers, ssl=False) as response:
                    self.vqd = response.headers.get("x-vqd-4")

                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Request failed with status {response.status}: {error_text}")

                    async for line in response.content:
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith('data: '):
                                json_str = decoded_line[6:]
                                if json_str == '[DONE]':
                                    break
                                try:
                                    json_data = json.loads(json_str)
                                    if 'message' in json_data:
                                        full_response += json_data['message']
                                except json.JSONDecodeError as e:
                                    logging.error(f"JSON decode error: {str(e)} for line: {json_str}")

            if not full_response:
                raise Exception("No response received from the chat service")

            return full_response

        except Exception as e:
            logging.error(f"Chat error: {str(e)}")
            raise

chat_instance = ChatGPT4oMini()
# Update the chat endpoint
@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        data = request.get_json()
        logging.info(f"Received request data: {data}")

        if not data or 'messages' not in data:
            return jsonify({'error': 'Messages are required'}), 400

        messages = data['messages']
        logging.info(f"Processing chat request with {len(messages)} messages")

        try:
            response = chat_instance.loop.run_until_complete(chat_instance.chat(messages))
            logging.info("Chat request completed successfully")

            result = {
                'response': response,
                'messages': messages + [{'role': 'assistant', 'content': response}]
            }

            return jsonify(result)

        except Exception as e:
            logging.error(f"Error during chat processing: {str(e)}")
            return jsonify({'error': f"Chat processing error: {str(e)}"}), 500

    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Add error handler
@app.errorhandler(Exception)
def handle_error(error):
    logging.error(f"Unhandled error: {str(error)}")
    return jsonify({'error': str(error)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
