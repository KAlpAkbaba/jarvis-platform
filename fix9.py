f = open('/app/core/assistant.py', 'rb')
content = f.read()
f.close()

# Bozuk karakteri bul ve duzelt
content = content.replace(b'not_i\xef\xbf\xbdrik', b'not_icerik')
content = content.replace(b'not_i\xc3\xa7erik', b'not_icerik')

f = open('/app/core/assistant.py', 'wb')
f.write(content)
f.close()

# Simdi str olarak oku ve hatirlatici duzelt
f = open('/app/core/assistant.py', 'r', encoding='utf-8', errors='replace')
content = f.read()
f.close()

idx = content.find('HATIRLATICI":')
print('Mevcut kod:')
print(repr(content[idx:idx+150]))
