"""
Wyjątki generatora paragonów
============================

Dedykowane klasy wyjątków dla generatora syntetycznych paragonów.
"""


class ReceiptGeneratorError(Exception):
    """Bazowa klasa dla wszystkich wyjątków w generatorze paragonów."""
    pass


class ConfigError(ReceiptGeneratorError):
    """Wyjątek zgłaszany przy problemach z konfiguracją."""
    pass


class CorpusError(ReceiptGeneratorError):
    """Wyjątek zgłaszany przy problemach z korpusem danych."""
    pass


class GenerationError(ReceiptGeneratorError):
    """Wyjątek zgłaszany przy problemach z generowaniem paragonu."""
    pass


class LayoutError(ReceiptGeneratorError):
    """Wyjątek zgłaszany przy problemach z układem paragonu."""
    pass