"""Shared fixtures: a fresh LostAndFoundRegistry on the running Ganache for each test."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import blockchain_client  # noqa: E402
from deploy_contract import compile_contract, deploy  # noqa: E402


@pytest.fixture(scope="session")
def w3():
    try:
        return blockchain_client.connect_web3(blockchain_client.rpc_url_from_env())
    except blockchain_client.BlockchainError as error:
        pytest.exit(f"Ganache is required for tests: {error}", returncode=2)


@pytest.fixture(scope="session")
def compiled():
    return compile_contract()


@pytest.fixture()
def accounts(w3):
    finder, owner, other, outsider = w3.eth.accounts[:4]
    return {"finder": finder, "owner": owner, "other": other, "outsider": outsider}


@pytest.fixture()
def registry(w3, compiled, accounts):
    abi, bytecode = compiled
    contract, _ = deploy(w3, abi, bytecode, accounts["finder"])
    return contract


@pytest.fixture()
def api_client(tmp_path, monkeypatch, registry, compiled):
    """Flask test client wired to the fresh contract through a temp contract-config.json."""
    config = tmp_path / "contract-config.json"
    blockchain_client.save_config(registry.address, compiled[0], path=config)
    monkeypatch.setattr(blockchain_client, "CONFIG_PATH", config)
    from app import app

    app.config["TESTING"] = True
    return app.test_client()
