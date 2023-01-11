from crest import CRest

bx24 = CRest('member_id')

r = bx24.call("app.info", {})
#r.get('result').get('ID')
print(r)
