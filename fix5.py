f = open('/app/core/assistant.py', 'r')
content = f.read()
f.close()

# Override ekle - result alindiktan hemen sonra
old = 'result = self.llm.process(text, self.context.to_list())\n        category = result.get'
new = 'result = self.llm.process(text, self.context.to_list())\n        if result.get("not_icerik") and result.get("kategori") not in ["NOT_AL","HATIRLATICI"]:\n            result["kategori"] = "NOT_AL"\n        category = result.get'

if old in content:
    content = content.replace(old, new)
    open('/app/core/assistant.py', 'w').write(content)
    print('Override eklendi!')
else:
    print('BULUNAMADI')
    idx = content.find('self.llm.process')
    print(repr(content[idx:idx+150]))
