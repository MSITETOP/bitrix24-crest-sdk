from crest import CRest

bx24 = CRest('4c0593136ca5cde131aa546feda75661')

arParamsInstall = {
    "DOMAIN": "site.t2.ipg4you.com", 
    "PROTOCOL": "1", 
    "LANG": "ru", 
    "APP_SID": "b097a4d6b194500574aed18146195772",
    "AUTH_ID": "8696b963005f81fe005dd2fe00000015201c07fc19d8463f5ed52f82a810e6c40b945c", 
    "AUTH_EXPIRES": "3600",   
    "REFRESH_ID": "8615e163005f81fe005dd2fe00000015201c078c4165a09c2763c22a83c7587764576d",
    "member_id": "4c0593136ca5cde131aa546feda75661",
    "status": "F",  
    "PLACEMENT": "DEFAULT",  
}
arSettings = bx24.installApp(arParamsInstall)

print(arSettings)
