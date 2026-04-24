import os

for root, dirs, filenames in os.walk('.'):
    for fn in filenames:
        if fn.endswith('.py'):
            fp = os.path.join(root, fn)
            try:
                content = open(fp).read()
                if 'piper' in content.lower() and 'import' in content:
                    content = content.replace(
                        '# from piper', '# # from piper'
                    ).replace(
                        '# import piper', '# # import piper'
                    ).replace(
                        '# from clients.piper_client', '# # from clients.piper_client'
                    ).replace(
                        '# import PiperClient', '# # import PiperClient'
                    )
                    open(fp, 'w').write(content)
                    print(f'Duzeltildi: {fp}')
            except:
                pass
print('Tamamlandi!')
