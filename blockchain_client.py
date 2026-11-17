"""web3.py connection to Ganache and the LostAndFoundRegistry contract.

Built from the course template: connect to Ganache, validate the pasted contract
address + ABI, then expose the contract. Address and ABI come from
contract-config.json (paste them from Remix, or run deploy_contract.py).
"""
import json
import os
from pathlib import Path

from web3 import Web3

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get("CONTRACT_CONFIG", BASE_DIR / "contract-config.json"))
DEFAULT_RPC_URL = "http://127.0.0.1:7545"


class BlockchainError(Exception):
    """Raised when Ganache or the contract cannot be reached or used."""


def rpc_url_from_env(config_rpc_url=None):
    """RPC_URL env var wins (useful in Docker), then the config file, then the default."""
    return os.environ.get("RPC_URL") or config_rpc_url or DEFAULT_RPC_URL


def load_config(path=None):
    path = Path(path or CONFIG_PATH)
    if not path.exists():
        raise BlockchainError(
            f"Missing {Path(path).name}. Deploy the contract (Remix or deploy_contract.py) "
            "and save its address + ABI there."
        )
    try:
        config = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BlockchainError(f"{Path(path).name} is not valid JSON: {exc}") from exc
    if not isinstance(config.get("abi"), list):
        raise BlockchainError("contract-config.json must contain the ABI JSON array under 'abi'.")
    return config


def save_config(address, abi, rpc_url=None, path=None):
    data = {"rpc_url": rpc_url or DEFAULT_RPC_URL, "contract_address": address, "abi": abi}
    Path(path or CONFIG_PATH).write_text(json.dumps(data, indent=2), encoding="utf-8")


def connect_web3(rpc_url):
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
    if not w3.is_connected():
        raise BlockchainError(
            f"Cannot connect to Ganache at {rpc_url}. Check that Ganache is running and the URL is correct."
        )
    return w3


def load_contract(w3, address, abi):
    if not Web3.is_address(address or ""):
        raise BlockchainError("contract_address is not a valid address. Paste the deployed contract address.")
    checksum = Web3.to_checksum_address(address)
    if not w3.eth.get_code(checksum):
        raise BlockchainError(
            "No contract code at this address on the connected network. Check the address and Ganache network."
        )
    return w3.eth.contract(address=checksum, abi=abi)


def get_connection(config_path=None):
    """Return (w3, contract) using contract-config.json."""
    config = load_config(config_path)
    w3 = connect_web3(rpc_url_from_env(config.get("rpc_url")))
    return w3, load_contract(w3, config.get("contract_address"), config["abi"])


if __name__ == "__main__":
    try:
        web3_client, registry = get_connection()
    except BlockchainError as error:
        raise SystemExit(f"Error: {error}")
    print("Connected to Ganache and contract!")
    print("Chain ID:", web3_client.eth.chain_id)
    print("Contract:", registry.address)
    print("Available unlocked accounts:", web3_client.eth.accounts)
