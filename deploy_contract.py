"""Compile and deploy LostAndFoundRegistry to Ganache with web3.py.

Alternative to deploying from Remix. Writes contract-config.json (address + ABI)
so the web app and demo script can find the contract.

Usage: python deploy_contract.py [--account-index 0]
"""
import argparse
from pathlib import Path

import solcx

from blockchain_client import BlockchainError, connect_web3, rpc_url_from_env, save_config

BASE_DIR = Path(__file__).resolve().parent
SOURCE_PATH = BASE_DIR / "contracts" / "LostAndFoundRegistry.sol"
SOLC_VERSION = "0.8.24"
EVM_VERSION = "paris"  # Ganache-compatible bytecode (no PUSH0 / MCOPY)


def compile_contract():
    """Return (abi, bytecode) for LostAndFoundRegistry."""
    if SOLC_VERSION not in [str(v) for v in solcx.get_installed_solc_versions()]:
        solcx.install_solc(SOLC_VERSION)
    output = solcx.compile_standard(
        {
            "language": "Solidity",
            "sources": {SOURCE_PATH.name: {"content": SOURCE_PATH.read_text(encoding="utf-8")}},
            "settings": {
                "evmVersion": EVM_VERSION,
                "optimizer": {"enabled": True, "runs": 200},
                "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}},
            },
        },
        solc_version=SOLC_VERSION,
    )
    artifact = output["contracts"][SOURCE_PATH.name]["LostAndFoundRegistry"]
    return artifact["abi"], artifact["evm"]["bytecode"]["object"]


def deploy(w3, abi, bytecode, deployer):
    """Deploy the contract from an unlocked Ganache account; return the contract instance."""
    factory = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = factory.constructor().transact({"from": deployer})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
    if receipt.status != 1:
        raise BlockchainError(f"Deployment transaction failed: {tx_hash.hex()}")
    return w3.eth.contract(address=receipt.contractAddress, abi=abi), receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--account-index", type=int, default=0, help="Ganache account used to deploy")
    args = parser.parse_args()
    try:
        rpc_url = rpc_url_from_env()
        w3 = connect_web3(rpc_url)
        accounts = w3.eth.accounts
        if not 0 <= args.account_index < len(accounts):
            raise BlockchainError(f"Account index must be between 0 and {len(accounts) - 1}.")
        abi, bytecode = compile_contract()
        contract, receipt = deploy(w3, abi, bytecode, accounts[args.account_index])
        save_config(contract.address, abi)  # RPC_URL env var still overrides at runtime
    except BlockchainError as error:
        raise SystemExit(f"Error: {error}")
    print("LostAndFoundRegistry deployed")
    print("  Address :", contract.address)
    print("  Deployer:", accounts[args.account_index])
    print("  Tx hash :", receipt.transactionHash.hex())
    print("  Gas used:", receipt.gasUsed)
    print("Saved address + ABI to contract-config.json")


if __name__ == "__main__":
    main()
