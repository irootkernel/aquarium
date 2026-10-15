from greet import greeting


def test_named_greeting():
    assert greeting("Ada") == "Hello, Ada!"


def test_world_greeting():
    assert greeting("world") == "Hello, world!"
