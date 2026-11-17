"""Read state from and send transactions to LostAndFoundRegistry via web3.py."""
from web3 import Web3
from web3.exceptions import ContractCustomError, ContractLogicError, TimeExhausted
from web3.logs import DISCARD

from blockchain_client import BlockchainError

ITEM_STATUS = ("Found", "Returned")
CLAIM_STATUS = ("Pending", "Approved")
EVENT_NAMES = ("ItemRegistered", "ClaimSubmitted", "ClaimApproved", "ItemReturned")


class TransactionRejected(Exception):
    """The contract reverted (rule or permission violation)."""


def revert_reason(error):
    """Turn a web3 revert error into the contract's require() message."""
    message = str(getattr(error, "message", None) or error)
    for prefix in ("execution reverted: ", "VM Exception while processing transaction: revert "):
        if prefix in message:
            return message.split(prefix, 1)[1].strip(" '\"")
    return message


def resolve_account(w3, account):
    """Only unlocked Ganache accounts can sign through the node."""
    if not Web3.is_address(account or ""):
        raise TransactionRejected("Select a valid Ganache account first.")
    checksum = Web3.to_checksum_address(account)
    if checksum not in w3.eth.accounts:
        raise TransactionRejected("Account is not an unlocked Ganache account.")
    return checksum


def send_transaction(w3, contract_fn, sender):
    """Simulate first (to surface revert reasons), then send and wait for the receipt."""
    try:
        contract_fn.call({"from": sender})
        tx_hash = contract_fn.transact({"from": sender})
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
    except (ContractLogicError, ContractCustomError) as error:
        raise TransactionRejected(revert_reason(error)) from error
    except TimeExhausted as error:
        raise BlockchainError("Timed out waiting for the transaction receipt.") from error
    if receipt.status != 1:
        # The pre-call passed but state changed before mining (e.g. two approvals racing).
        raise TransactionRejected(f"Transaction reverted on-chain (state changed); tx {_hex(receipt.transactionHash)}")
    return receipt


def receipt_summary(contract, receipt):
    events = []
    for name in EVENT_NAMES:
        for log in getattr(contract.events, name)().process_receipt(receipt, errors=DISCARD):
            events.append({"event": name, "args": _plain(log["args"]), "logIndex": log["logIndex"]})
    events.sort(key=lambda e: e["logIndex"])  # true chain order
    return {
        "txHash": _hex(receipt.transactionHash),
        "blockNumber": receipt.blockNumber,
        "gasUsed": receipt.gasUsed,
        "from": receipt["from"],
        "events": events,
    }


def item_to_dict(item):
    return {
        "id": item[0], "finder": item[1], "name": item[2], "description": item[3],
        "status": ITEM_STATUS[item[4]], "approvedClaimId": item[5], "createdAt": item[6],
    }


def claim_to_dict(claim):
    return {
        "id": claim[0], "itemId": claim[1], "claimant": claim[2], "details": claim[3],
        "status": CLAIM_STATUS[claim[4]], "createdAt": claim[5],
    }


def list_items(contract):
    """All items (newest first) with their claims."""
    items = []
    for item_id in range(contract.functions.itemCount().call(), 0, -1):
        item = item_to_dict(contract.functions.getItem(item_id).call())
        claim_ids = contract.functions.getItemClaimIds(item_id).call()
        item["claims"] = [claim_to_dict(contract.functions.getClaim(cid).call()) for cid in claim_ids]
        items.append(item)
    return items


def recent_events(contract, limit=30):
    """Contract events from the chain, newest first."""
    events = []
    for name in EVENT_NAMES:
        for log in getattr(contract.events, name)().get_logs(from_block=0):
            events.append({
                "event": name, "args": _plain(log["args"]), "blockNumber": log["blockNumber"],
                "logIndex": log["logIndex"], "txHash": _hex(log["transactionHash"]),
            })
    events.sort(key=lambda e: (e["blockNumber"], e["logIndex"]), reverse=True)
    return events[:limit]


def _hex(value):
    text = value.hex()
    return text if text.startswith("0x") else "0x" + text


def _plain(args):
    return {key: value for key, value in dict(args).items()}
