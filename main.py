import base64
with open('result.txt','r') as f: encoded = f.read()
exec(base64.b64decode(encoded).decode('utf-8'))
