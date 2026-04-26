f = open('/app/core/assistant.py', 'rb')
raw = f.read()
f.close()

old = b'            content = result.get("not_i\xef\xbf\xbderik") or text'
new = b'''            import re as _re6
            content = result.get("not_icerik")
            if not content:
                content = __import__("re").sub(r"^(hatirlatici ekle|hatirlatici|alarm)\\s*", "", text, flags=__import__("re").IGNORECASE).strip()
            if not content:
                content = text'''

if old in raw:
    raw = raw.replace(old, new)
    open('/app/core/assistant.py', 'wb').write(raw)
    print('OK!')
else:
    print('BULUNAMADI, farkli deneniyor...')
    idx = raw.find(b'not_i\xef\xbf\xbd')
    print('Tam bayt:', raw[idx-30:idx+40])
