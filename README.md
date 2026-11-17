# Lost and Found Registry (DS 441 A – Individual Mini Project)

Student: Nguyễn Đăng Thịnh – 29210258195

A finder records a found item and its description. A claimant submits a claim. Only the
finder can approve a claim, which marks the item **Returned**. New claims on returned items are
rejected. The smart contract enforces every rule and permission, not only the interface.

---

## Contents

1. [Architecture](#1-architecture)
2. [Project structure](#2-project-structure)
3. [Contract rules](#3-contract-rules)
4. [Setup and run (Python + Ganache)](#4-setup-and-run-python--ganache)
5. [Using the web interface (demo walkthrough)](#5-using-the-web-interface-demo-walkthrough)
6. [CLI demo](#6-cli-demo)
7. [Tests](#7-tests)
8. [Configuration reference](#8-configuration-reference)
9. [Troubleshooting](#9-troubleshooting)
10. [Screenshots / demo](#10-screenshots--demo)
11. [Citations](#11-citations)

---

## 1. Architecture

```
Browser (HTML/JS, templates/ + static/)
   │ fetch /api/*
Flask backend (app.py) ── web3.py (blockchain_client.py, registry_service.py)
   │ JSON-RPC http://127.0.0.1:7545
Ganache (local test chain) ── LostAndFoundRegistry.sol (contracts/)
```

- The browser never holds private keys. You pick one of Ganache's **unlocked test accounts**
  in the UI; the backend sends the transaction from that account through Ganache.
- Before sending, the backend simulates the call, so a rule violation comes back as the
  contract's own `require()` message (e.g. `Only finder can approve`).
- Only Ganache test accounts and test Ether are used. No real funds or real keys.

## 2. Project structure

| File / folder | Purpose |
|---|---|
| `contracts/LostAndFoundRegistry.sol` | Smart contract (Solidity ^0.8.20) |
| `blockchain_client.py` | Connects to Ganache, loads address + ABI from `contract-config.json` (based on the course web3.py template) |
| `registry_service.py` | Sends transactions, decodes revert reasons and events, reads items/claims |
| `app.py` | Flask web server + JSON API used by the UI |
| `templates/index.html`, `static/app.js`, `static/style.css` | Web interface |
| `deploy_contract.py` | Compiles (solc 0.8.24, EVM `paris`) and deploys, writes `contract-config.json` |
| `demo_workflow.py` | Command-line demo of the full scenario with 3 accounts |
| `tests/` | pytest suite (contract rules + web API) against a running Ganache |
| `requirements.txt` | Python dependencies (web3, flask, py-solc-x, pytest) |

`contract-config.json` is generated at deploy time and is not committed.

## 3. Contract rules

| Function | Who can call | Rule (revert message) |
|---|---|---|
| `registerItem(name, description)` | anyone (caller becomes the **finder**) | name 1–64 bytes (`Item name is required` / `Item name is too long`), description 1–280 bytes |
| `submitClaim(itemId, details)` | anyone **except the finder** | `Item does not exist`; `Item already returned`; `Finder cannot claim own item`; `Already claimed this item`; details 1–280 bytes |
| `approveClaim(claimId)` | **finder only** | `Claim does not exist`; `Only finder can approve`; `Item already returned`. Marks the claim *Approved* and the item *Returned* |
| `getItem`, `getClaim`, `getItemClaimIds`, `itemCount`, `claimCount`, `hasClaimed` | anyone (read-only) | – |

Events: `ItemRegistered`, `ClaimSubmitted`, `ClaimApproved`, `ItemReturned`. The UI shows them in
the **Transaction status** panel and the **Contract events** log.

## 4. Setup and run (Python + Ganache)

**Quick start** (Python and Ganache already installed, Ganache running on port 7545):

```bash
git clone https://github.com/nguyendangthinhit/block_chain_mini_project.git
cd block_chain_mini_project
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python deploy_contract.py         # compile + deploy, writes contract-config.json
python app.py                     # open http://127.0.0.1:5000
```

The subsections below explain each step in detail.

### 4.1 Prerequisites

- **Python 3.10 – 3.12** with `pip` (`python --version`)
- **Ganache**, one of:
  - Ganache GUI 2.7+ ([download](https://archive.trufflesuite.com/ganache/)), or
  - Node.js 16+ and the CLI: `npx ganache` (no install needed)
- Internet on the first deploy (py-solc-x downloads solc 0.8.24 once)
- Optional: [Remix IDE](https://remix.ethereum.org) if you want to deploy from the browser

### 4.2 Install Python dependencies

```bash
git clone https://github.com/nguyendangthinhit/block_chain_mini_project.git
cd block_chain_mini_project

python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Windows (cmd):         .venv\Scripts\activate.bat
# macOS / Linux:         source .venv/bin/activate

pip install -r requirements.txt
python -c "from web3 import Web3; print('web3 OK')"
```

### 4.3 Start Ganache

| Setting | Value |
|---|---|
| RPC URL | `http://127.0.0.1:7545` |
| Chain ID | `1337` |
| Network ID | `5777` |
| Accounts | 10 unlocked test accounts, 100 ETH each |

**Ganache GUI**: *New Workspace (Ethereum)* → *Server* tab → host `127.0.0.1`, port `7545`,
network ID `5777` → *Save Workspace*. (Quickstart also uses port 7545.)

**Ganache CLI** (keep this terminal open):

```bash
npx ganache --server.port 7545 --chain.chainId 1337 --chain.networkId 5777 --wallet.deterministic
```

### 4.4 Deploy the contract

**Way 1 – script (easiest)**

```bash
python deploy_contract.py              # deploys from account #0
python deploy_contract.py --account-index 1   # or from another account
```

It prints the contract address and writes `contract-config.json` next to `app.py`.

**Way 2 – Remix**
1. Open [Remix](https://remix.ethereum.org), create `LostAndFoundRegistry.sol`, paste the contents of `contracts/LostAndFoundRegistry.sol`.
2. *Solidity compiler* tab: version **0.8.24**, *Advanced Configurations* → EVM version **paris** → *Compile*.
   (Newer EVM targets such as `cancun`/`shanghai` produce opcodes Ganache may not support.)
3. *Deploy & run transactions* tab: Environment **Dev – Ganache Provider** (or *Custom – External Http Provider*) → `http://127.0.0.1:7545` → *Deploy*.
4. Copy the deployed address and the ABI (*Solidity compiler* tab → *ABI* button), and create `contract-config.json` next to `app.py`:
   ```json
   {
     "rpc_url": "http://127.0.0.1:7545",
     "contract_address": "0xYourDeployedAddress",
     "abi": [ "...paste the ABI array here..." ]
   }
   ```

Check the connection:

```bash
python blockchain_client.py
# Connected to Ganache and contract!  Chain ID: 1337 ...
```

### 4.5 Run the web app

```bash
python app.py
```

Open **http://127.0.0.1:5000**. If you redeploy, just refresh the page; the app reloads
`contract-config.json` on every request.

---

## 5. Using the web interface (demo walkthrough)

The page has: **Wallet** (account picker, connected account, balance, chain ID, block, contract
address, item/claim counts), **Register a found item**, **Transaction status**, **Items & claims**,
and **Contract events**.

Buttons are intentionally never disabled by role, so you can show the contract rejecting invalid actions.

| # | Account | Action | Expected result |
|---|---|---|---|
| 1 | #0 (finder) | Select `#0` → **Connect account** → fill name + description → **Register item** | ✅ success, tx hash, block, gas, event `ItemRegistered`; item #1 shows **Found** |
| 2 | #1 (owner) | Connect `#1` → in item #1 type proof of ownership → **Submit claim** | ✅ success, event `ClaimSubmitted`; claim #1 **Pending** |
| 3 | #1 (owner) | Still #1 → click **Approve & mark returned** on claim #1 | ❌ *Rejected by contract: `Only finder can approve`* (unauthorized action) |
| 4 | #0 (finder) | Connect `#0` → **Approve & mark returned** | ✅ success, events `ClaimApproved` + `ItemReturned`; item becomes **Returned**, claim **Approved** |
| 5 | #2 (late claimant) | Connect `#2` → **Submit claim** on item #1 | ❌ *Rejected by contract: `Item already returned`* |

Other rejections you can try: the finder claiming their own item (`Finder cannot claim own item`),
the same account claiming twice (`Already claimed this item`), an empty name (`Item name is required`).

**Why the rejections happen**: the checks are `require()` statements inside the contract, so the
transaction reverts on-chain no matter which client sends it. The interface only displays the
revert reason; it does not decide the rule.

## 6. CLI demo

`demo_workflow.py` runs the same 5 steps with accounts #0, #1, #2 and prints each transaction:

```bash
python demo_workflow.py
```

Expected result of each step (shortened; real output also shows sender, tx hash, block and gas):

```
== 1. Finder registers a found item           -> SUCCESS ... event ItemRegistered
== 2. Owner submits a claim on item #1         -> SUCCESS ... event ClaimSubmitted
== 3. Owner tries to approve own claim #1      -> REJECTED by contract: Only finder can approve
== 4. Finder approves claim #1 ...             -> SUCCESS ... events ClaimApproved, ItemReturned
== 5. Another account claims returned item #1  -> REJECTED by contract: Item already returned
Final state: item #1 'Black wallet' is Returned (approved claim #1)
```

## 7. Tests

Ganache must be running on `RPC_URL` (default `http://127.0.0.1:7545`). Each test deploys its own
fresh contract, so tests do not touch the contract used by the UI.

```bash
python -m pytest -v
```

| Test | What it checks |
|---|---|
| `test_register_item_stores_data_and_emits_event` | item stored with finder/status, `ItemRegistered` emitted |
| `test_register_item_validates_input` | empty / too long name and description rejected |
| `test_submit_claim_by_another_account` | claim stored, `ClaimSubmitted` emitted |
| `test_finder_cannot_claim_own_item` | finder blocked from claiming |
| `test_duplicate_claim_and_missing_item_rejected` | double claim and unknown item rejected |
| `test_only_finder_can_approve` | non-finder approval rejected (address-based permission) |
| `test_finder_approves_and_item_is_returned` | approval marks claim Approved + item Returned, both events |
| `test_later_claims_on_returned_item_are_rejected` | `Item already returned` |
| `test_list_items_and_events` | read helpers used by the UI |
| `test_status_and_index` | API status + page loads |
| `test_full_workflow_through_api` | whole scenario through the web API, incl. both rejections |
| `test_rejects_unknown_or_missing_account` | API refuses missing / non-Ganache accounts |

**Results**: _to be filled after running (paste the pytest summary line, e.g. `N passed in Xs`)._

## 8. Configuration reference

| Environment variable | Default | Used for |
|---|---|---|
| `RPC_URL` | `http://127.0.0.1:7545` | Ganache RPC (overrides `rpc_url` in `contract-config.json`) |
| `CONTRACT_CONFIG` | `./contract-config.json` | Path to address + ABI file |
| `HOST` | `127.0.0.1` | Flask bind address |
| `PORT` | `5000` | Flask port |

Example (PowerShell): `$env:RPC_URL="http://127.0.0.1:8545"; python app.py`
Example (bash): `RPC_URL=http://127.0.0.1:8545 python app.py`

## 9. Troubleshooting

| Problem | Cause / fix |
|---|---|
| `Cannot connect to Ganache at http://127.0.0.1:7545` | Ganache is not running or uses another port. Start it on 7545 or set `RPC_URL`. |
| `Missing contract-config.json` | Deploy first (`python deploy_contract.py` or Remix, section 4.4). |
| `No contract code at this address` | Ganache was restarted (new chain) or the address is from another network. Redeploy. |
| Remix deploy fails / `invalid opcode` | Set EVM version to **paris** in Remix compiler settings. |
| `Account is not an unlocked Ganache account` | The UI remembers an account from an old Ganache session. Pick an account again and click **Connect account**. |
| Port 5000 or 7545 already in use | Stop the other program, or change it: `PORT=5050 python app.py` (PowerShell: `$env:PORT="5050"; python app.py`). On macOS, AirPlay Receiver uses port 5000. |
| Windows: `DLL load failed ... An Application Control policy has blocked this file` | Windows **Smart App Control** blocks web3.py's native modules. Use another machine, or turn off Smart App Control (Windows Security → App & browser control). |
| `solcx` cannot download the compiler | First deploy needs internet. Or deploy with Remix instead. |
| `pip install` fails building packages | Use Python 3.10–3.12 (64-bit) and upgrade pip: `python -m pip install --upgrade pip`. |

## 10. Screenshots / demo

_Add screenshots of steps 1–5 from section 5 (e.g. a `docs/` folder) or a short recording link here._

## 11. Citations

- web3.py connection template provided by the course (`blockchain_client.py` is based on it).
- Libraries / tools: web3.py, Flask, py-solc-x, pytest, Ganache.
- AI assistance: Claude Code (Anthropic) helped draft the code, tests and README. I reviewed and ran them.
