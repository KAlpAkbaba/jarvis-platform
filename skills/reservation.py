import asyncio
import re
from urllib.parse import quote
from datetime import datetime
from playwright.async_api import async_playwright
from database.repository import save_reservation, get_reservations


AIRPORT_CODES = {
    "istanbul": "IST", "ankara": "ESB", "izmir": "ADB",
    "antalya": "AYT", "kibris": "ECN", "lefkosa": "ECN",
    "larnaka": "LCA", "bodrum": "BJV", "dalaman": "DLM",
    "trabzon": "TZX", "adana": "ADA", "kayseri": "ASR",
}

SLUGS = {
    "IST": "istanbul-ataturk-havalimani-ista-ist",
    "ESB": "ankara-ankara-esenboga-havalimani-ista-esb",
    "ADB": "izmir-adnan-menderes-havalimani-ista-adb",
    "AYT": "antalya-antalya-havalimani-ista-ayt",
    "ECN": "ecn-ercan-intl-havalimani-ista-ecn",
    "LCA": "larnaka-larnaka-intl-havalimani-ista-lca",
    "BJV": "bodrum-milas-bodrum-havalimani-ista-bjv",
    "DLM": "dalaman-dalaman-havalimani-ista-dlm",
    "TZX": "trabzon-trabzon-havalimani-ista-tzx",
    "ADA": "adana-adana-havalimani-ista-ada",
    "ASR": "kayseri-erkilet-havalimani-ista-asr",
}

INTERNATIONAL = {"ECN", "LCA"}

MONTHS = {
    "ocak": 1, "subat": 2, "mart": 3, "nisan": 4,
    "mayis": 5, "haziran": 6, "temmuz": 7, "agustos": 8,
    "eylul": 9, "ekim": 10, "kasim": 11, "aralik": 12,
    "mayis": 5, "subat": 2, "agustos": 8, "eyl�l": 9, "kasim": 11, "aralik": 12,
    "mais": 5, "maiz": 5,
}

NUMBERS = {
    "bir": 1, "iki": 2, "uc": 3, "uch": 3, "dort": 4, "bes": 5,
    "alti": 6, "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10,
    "iki": 2, "��": 3, "d�rt": 4, "bes": 5, "alti": 6,
}


def normalize(text):
    tr = {
        chr(305): 'i', chr(304): 'i', chr(287): 'g', chr(286): 'g',
        chr(252): 'u', chr(220): 'u', chr(351): 's', chr(350): 's',
        chr(246): 'o', chr(214): 'o', chr(231): 'c', chr(199): 'c',
        'I': 'i',
    }
    for k, v in tr.items():
        text = text.replace(k, v)
    return text.lower()


def airport_code(city: str) -> str:
    if not city:
        return "IST"
    city_clean = city.replace('(varsayilan)', '').replace('varsayilan', '').strip()
    return AIRPORT_CODES.get(normalize(city_clean), city_clean.upper()[:3])


def parse_date(text: str) -> str:
    text = normalize(text.lower().strip())
    now = datetime.now()
    year = now.year

    direct = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
    if direct:
        return direct.group()

    month = None
    for name, num in sorted(MONTHS.items(), key=lambda x: -len(x[0])):
        if name in text:
            month = num
            text = text.replace(name, '').strip()
            break

    day = None
    digit = re.search(r'\b(\d{1,2})\b', text)
    if digit:
        day = int(digit.group(1))
    else:
        for word, val in sorted(NUMBERS.items(), key=lambda x: -len(x[0])):
            if word in text:
                day = val
                break

    if day and month:
        try:
            dt = datetime(year, month, day)
            if dt < now:
                dt = datetime(year + 1, month, day)
            return dt.strftime('%Y-%m-%d')
        except:
            return None
    return None


def parse_number(text: str) -> int:
    text_lower = normalize(text.lower())
    digit = re.search(r'\d+', text)
    if digit:
        return int(digit.group())
    for word, val in NUMBERS.items():
        if word in text_lower:
            return val
    return 1


def sync_run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except:
        return asyncio.run(coro)


async def _booking_search(city: str, check_in: str, check_out: str, guests: int):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        url = (
            f"https://www.booking.com/searchresults.tr.html"
            f"?ss={quote(city, encoding='utf-8')}"
            f"&checkin={check_in}&checkout={check_out}"
            f"&group_adults={guests}&no_rooms=1"
            f"&selected_currency=TRY&order=class"
        )
        await page.goto(url)
        await page.wait_for_timeout(4000)

        for sel in ['[aria-label="Kapat"]', '[aria-label="Close"]', '[data-testid="modal-close-button"]']:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    await page.wait_for_timeout(500)
                    break
            except:
                continue

        hotels = []
        cards = await page.query_selector_all('[data-testid="property-card"]')
        for card in cards[:5]:
            try:
                name_el = await card.query_selector('[data-testid="title"]')
                price_el = await card.query_selector('[data-testid="price-and-discounted-price"]')
                score_el = await card.query_selector('[data-testid="review-score"]')
                link_el = await card.query_selector('a[data-testid="title-link"]')

                name = await name_el.inner_text() if name_el else ""
                price = await price_el.inner_text() if price_el else "Fiyat yok"
                score_text = await score_el.inner_text() if score_el else "-"
                link = await link_el.get_attribute("href") if link_el else ""

                score_match = re.search(r'[\d,\.]+', score_text)
                score = score_match.group() if score_match else "-"

                if name:
                    hotels.append({"name": name.strip(), "price": price.strip(),
                                   "score": score, "source": "Booking.com", "link": link})
            except:
                continue

        await browser.close()
        return hotels


