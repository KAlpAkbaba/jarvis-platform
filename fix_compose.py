with open('docker-compose.yml', 'r') as f:
    content = f.read()

content = content.replace(
    '      # ports: host mode',
    '      ports:\n        - "8000:8000"'
).replace(
    '    network_mode: host\n', ''
)

with open('docker-compose.yml', 'w') as f:
    f.write(content)
print('docker-compose.yml guncellendi!')
print(content)
