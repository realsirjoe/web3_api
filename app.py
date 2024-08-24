import os
from pathlib import Path
import json
import threading
from flask import Flask, jsonify, request, abort
from werkzeug.exceptions import HTTPException
from daemon import block_download_daemon
from flask import g
from crypto import init, download_blocks_eth, download_blocks, get_balance, get_volume

############### CONFIG ###############
infura_api_key = "eeb48ea631c74f1682d9ce248112ec56"
cache_path = "/Users/sirjoe/Downloads/crypto2"
######################################

tokens = ["ETH", "USDC", "USDT"]

app = Flask(__name__)
volumes = {}

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "error": e.name,
        "error_description": e.description,
    })
    response.content_type = "application/json"
    return response

@app.route('/balance/<wallet_address>', methods=['GET'])
def balance(wallet_address):
    try:
        balances = get_balance(infura_api_key, wallet_address, tokens)
    except Exception as e:
        abort(400, description=str(e))

    data = {"code": 200, "error": None, "error_description": None,"data": balances}
    return jsonify(data)

@app.route('/volume/<wallet_address>', methods=['GET'])
def volume(wallet_address):
    full_volumens = {}
    for token in tokens:
        try:
            full_volumens[token] = volumes[token][wallet_address.lower()]
        except:
            full_volumens[token] = 0

    data = {"code": 200, "error": None, "error_description": None,"data": full_volumens}
    return jsonify(data)

if __name__ == '__main__':
    init()

    for token in tokens:
        full_download_dir = os.path.join(cache_path, token)
        Path(full_download_dir).mkdir(parents=True, exist_ok=True)

    volumes = get_volume(cache_path, tokens)

    def daemon():
        for v in block_download_daemon(cache_path, infura_api_key):
            volumes = v

    t1 = threading.Thread(target=daemon)
    t1.start()

    app.run(port=5000)
