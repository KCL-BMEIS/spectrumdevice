from dataclasses import dataclass
from functools import singledispatch


class DeviceConfig:
    pass


@dataclass
class CardConfig(DeviceConfig):
    name: str = 'card'
    value: int = 1


@dataclass
class SuperCardConfig(CardConfig):
    pass


@dataclass
class MockCardConfig(DeviceConfig):
    name: str = 'mock card'
    mock_value: int = 1


class TestCardConfig(CardConfig, MockCardConfig):
    pass


@singledispatch
def dispatch(d: DeviceConfig):
    return NotImplementedError()


@dispatch.register
def _(d: CardConfig):
    print("It's a card config!")


if __name__ == '__main__':

    c = SuperCardConfig()
    dispatch(c)


