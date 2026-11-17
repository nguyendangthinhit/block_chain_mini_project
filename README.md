# Lost and Found Registry (DS 441 A – Individual Mini Project)

Student: Nguyễn Đăng Thịnh – 29210258195

A finder records a found item and its description. A claimant submits a claim. Only the
finder can approve a claim, which marks the item **Returned**. New claims on returned items are
rejected. The contract enforces every rule and permission, not only the interface.

## Architecture

```
Browser (HTML/JS, templates/ + static/)
   │ fetch /api/*
Flask backend (app.py) ── web3.py (blockchain_client.py, registry_service.py)
   │ JSON-RPC http://127.0.0.1:7545
Ganache ── LostAndFoundRegistry.sol (contracts/)
```

| File | Purpose |
|---|---|
| `contracts/LostAndFoundRegistry.sol` | Smart contract (paste into Remix or compile with `deploy_contract.py`) |
| `blockchain_client.py` | Course web3.py template: connect to Ganache, load address + ABI from `contract-config.json` |
| `registry_service.py` | Send transactions, decode revert reasons and events, read items/claims |
| `app.py`, `templates/`, `static/` | Web interface (account picker, forms, tx status, events) |
| `deploy_contract.py` | Compile (solc 0.8.24, EVM `paris`) + deploy with web3.py, writes `contract-config.json` |
| `demo_workflow.py` | CLI demo of the required scenario with 3 accounts |
| `tests/` | pytest suite (contract rules + web API) against Ganache |

### Contract rules

| Function | Who | Rule (revert message) |
|---|---|---|
| `registerItem(name, description)` | anyone (becomes finder) | name 1–64 bytes, description 1–280 bytes |
| `submitClaim(itemId, details)` | anyone except the finder | item exists; `Item already returned`; `Finder cannot claim own item`; `Already claimed this item` |
| `approveClaim(claimId)` | **finder only** | `Only finder can approve`; `Item already returned`. Approval marks the claim Approved and the item Returned |

Events: `ItemRegistered`, `ClaimSubmitted`, `ClaimApproved`, `ItemReturned`. The UI shows them in
the transaction status panel and the event log.

## Prerequisites

- Python 3.10+ and `pip`
- Ganache (GUI 2.7+ or CLI `npx ganache`). Test accounts and test Ether only, no real keys or funds.
- Optional: [Remix IDE](https://remix.ethereum.org) to deploy from the browser

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Quick start with Docker (no local Python/Ganache needed)

Needs Docker Desktop (Windows: WSL 2 enabled) or Docker Engine.

```bash
docker compose up --build                        # Ganache + deploy + app -> http://127.0.0.1:5000
docker compose exec app python demo_workflow.py  # CLI demo (in a 2nd terminal while `up` runs)
docker compose run --rm app python -m pytest -v  # test suite against the Ganache container
docker compose down                              # stop (chain data is discarded)
```

Ganache is also published on `http://127.0.0.1:7545`, so Remix can deploy to the same chain.
Every `up` deploys a fresh contract; the UI picks it up automatically.

## Ganache network settings

| Setting | Value |
|---|---|
| RPC URL | `http://127.0.0.1:7545` (override with env `RPC_URL`) |
| Chain ID | `1337` |
| Network ID | `5777` |
| Accounts | 10 unlocked test accounts, 100 ETH each |

CLI equivalent: `npx ganache --server.port 7545 --chain.chainId 1337 --chain.networkId 5777 --wallet.deterministic`

## Deploy

**Option A: Remix**
1. Open `contracts/LostAndFoundRegistry.sol` in Remix.
2. Solidity compiler: version **0.8.24**, Advanced → EVM version **paris** (newer EVM targets such as cancun do not run on Ganache).
3. Deploy & Run: Environment **Dev – Ganache Provider** (or *Custom – External Http Provider*) → `http://127.0.0.1:7545` → Deploy.
4. Create `contract-config.json` next to `app.py`:
   ```json
   { "rpc_url": "http://127.0.0.1:7545", "contract_address": "0x…from Remix…", "abi": [ …ABI copied from Remix… ] }
   ```

**Option B: script**: `python deploy_contract.py` (downloads solc 0.8.24 on first run, deploys from account #0 and writes `contract-config.json`).

Check the connection: `python blockchain_client.py`

## Run

```bash
python app.py          # open http://127.0.0.1:5000
python demo_workflow.py  # optional CLI demo
```

UI walkthrough (two or more accounts):
1. Pick account #0 → **Connect account** → register an item (finder).
2. Connect account #1 → **Submit claim** on the item (owner).
3. Still as #1, click **Approve** → rejected: `Only finder can approve`.
4. Connect #0 → **Approve & mark returned** → success, item becomes *Returned*.
5. Connect #2 → submit a claim on the same item → rejected: `Item already returned`.

## Tests

```bash
# Ganache must be running on RPC_URL
python -m pytest -v
```

Results: _to be filled after running on Ganache._

## Screenshots / demo

_Add screenshots of the steps above (`docs/` folder) or a short recording link._

## Citations

- web3.py connection template provided by the course (`blockchain_client.py` is based on it).
- Libraries: web3.py, Flask, py-solc-x, pytest.
- AI assistance: Claude Code (Anthropic) helped draft the code, tests and README. I reviewed and ran them.
