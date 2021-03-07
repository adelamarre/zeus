
from src.application.adapters import AbstractAdapter


class AbstractParser:
    def __init__(self, adapter: AbstractAdapter) -> None:
        self.adapter: AbstractAdapter = adapter
        pass

    def parse(self):
        pass