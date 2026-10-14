from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

BASE = "/api/v1/reviews"


def create(client: TestClient, payload: dict, **overrides) -> dict:
    response = client.post(BASE, json={**payload, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


# ---------- health / catalog ----------


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_readiness_checks_database(client: TestClient) -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_hotel_catalog_has_28_hotels(client: TestClient) -> None:
    hotels = client.get("/api/v1/hotels").json()
    assert len(hotels) == 28
    assert {"HP-PT-001", "HP-PT-002"} <= {hotel["hotel_id"] for hotel in hotels}


def test_openapi_contract_is_published(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert {BASE, f"{BASE}/{{review_id}}", "/api/v1/hotels"} <= set(paths)


# ---------- create ----------


def test_create_review(client: TestClient, review_payload: dict) -> None:
    body = create(client, review_payload)
    assert body["id"] > 0
    assert body["reviewer_country"] == "CO"  # normalized to upper case
    assert body["platform"] == "booking"


def test_create_duplicate_external_id_returns_409(client: TestClient, review_payload) -> None:
    create(client, review_payload)
    response = client.post(BASE, json=review_payload)
    assert response.status_code == 409
    assert response.json()["error"] == "conflict"


def test_same_external_id_on_other_platform_is_allowed(client: TestClient, review_payload) -> None:
    create(client, review_payload)
    create(client, review_payload, platform="google")


def test_create_unknown_hotel_returns_422(client: TestClient, review_payload: dict) -> None:
    response = client.post(BASE, json={**review_payload, "hotel_id": "HP-XX-999"})
    assert response.status_code == 422
    assert "Unknown hotel_id" in response.json()["detail"]


@pytest.mark.parametrize("rating", [0, 6])
def test_create_rating_out_of_range_returns_422(client, review_payload, rating: int) -> None:
    assert client.post(BASE, json={**review_payload, "rating": rating}).status_code == 422


def test_create_invalid_language_returns_422(client, review_payload) -> None:
    assert client.post(BASE, json={**review_payload, "language": "fr"}).status_code == 422


def test_create_future_review_returns_422(client, review_payload) -> None:
    future = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    response = client.post(BASE, json={**review_payload, "published_at": future})
    assert response.status_code == 422


def test_create_stay_after_publication_returns_422(client, review_payload) -> None:
    response = client.post(BASE, json={**review_payload, "stay_date": "2026-10-09"})
    assert response.status_code == 422


def test_naive_published_at_is_treated_as_utc(client, review_payload) -> None:
    body = create(client, review_payload, published_at="2026-10-05T12:00:00")
    assert body["published_at"].startswith("2026-10-05T12:00:00")


# ---------- read ----------


def test_get_review_by_id(client: TestClient, review_payload: dict) -> None:
    created = create(client, review_payload)
    response = client.get(f"{BASE}/{created['id']}")
    assert response.status_code == 200
    assert response.json()["external_id"] == "BK-test-0001"


def test_get_missing_review_returns_404(client: TestClient) -> None:
    response = client.get(f"{BASE}/999999")
    assert response.status_code == 404
    assert response.json() == {"error": "not_found", "detail": "Review 999999 not found"}


# ---------- list / pagination ----------


def seed_many(client: TestClient, payload: dict, total: int) -> None:
    base_date = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
    for index in range(total):
        create(
            client,
            payload,
            external_id=f"EXT-{index:03d}",
            hotel_id="HP-CO-001" if index % 2 == 0 else "HP-BR-001",
            language="es" if index % 2 == 0 else "pt",
            rating=(index % 5) + 1,
            stay_date=None,
            published_at=(base_date + timedelta(days=index)).isoformat(),
        )


def test_pagination_metadata(client: TestClient, review_payload: dict) -> None:
    seed_many(client, review_payload, total=7)
    body = client.get(BASE, params={"page": 2, "page_size": 3}).json()
    assert [item["external_id"] for item in body["items"]] == ["EXT-003", "EXT-004", "EXT-005"]
    assert body["pagination"] == {
        "page": 2,
        "page_size": 3,
        "total_items": 7,
        "total_pages": 3,
        "has_next": True,
        "has_previous": True,
    }


def test_walking_all_pages_returns_every_review_once(client, review_payload) -> None:
    seed_many(client, review_payload, total=11)
    seen, page = [], 1
    while True:
        body = client.get(BASE, params={"page": page, "page_size": 4}).json()
        seen += [item["external_id"] for item in body["items"]]
        if not body["pagination"]["has_next"]:
            break
        page += 1
    assert len(seen) == len(set(seen)) == 11


def test_page_beyond_last_is_empty(client: TestClient, review_payload: dict) -> None:
    seed_many(client, review_payload, total=2)
    body = client.get(BASE, params={"page": 5}).json()
    assert body["items"] == []
    assert body["pagination"]["has_next"] is False


def test_empty_list(client: TestClient) -> None:
    body = client.get(BASE).json()
    assert body["items"] == []
    assert body["pagination"]["total_pages"] == 0


def test_descending_order(client: TestClient, review_payload: dict) -> None:
    seed_many(client, review_payload, total=3)
    items = client.get(BASE, params={"order": "desc"}).json()["items"]
    assert [item["external_id"] for item in items] == ["EXT-002", "EXT-001", "EXT-000"]


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"hotel_id": "HP-BR-001"}, 3),
        ({"language": "es"}, 4),
        ({"platform": "booking"}, 7),
        ({"platform": "google"}, 0),
        ({"min_rating": 4}, 2),
        ({"max_rating": 2}, 4),
        ({"published_from": "2026-09-03", "published_to": "2026-09-05"}, 3),
        ({"published_to": "2026-09-01"}, 1),
    ],
)
def test_filters(client: TestClient, review_payload: dict, params: dict, expected: int) -> None:
    seed_many(client, review_payload, total=7)
    body = client.get(BASE, params=params).json()
    assert body["pagination"]["total_items"] == expected


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"page_size": 0},
        {"page_size": 101},
        {"min_rating": 6},
        {"platform": "airbnb"},
        {"published_from": "not-a-date"},
    ],
)
def test_invalid_query_params_return_422(client: TestClient, params: dict) -> None:
    assert client.get(BASE, params=params).status_code == 422