async def _flight_search(from_slug: str, to_slug: str, date_fmt: str, passengers: int, geotrip: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        url = (
            f"https://www.enuygun.com/ucak-bileti/arama/"
            f"{from_slug}-{to_slug}/"
            f"?gidis={date_fmt}&yetiskin={passengers}"
            f"&sinif=ekonomi&save=1&geotrip={geotrip}&trip={geotrip}"
        )
        print(f"Enuygun URL: {url}")
        await page.goto(url)
        await page.wait_for_timeout(6000)

        for sel in ['#CybotCookiebotDialogBodyButtonAccept', 'button:has-text("KABUL ET")']:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    await page.wait_for_timeout(1000)
                    break
            except:
                continue

        flights = []
        for sel in ['.flight-card', '[data-testid="flight-card"]', '.result-item']:
            cards = await page.query_selector_all(sel)
            if cards:
                for card in cards[:5]:
                    try:
                        airline_el = await card.query_selector('.airline-name, [class*="airline"]')
                        price_el = await card.query_selector('.price, [class*="price"]')
                        airline = await airline_el.inner_text() if airline_el else "?"
                        price = await price_el.inner_text() if price_el else "?"
                        flights.append({"airline": airline, "price": price, "source": "Enuygun.com"})
                    except:
                        continue
                break

        await browser.close()
        return flights


class ReservationSkill:
    def __init__(self):
        self._dialog = {"active": False, "step": None, "data": {}}

    def dialog_active(self) -> bool:
        return self._dialog["active"]

    def _set(self, step: str, data: dict):
        self._dialog = {"active": True, "step": step, "data": data}

    def _reset(self):
        self._dialog = {"active": False, "step": None, "data": {}}

    def handle(self, text: str, details: dict) -> str:
        text_lower = text.lower()
        kind = details.get("t�r", "") if details else ""

        if kind == "otel" or any(k in text_lower for k in ["otel", "konaklama"]):
            city = details.get("sehir") if details else None
            check_in = details.get("giris_tarihi") if details else None
            check_out = details.get("�ikis_tarihi") if details else None
            guests = details.get("kisi", 2) if details else 2

            if not city:
                self._set("hotel_city", {})
                return "Hangi sehirde otel arayayim?"

            self._set("hotel_confirm", {"city": city, "check_in": check_in,
                                         "check_out": check_out, "guests": guests})
            return f"{city} i�in otel arayayim, dogru mu?"

        elif kind == "u�ak" or any(k in text_lower for k in ["u�ak", "u�us", "bilet"]):
            from_city = details.get("nereden") or "stanbul"
            to_city = details.get("nereye") if details else None
            date = details.get("tarih") if details else None
            passengers = details.get("kisi", 1) if details else 1

            if not to_city:
                self._set("flight_to", {"from": from_city, "passengers": passengers})
                return "Nereye u�mak istiyorsunuz?"

            if not date:
                self._set("flight_date", {"from": from_city, "to": to_city, "passengers": passengers})
                return f"{from_city} ? {to_city} i�in hangi tarihte u�mak istiyorsunuz?"

            return self._search_flights(from_city, to_city, date, passengers)

        return "Otel mi, u�ak mi, yoksa restoran mi arayayim?"

    def continue_dialog(self, text: str) -> str:
        step = self._dialog["step"]
        data = self._dialog["data"]
        text_lower = text.lower().strip()

        if step == "hotel_city":
            city = text.strip().title()
            self._set("hotel_confirm", {"city": city})
            return f"{city} i�in otel arayayim, dogru mu?"

        elif step == "hotel_confirm":
            if any(k in text_lower for k in ["evet", "dogru", "tamam", "olur"]):
                city = data["city"]
                check_in = data.get("check_in")
                check_out = data.get("check_out")
                guests = data.get("guests", 2)
                if check_in and check_out:
                    return self._search_hotels(city, check_in, check_out, guests)
                elif check_in:
                    self._set("hotel_checkout", data)
                    return "�ikis tarihi ne olsun?"
                else:
                    self._set("hotel_checkin", data)
                    return "Giris tarihi ne olsun?"
            else:
                self._set("hotel_city", {})
                return "Hangi sehirde otel arayayim?"

        elif step == "hotel_checkin":
            date = parse_date(text)
            if date:
                data["check_in"] = date
                self._set("hotel_checkout", data)
                return "�ikis tarihi ne olsun?"
            return "Anlamadim, �rnek: 5 Haziran"

        elif step == "hotel_checkout":
            date = parse_date(text)
            if date:
                data["check_out"] = date
                self._set("hotel_guests", data)
                return "Ka� kisilik oda olsun?"
            return "Anlamadim, �rnek: 8 Haziran"

        elif step == "hotel_guests":
            guests = parse_number(text)
            return self._search_hotels(data["city"], data["check_in"], data["check_out"], guests)

        elif step == "hotel_select":
            num = parse_number(text) - 1
            hotels = data.get("hotels", [])
            if 0 <= num < len(hotels):
                hotel = hotels[num]
                if hotel.get("link"):
                    import webbrowser
                    webbrowser.open(hotel["link"])
                save_reservation(
                    type="otel", city=data["city"],
                    check_in=datetime.strptime(data["check_in"], "%Y-%m-%d"),
                    check_out=datetime.strptime(data["check_out"], "%Y-%m-%d"),
                    guests=data.get("guests", 2), details=hotel
                )
                self._set("flight_offer", data)
                return f"{hotel['name']} se�ildi. {data['city']} i�in u�ak bileti de ayarlamami ister misiniz?"

            if any(k in text_lower for k in ["hayir", "yok", "istemiyorum"]):
                self._reset()
                return "Tamam, rezervasyon tamamlandi."
            return f"1 ile {len(hotels)} arasinda numara s�yleyin."

        elif step == "flight_offer":
            if any(k in text_lower for k in ["evet", "olur", "istiyorum", "tamam"]):
                city = data.get("city", "")
                check_in = data.get("check_in", "")
                return self._search_flights("stanbul", city, check_in, data.get("guests", 1))
            self._reset()
            return "Tamam, iyi tatiller!"

        elif step == "flight_to":
            to_city = text.strip().title()
            data["to"] = to_city
            self._set("flight_date", data)
            return f"{data.get('from', 'stanbul')} ? {to_city} i�in hangi tarihte u�mak istiyorsunuz?"

        elif step == "flight_date":
            date = parse_date(text)
            if date:
                return self._search_flights(data.get("from", "stanbul"), data["to"],
                                            date, data.get("passengers", 1))
            return "Anlamadim, �rnek: 5 Haziran"

        elif step == "flight_select":
            num = parse_number(text) - 1
            flights = data.get("flights", [])
            if 0 <= num < len(flights):
                flight = flights[num]
                save_reservation(
                    type="u�ak", from_city=data.get("from"),
                    to_city=data.get("to"),
                    check_in=datetime.strptime(data["date"], "%Y-%m-%d"),
                    guests=data.get("passengers", 1), details=flight
                )
                self._reset()
                return f"{flight['airline']} se�ildi. Rezervasyonunuz kaydedildi!"

            if any(k in text_lower for k in ["hayir", "yok"]):
                self._reset()
                return "Tamam."
            return "Numara s�yleyin."

        self._reset()
        return "Anlayamadim, tekrar s�yler misiniz?"

    def _search_hotels(self, city: str, check_in: str, check_out: str, guests: int) -> str:
        print(f"Otel araniyor: {city}")
        hotels = sync_run(_booking_search(city, check_in, check_out, guests))

        if not hotels:
            return f"{city} i�in Booking.com a�ildi. Ekrandan oteli se�in."

        hotels.sort(key=lambda x: float(x["score"].replace(",", ".")) if x["score"] not in ["-", ""] else 0, reverse=True)
        self._set("hotel_select", {"city": city, "check_in": check_in,
                                    "check_out": check_out, "guests": guests, "hotels": hotels})
        result = f"{city} i�in en iyi oteller. "
        for i, h in enumerate(hotels[:3], 1):
            result += f"{i}. {h['name']}, fiyat {h['price']}, puan {h['score']}. "
        return result + "Hangisini tercih edersiniz? Numara s�yleyin."

    def _search_flights(self, from_city: str, to_city: str, date: str, passengers: int) -> str:
        print(f"U�us araniyor: {from_city} ? {to_city}")
        from_code = airport_code(from_city)
        to_code = airport_code(to_city)
        from_slug = SLUGS.get(from_code, normalize(from_city) + "-ista-" + from_code.lower())
        to_slug = SLUGS.get(to_code, normalize(to_city) + "-ista-" + to_code.lower())

        dt = datetime.strptime(date, "%Y-%m-%d")
        date_fmt = dt.strftime("%d.%m.%Y")
        geotrip = "international" if from_code in INTERNATIONAL or to_code in INTERNATIONAL else "domestic"

        flights = sync_run(_flight_search(from_slug, to_slug, date_fmt, passengers, geotrip))

        if not flights:
            return f"{from_city} ? {to_city} i�in Enuygun.com a�ildi."

        self._set("flight_select", {"from": from_city, "to": to_city,
                                     "date": date, "passengers": passengers, "flights": flights})
        result = f"{from_city} ? {to_city} i�in en uygun u�uslar. "
        for i, f in enumerate(flights[:3], 1):
            result += f"{i}. {f['airline']}, fiyat {f['price']}. "
        return result + "Hangisini tercih edersiniz?"


