f = open('/app/core/assistant.py', 'r')
content = f.read()
f.close()

idx = content.find('NOT_AL')
print('NOT_AL index:', idx)
print(repr(content[idx:idx+300]))