@pytest.mark.parametrize(
    "params",
    [
        {"published_from": "2026-09-10", "published_to": "2026-09-01"},
        {"min_rating": 4, "max_rating": 2},
    ],
)
def test_inconsistent_ranges_return_422(client: TestClient, params: dict) -> None:
    response = client.get(BASE, params=params)
    assert response.status_code == 422
    assert response.json()["error"] == "business_rule_violation"


# ---------- update / delete ----------


def test_patch_review(client: TestClient, review_payload: dict) -> None:
    created = create(client, review_payload)
    response = client.patch(f"{BASE}/{created['id']}", json={"rating": 2, "title": "Cambió"})
    assert response.status_code == 200
    body = response.json()
    assert (body["rating"], body["title"], body["text"]) == (2, "Cambió", created["text"])
    assert body["updated_at"] >= created["updated_at"]


def test_patch_empty_body_returns_422(client: TestClient, review_payload: dict) -> None:
    created = create(client, review_payload)
    assert client.patch(f"{BASE}/{created['id']}", json={}).status_code == 422


def test_patch_required_field_to_null_returns_422(client, review_payload) -> None:
    created = create(client, review_payload)
    assert client.patch(f"{BASE}/{created['id']}", json={"text": None}).status_code == 422


def test_patch_missing_review_returns_404(client: TestClient) -> None:
    assert client.patch(f"{BASE}/123456", json={"rating": 3}).status_code == 404


def test_delete_review(client: TestClient, review_payload: dict) -> None:
    created = create(client, review_payload)
    assert client.delete(f"{BASE}/{created['id']}").status_code == 204
    assert client.get(f"{BASE}/{created['id']}").status_code == 404


def test_delete_missing_review_returns_404(client: TestClient) -> None:
    assert client.delete(f"{BASE}/424242").status_code == 404


def test_concurrent_insert_race_is_reported_as_409(client, review_payload, monkeypatch) -> None:
    """If two requests pass the existence check at once, the unique constraint decides."""
    from src.repositories.review_repository import ReviewRepository

    create(client, review_payload)
    monkeypatch.setattr(ReviewRepository, "get_by_external_id", lambda *_: None)
    response = client.post(BASE, json=review_payload)
    assert response.status_code == 409
