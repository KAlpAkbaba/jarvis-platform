f = open('/app/core/assistant.py', 'rb')
raw = f.read()
f.close()

# Bozuk satiri bul ve degistir
old_line = b'            content = result.get("not_i\xef\xbf\xbdrik") or text'
new_line = b'''            import re as _re6
            content = result.get("not_icerik")
            if not content:
                content = _re6.sub(rb"^(hatirlatici ekle|hatirlatici|alarm)\\s*".decode(), "", text, flags=_re6.IGNORECASE).strip()
            if not content:
                content = text'''

if old_line in raw:
    raw = raw.replace(old_line, new_line.encode())
    f = open('/app/core/assistant.py', 'wb')
    f.write(raw)
    f.close()
    print('OK - bozuk satir duzeltildi!')
else:
    # Farkli encoding dene
    for enc in [b'\xef\xbf\xbd', b'\xc3\xa7', b'\x9c']:
        test = b'not_i' + enc + b'erik'
        if test in raw:
            print('Bulunan encoding:', enc.hex())
            idx = raw.find(test)
            print('Etraf:', raw[idx-20:idx+30])
