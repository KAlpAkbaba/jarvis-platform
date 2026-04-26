f = open('/app/core/assistant.py', 'r')
content = f.read()
f.close()

idx = content.find('not_icerik') 
print('not_icerik override:')
print(repr(content[idx-50:idx+200]))
