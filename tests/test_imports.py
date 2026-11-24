"""Vérifie que les paquets du projet s'importent (garde-fou du squelette)."""


def test_packages_import():
    import app
    import mlops

    assert app.__doc__
    assert mlops.__doc__
