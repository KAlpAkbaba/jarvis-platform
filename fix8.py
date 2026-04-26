f = open('/app/core/assistant.py', 'r')
content = f.read()
f.close()

idx = content.find('HATIRLATICI":')
print(repr(content[idx:idx+400]))
