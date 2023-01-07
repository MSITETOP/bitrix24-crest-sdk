from crest import CRest

bx24 = CRest('4c0593136ca5cde131aa546feda75661')

r = bx24.call("app.info", {})
#r.get('result').get('ID')
print(r)
