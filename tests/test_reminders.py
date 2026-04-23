import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.reservation import parse_date, parse_number, normalize, airport_code


def test_parse_date_numeric():
    result = parse_date("5 Haziran")
    assert result is not None
    assert "-06-05" in result

def test_parse_date_verbal():
    result = parse_date("bir mayis")
    assert result is not None
    assert "-05-01" in result

def test_parse_number_digit():
    assert parse_number("2 kisilik") == 2

def test_parse_number_verbal():
    assert parse_number("iki kisi") == 2
    assert parse_number("bir") == 1

def test_airport_code():
    assert airport_code("istanbul") == "IST"
    assert airport_code("kibris") == "ECN"
    assert airport_code("ankara") == "ESB"

def test_normalize():
    assert normalize("stanbul") == "istanbul"
    assert normalize("Kibris") == "kibris"

if __name__ == "__main__":
    test_parse_date_numeric()
    test_parse_date_verbal()
    test_parse_number_digit()
    test_parse_number_verbal()
    test_airport_code()
    test_normalize()
    print("Tum testler gecti!")
