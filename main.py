import base64
with open('result.txt','r')as f:c=f.read()
exec(base64.b64decode(c).decode('utf-8'))
