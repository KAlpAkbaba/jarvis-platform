with open('core/assistant.py', 'r') as f:
    content = f.read()

# speak fonksiyonunu sadece print yapacak sekilde degistir
old = """    def speak(self, text: str):
        print(f"Asistan: {text}")
        self.tts.speak(text)"""

new = """    def speak(self, text: str):
        print(f"Asistan: {text}")"""

if old in content:
    content = content.replace(old, new)
    with open('core/assistant.py', 'w') as f:
        f.write(content)
    print('assistant.py guncellendi!')
else:
    print('Pattern bulunamadi, mevcut speak:')
    idx = content.find('def speak')
    print(content[idx:idx+150])
