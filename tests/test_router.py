import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.router import Router


def test_route_ses_artir():
    r = Router()
    assert r.route("sesi artir") == "ses_artir"

def test_route_notlar():
    r = Router()
    assert r.route("notlarimi göster") == "notlar"

def test_route_hatirlaticilar():
    r = Router()
    assert r.route("planlarimi göster") == "hatirlaticilar"

def test_route_muzik():
    r = Router()
    assert r.route("Tarkan çal") == "muzik"

def test_extract_number():
    r = Router()
    assert r.extract_number("2 numara") == 2

def test_extract_verbal_number():
    r = Router()
    assert r.extract_verbal_number("iki") == 2
    assert r.extract_verbal_number("bir") == 1

if __name__ == "__main__":
    test_route_ses_artir()
    test_route_notlar()
    test_route_hatirlaticilar()
    test_route_muzik()
    test_extract_number()
    test_extract_verbal_number()
    print("Tum testler gecti!")
