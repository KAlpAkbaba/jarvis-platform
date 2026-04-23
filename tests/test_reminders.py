# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.reservation import parse_date, parse_number, normalize, airport_code


def test_parse_date_numeric():
    result = parse_date("5 haziran")
    assert result is not None
    assert "-06-05" in result
    print("test_parse_date_numeric OK")

def test_parse_date_verbal():
    result = parse_date("bir mayis")
    assert result is not None
    assert "-05-01" in result
    print("test_parse_date_verbal OK")

def test_parse_number_digit():
    assert parse_number("2 kisili") == 2
    print("test_parse_number_digit OK")

def test_parse_number_verbal():
    assert parse_number("iki kisi") == 2
    assert parse_number("bir") == 1
    print("test_parse_number_verbal OK")

def test_airport_code():
    assert airport_code("istanbul") == "IST"
    assert airport_code("kibris") == "ECN"
    assert airport_code("ankara") == "ESB"
    print("test_airport_code OK")

def test_normalize():
    assert normalize("Istanbul") == "istanbul"
    assert normalize("Kibris") == "kibris"
    print("test_normalize OK")

if __name__ == "__main__":
    test_normalize()
    test_parse_date_numeric()
    test_parse_date_verbal()
    test_parse_number_digit()
    test_parse_number_verbal()
    test_airport_code()
    print("\nTum testler gecti!")