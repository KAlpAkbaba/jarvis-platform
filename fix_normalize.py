import re

with open('skills/reservation.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_fn = '''def normalize(text):
    tr = {
        chr(305): 'i', chr(304): 'i', chr(287): 'g', chr(286): 'g',
        chr(252): 'u', chr(220): 'u', chr(351): 's', chr(350): 's',
        chr(246): 'o', chr(214): 'o', chr(231): 'c', chr(199): 'c',
        'I': 'i',
    }
    for k, v in tr.items():
        text = text.replace(k, v)
    return text.lower()'''

content = re.sub(
    r'def normalize\(text.*?\).*?return text\.lower\(\)',
    new_fn,
    content,
    flags=re.DOTALL
)

with open('skills/reservation.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Guncellendi!')
