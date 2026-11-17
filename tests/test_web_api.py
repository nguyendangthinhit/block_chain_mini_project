"""Flask API (the interface's backend) against a freshly deployed contract."""


def post(client, path, body):
    return client.post(path, json=body)


def test_status_and_index(api_client, registry, accounts):
    status = api_client.get("/api/status").get_json()
    assert status["connected"] is True
    assert status["contractAddress"] == registry.address
    assert any(a["address"] == accounts["finder"] for a in status["accounts"])
    assert b"Lost and Found Registry" in api_client.get("/").data


def test_full_workflow_through_api(api_client, accounts):
    res = post(api_client, "/api/items", {"account": accounts["finder"], "name": "Keys", "description": "Car keys at gym"})
    assert res.status_code == 200 and res.get_json()["events"][0]["event"] == "ItemRegistered"

    res = post(api_client, "/api/items/1/claims", {"account": accounts["owner"], "details": "Toyota key, red tag"})
    assert res.status_code == 200

    res = post(api_client, "/api/claims/1/approve", {"account": accounts["owner"]})
    assert res.status_code == 400
    assert res.get_json() == {"error": "Only finder can approve", "rejected": True}

    res = post(api_client, "/api/claims/1/approve", {"account": accounts["finder"]})
    assert res.status_code == 200
    assert [e["event"] for e in res.get_json()["events"]] == ["ClaimApproved", "ItemReturned"]

    res = post(api_client, "/api/items/1/claims", {"account": accounts["other"], "details": "late"})
    assert res.status_code == 400 and res.get_json()["error"] == "Item already returned"

    items = api_client.get("/api/items").get_json()
    assert items[0]["status"] == "Returned" and items[0]["claims"][0]["status"] == "Approved"
    assert len(api_client.get("/api/events").get_json()) == 4


def test_rejects_unknown_or_missing_account(api_client):
    res = post(api_client, "/api/items", {"name": "Pen", "description": "Blue"})
    assert res.status_code == 400 and "Select a valid Ganache account" in res.get_json()["error"]
    res = post(api_client, "/api/items", {"account": "0x" + "1" * 40, "name": "Pen", "description": "Blue"})
    assert res.status_code == 400 and "not an unlocked Ganache account" in res.get_json()["error"]
