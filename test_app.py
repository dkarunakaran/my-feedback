from app import insert_types


def test_insert_types():
    assert insert_types() == "Not allowed in prod enviornment"
