from crest import CRest

bx24 = CRest('member_id')

arSettings = bx24.installApp(arParamsInstall)

print(arSettings)
