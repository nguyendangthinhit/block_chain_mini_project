"""Contract rules and address-based permissions, exercised through web3.py on Ganache."""
import pytest

import registry_service as service


def tx(w3, registry, fn, sender):
    receipt = service.send_transaction(w3, fn, sender)
    return service.receipt_summary(registry, receipt)


def reverts(w3, fn, sender, reason):
    with pytest.raises(service.TransactionRejected, match=reason):
        service.send_transaction(w3, fn, sender)


def register(w3, registry, finder, name="Black wallet"):
    return tx(w3, registry, registry.functions.registerItem(name, "Found at library, 2nd floor"), finder)


def test_register_item_stores_data_and_emits_event(w3, registry, accounts):
    result = register(w3, registry, accounts["finder"])
    assert [e["event"] for e in result["events"]] == ["ItemRegistered"]
    item = service.item_to_dict(registry.functions.getItem(1).call())
    assert item["finder"] == accounts["finder"]
    assert item["name"] == "Black wallet"
    assert item["status"] == "Found"
    assert registry.functions.itemCount().call() == 1


@pytest.mark.parametrize("name,description,reason", [
    ("", "desc", "Item name is required"),
    ("x" * 65, "desc", "Item name is too long"),
    ("Keys", "", "Description is required"),
    ("Keys", "d" * 281, "Description is too long"),
])
def test_register_item_validates_input(w3, registry, accounts, name, description, reason):
    reverts(w3, registry.functions.registerItem(name, description), accounts["finder"], reason)


def test_submit_claim_by_another_account(w3, registry, accounts):
    register(w3, registry, accounts["finder"])
    result = tx(w3, registry, registry.functions.submitClaim(1, "Contains my student ID"), accounts["owner"])
    assert result["events"][0]["event"] == "ClaimSubmitted"
    claim = service.claim_to_dict(registry.functions.getClaim(1).call())
    assert claim["claimant"] == accounts["owner"]
    assert claim["status"] == "Pending"
    assert registry.functions.getItemClaimIds(1).call() == [1]


def test_finder_cannot_claim_own_item(w3, registry, accounts):
    register(w3, registry, accounts["finder"])
    reverts(w3, registry.functions.submitClaim(1, "mine"), accounts["finder"], "Finder cannot claim own item")


def test_duplicate_claim_and_missing_item_rejected(w3, registry, accounts):
    register(w3, registry, accounts["finder"])
    tx(w3, registry, registry.functions.submitClaim(1, "proof"), accounts["owner"])
    reverts(w3, registry.functions.submitClaim(1, "again"), accounts["owner"], "Already claimed this item")
    reverts(w3, registry.functions.submitClaim(42, "proof"), accounts["owner"], "Item does not exist")
    reverts(w3, registry.functions.submitClaim(1, ""), accounts["other"], "Claim details are required")
    reverts(w3, registry.functions.submitClaim(1, "x" * 281), accounts["other"], "Claim details are too long")


def test_only_finder_can_approve(w3, registry, accounts):
    register(w3, registry, accounts["finder"])
    tx(w3, registry, registry.functions.submitClaim(1, "proof"), accounts["owner"])
    reverts(w3, registry.functions.approveClaim(1), accounts["owner"], "Only finder can approve")
    reverts(w3, registry.functions.approveClaim(1), accounts["outsider"], "Only finder can approve")
    assert service.item_to_dict(registry.functions.getItem(1).call())["status"] == "Found"


def test_finder_approves_and_item_is_returned(w3, registry, accounts):
    register(w3, registry, accounts["finder"])
    tx(w3, registry, registry.functions.submitClaim(1, "proof"), accounts["owner"])
    result = tx(w3, registry, registry.functions.approveClaim(1), accounts["finder"])
    assert [e["event"] for e in result["events"]] == ["ClaimApproved", "ItemReturned"]
    assert result["events"][1]["args"]["owner"] == accounts["owner"]
    item = service.item_to_dict(registry.functions.getItem(1).call())
    assert item["status"] == "Returned"
    assert item["approvedClaimId"] == 1
    assert service.claim_to_dict(registry.functions.getClaim(1).call())["status"] == "Approved"


def test_later_claims_on_returned_item_are_rejected(w3, registry, accounts):
    register(w3, registry, accounts["finder"])
    tx(w3, registry, registry.functions.submitClaim(1, "proof"), accounts["owner"])
    tx(w3, registry, registry.functions.submitClaim(1, "maybe mine"), accounts["other"])
    tx(w3, registry, registry.functions.approveClaim(1), accounts["finder"])
    reverts(w3, registry.functions.submitClaim(1, "late"), accounts["outsider"], "Item already returned")
    reverts(w3, registry.functions.approveClaim(2), accounts["finder"], "Item already returned")
    reverts(w3, registry.functions.approveClaim(99), accounts["finder"], "Claim does not exist")


def test_list_items_and_events(w3, registry, accounts):
    register(w3, registry, accounts["finder"], "Umbrella")
    register(w3, registry, accounts["finder"], "Laptop")
    tx(w3, registry, registry.functions.submitClaim(2, "Sticker on lid"), accounts["owner"])
    items = service.list_items(registry)
    assert [i["name"] for i in items] == ["Laptop", "Umbrella"]
    assert items[0]["claims"][0]["details"] == "Sticker on lid"
    assert service.recent_events(registry)[0]["event"] == "ClaimSubmitted"
