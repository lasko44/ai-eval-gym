from app.models import Cycle


def test_create_cycle_then_see_it_on_its_page(client):
    r = client.post("/cycles", data={
        "target_name": "llama_index_rag_demo",
        "target_url": "https://github.com/example/repo",
        "question": "Is retrieval any good on multi-hop questions?",
    }, follow_redirects=True)
    assert r.status_code == 200
    assert "llama_index_rag_demo" in r.text
    assert "multi-hop" in r.text


def test_new_cycle_starts_open(client, session):
    client.post("/cycles", data={"target_name": "x", "target_url": "u", "question": "q"})
    assert session.query(Cycle).one().stage == "open"
