# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.router import Router, normalize


def test_normalize():
    assert normalize("Istanbul") == "istanbul"
    assert normalize("muzik") == "muzik"
    print("test_normalize OK")

def test_route_ses_artir():
    r = Router()
    assert r.route("sesi artir") == "ses_artir"
    print("test_route_ses_artir OK")

def test_route_notlar():
    r = Router()
    assert r.route("notlarimi goster") == "notlar"
    print("test_route_notlar OK")

def test_route_hatirlaticilar():
    r = Router()
    assert r.route("planlarimi goster") == "hatirlaticilar"
    print("test_route_hatirlaticilar OK")

def test_route_muzik():
    r = Router()
    assert r.route("cal") == "muzik"
    print("test_route_muzik OK")

def test_extract_number():
    r = Router()
    assert r.extract_number("2 numara") == 2
    print("test_extract_number OK")

def test_extract_verbal_number():
    r = Router()
    assert r.extract_verbal_number("iki") == 2
    assert r.extract_verbal_number("bir") == 1
    print("test_extract_verbal_number OK")

if __name__ == "__main__":
    test_normalize()
    test_route_ses_artir()
    test_route_notlar()
    test_route_hatirlaticilar()
    test_route_muzik()
    test_extract_number()
    test_extract_verbal_number()
    print("\nTum testler gecti!")