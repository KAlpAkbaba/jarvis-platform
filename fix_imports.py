import os

files = []
for root, dirs, filenames in os.walk('.'):
    for fn in filenames:
        if fn.endswith('.py'):
            files.append(os.path.join(root, fn))

for f in files:
    try:
        content = open(f).read()
        if 'sounddevice' in content or 'pyaudio' in content or 'piper' in content:
            content = content.replace(
                '# import sounddevice', '# # import sounddevice'
            ).replace(
                '# from sounddevice', '# # from sounddevice'
            ).replace(
                '# import pyaudio', '# # import pyaudio'
            ).replace(
                '# from pyaudio', '# # from pyaudio'
            )
            open(f, 'w').write(content)
            print(f'Duzeltildi: {f}')
    except:
        pass
print('Tamamlandi!')
