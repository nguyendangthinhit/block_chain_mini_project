"""End-to-end demo with three Ganache accounts on the deployed contract.

Register an item -> submit a claim -> unauthorized approval (rejected) ->
finder approves -> a later claim on the returned item (rejected).
Usage: python demo_workflow.py   (after deploying; uses contract-config.json)
"""
import registry_service as service
from blockchain_client import BlockchainError, get_connection


def step(title, w3, contract, fn, sender):
    print(f"\n== {title}\n   from {sender}")
    try:
        receipt = service.send_transaction(w3, fn, sender)
    except service.TransactionRejected as error:
        print(f"   REJECTED by contract: {error}")
        return None
    summary = service.receipt_summary(contract, receipt)
    print(f"   SUCCESS tx {summary['txHash']} | block {summary['blockNumber']} | gas {summary['gasUsed']}")
    for event in summary["events"]:
        print(f"   event {event['event']}: {event['args']}")
    return summary


def main():
    try:
        w3, contract = get_connection()
    except BlockchainError as error:
        raise SystemExit(f"Error: {error}")
    if len(w3.eth.accounts) < 3:
        raise SystemExit("Error: the demo needs at least 3 Ganache accounts.")
    finder, owner, late_claimant = w3.eth.accounts[:3]
    print(f"Chain {w3.eth.chain_id} | contract {contract.address}")
    print(f"Finder={finder}\nOwner={owner}\nLate claimant={late_claimant}")

    step("1. Finder registers a found item", w3, contract,
         contract.functions.registerItem("Black wallet", "Found in library, 2nd floor, 17 Nov"), finder)
    item_id = contract.functions.itemCount().call()
    step(f"2. Owner submits a claim on item #{item_id}", w3, contract,
         contract.functions.submitClaim(item_id, "Contains my student ID card"), owner)
    claim_id = contract.functions.claimCount().call()
    step(f"3. Owner tries to approve own claim #{claim_id} (unauthorized)", w3, contract,
         contract.functions.approveClaim(claim_id), owner)
    step(f"4. Finder approves claim #{claim_id} and marks item returned", w3, contract,
         contract.functions.approveClaim(claim_id), finder)
    step(f"5. Another account claims returned item #{item_id} (invalid)", w3, contract,
         contract.functions.submitClaim(item_id, "I lost a wallet too"), late_claimant)

    item = service.item_to_dict(contract.functions.getItem(item_id).call())
    print(f"\nFinal state: item #{item_id} '{item['name']}' is {item['status']} "
          f"(approved claim #{item['approvedClaimId']})")


if __name__ == "__main__":
    main()
