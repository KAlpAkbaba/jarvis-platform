f = open('/app/core/assistant.py', 'r')
content = f.read()
f.close()

old = '''            content = result.get("not_icerik") or text'''

new = '''            import re as _re5
            content = result.get("not_icerik")
            if not content:
                content = _re5.sub(r"^(hatirlatici ekle|hatirlatici|alarm|remind)\s*", "", text, flags=_re5.IGNORECASE).strip()
            if not content:
                content = text'''

if old in content:
    content = content.replace(old, new)
    open('/app/core/assistant.py', 'w').write(content)
    print('Hatirlatici OK!')
else:
    print('BULUNAMADI')
    idx = content.find('HATIRLATICI')
    print(repr(content[idx:idx+300]))
