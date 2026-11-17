"""Flask web app: HTML/JS interface backed by web3.py talking to Ganache.

Run: python app.py  ->  http://127.0.0.1:5000
"""
import json
import os

from flask import Flask, jsonify, render_template, request
from web3 import Web3
from web3.exceptions import Web3ValidationError
from werkzeug.exceptions import HTTPException

import registry_service as service
from blockchain_client import BlockchainError, get_connection

app = Flask(__name__)


def _connection():
    """Connect per request so a redeploy (new contract-config.json) is picked up without restart."""
    return get_connection()


def _body():
    return request.get_json(silent=True) or {}


def _transact(build_fn):
    """Shared handler: resolve sender, send tx, return receipt summary or a readable error."""
    w3, contract = _connection()
    sender = service.resolve_account(w3, _body().get("account"))
    receipt = service.send_transaction(w3, build_fn(contract), sender)
    return jsonify(service.receipt_summary(contract, receipt))


@app.errorhandler(BlockchainError)
def handle_blockchain_error(error):
    return jsonify({"error": str(error)}), 503


@app.errorhandler(service.TransactionRejected)
def handle_rejected(error):
    return jsonify({"error": str(error), "rejected": True}), 400


@app.errorhandler(Web3ValidationError)
def handle_invalid_input(error):
    return jsonify({"error": f"Invalid input: {error}"}), 400


@app.errorhandler(HTTPException)
def handle_http_error(error):
    response = error.get_response()  # keeps headers such as Allow on 405
    response.data = json.dumps({"error": error.description})
    response.content_type = "application/json"
    return response


@app.errorhandler(Exception)
def handle_unexpected(error):
    app.logger.exception("Request failed")
    return jsonify({"error": "Internal server error. Check the server log."}), 500


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/status")
def status():
    w3, contract = _connection()
    accounts = [
        {"address": acc, "balanceEth": str(Web3.from_wei(w3.eth.get_balance(acc), "ether"))}
        for acc in w3.eth.accounts
    ]
    return jsonify({
        "connected": True,
        "chainId": w3.eth.chain_id,
        "blockNumber": w3.eth.block_number,
        "contractAddress": contract.address,
        "itemCount": contract.functions.itemCount().call(),
        "claimCount": contract.functions.claimCount().call(),
        "accounts": accounts,
    })


@app.get("/api/items")
def items():
    _, contract = _connection()
    return jsonify(service.list_items(contract))


@app.get("/api/events")
def events():
    _, contract = _connection()
    return jsonify(service.recent_events(contract))


@app.post("/api/items")
def register_item():
    body = _body()
    name, description = str(body.get("name", "")).strip(), str(body.get("description", "")).strip()
    return _transact(lambda c: c.functions.registerItem(name, description))


@app.post("/api/items/<int:item_id>/claims")
def submit_claim(item_id):
    details = str(_body().get("details", "")).strip()
    return _transact(lambda c: c.functions.submitClaim(item_id, details))


@app.post("/api/claims/<int:claim_id>/approve")
def approve_claim(claim_id):
    return _transact(lambda c: c.functions.approveClaim(claim_id))


if __name__ == "__main__":
    # Local demo only: bind to localhost unless HOST is set (e.g. 0.0.0.0 inside Docker).
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")), debug=False)
