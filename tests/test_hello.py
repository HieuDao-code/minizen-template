from minizen_template.main import hello


def test_hello() -> None:
    # act
    result = hello()

    # assert
    assert result == "Hello, world!"
