import logging
import requests
import json

class CRest(object):
  BATCH_COUNT = 50

  C_REST_WEB_HOOK_URL = False  #url on creat Webhook 
  #OR
  C_REST_CLIENT_ID = 'Application ID' # Application ID
  C_REST_CLIENT_SECRET = 'Application key'# Application key

  C_REST_IGNORE_SSL = True # turn off validate ssl by curl

  C_REST_TIMEOUT = 30 # timeout by curl

  def __init__(self, member_id = ''):
    self.__member_id = member_id

  # call where install application even url
  def installApp(self, arParams):
    result = {
      'rest_only': True,
      'install': False
    };

    if arParams.get('event') == 'ONAPPINSTALL' and not arParams.get('auth'):
      result['install'] = self.__setAppSettings(arParams.get('auth'), True)
    elif arParams['PLACEMENT'] == 'DEFAULT':
        result['rest_only'] = False;
        arSettings = {
          'access_token': arParams.get('AUTH_ID'),
          'expires_in': arParams.get('AUTH_EXPIRES'),
          'application_token': arParams.get('APP_SID'),
          'refresh_token': arParams.get('REFRESH_ID'),
          'domain': arParams.get('DOMAIN'),
          'client_endpoint': 'https://' + arParams.get('DOMAIN') + '/rest/',
        }
        result['install'] = self.__setAppSettings(arSettings, True);

    logging.debug({
      'function': 'installApp',
      'request': arParams,
      'result': result
    })

    return result

  # var arParams array
  # arParams {
  #    'method'  : 'some rest method',
  #    'params'  : {}//array params of method
  # }
  # return mixed array|string|boolean curl-return or error
  def __callCurl(self, arParams):
    result = {}
    arSettings = self.__getAppSettings()

    if arSettings:
        if arParams.get('this_auth') == 'Y':
          url = 'https://oauth.bitrix.info/oauth/token/'
        else:
          url = arSettings.get("client_endpoint") + arParams.get('method') + '.json'
          if arSettings.get('is_web_hook') or arSettings.get('is_web_hook') != 'Y':
            arParams[ 'params' ][ 'auth' ] = arSettings.get('access_token')
    else:
      result['error'] = 'arSettings is not a set'
      return result

    try:
      session = requests.Session()
      session.verify = self.C_REST_IGNORE_SSL
      params = arParams.get('params')

      req  = session.post(url, data=params, timeout=self.C_REST_TIMEOUT)

      statusCode = req.status_code
      jsonBody = req.json()

      if jsonBody.get('error'):
        if ( jsonBody.get('error') == 'expired_token' or  jsonBody.get('error') == 'invalid_token' ) and not arParams.get('this_auth'):
          result = self.__GetNewAuth(arParams)
        else:
          result = jsonBody
      else:
        result = jsonBody
    except requests.exceptions.Timeout:
        result['error'] = 'Increase the Timeout'
    except requests.exceptions.TooManyRedirects:
        result['error'] = 'Tell the user their URL was bad and try a different one'
    except requests.exceptions.RequestException as e:
        result['error'] = e


    logging.debug({
      'function': 'callCurl',
      'url'    : url,
      'params' : arParams,
      'result' : result
    })

    return result

  # Generate a request for callCurl()
  # var method string
  # var params array method params
  # return mixed array|string|boolean curl-return or error
  def call(self, method, params = {}):
    arPost = {
      'method': method,
      'params': params
    }

    result = self.__callCurl(arPost)
    return result

  # example arData:
  # arData = {
  #    'find_contact' : {
  #      'method' : 'crm.duplicate.findbycomm',
  #      'params' : [ "entity_type" : "CONTACT",  "type" : "EMAIL", "values" : array("infobitrix24.com") ]
  #    },
  #    'get_contact' : {
  #      'method' : 'crm.contact.get',
  #      'params' : [ "id" : '$result[find_contact][CONTACT][0]' ]
  #    },
  #    'get_company' : {
  #      'method' : 'crm.company.get',
  #      'params' : [ "id" : '$result[get_contact][COMPANY_ID]', "select" : ["*"],]
  #    }
  # }
  # var arData array
  # var halt   integer 0 or 1 stop batch on error
  # return array
  def callBatch(self, arData, halt = 0):
    arResult = {}
    if type(arData) is dict:
      arDataRest = {
        'cmd' : {},
        'halt': halt
      }
      i = 0
      for key in arData:
        data = arData.get(key)
        if data.get('method'):
          i = i + 1
          if self.BATCH_COUNT >= i:
            if data.get('params') and len(data.get('params'))>0:
               arDataRest[ 'cmd' ][ key ] = data.get('method') + "?" + urllib.parse.urlencode(data.get('params'), doseq=True)
            else:
               arDataRest[ 'cmd' ][ key ] = data.get('method')

      if len(arDataRest) > 0:
        arPost = {
          'method' : 'batch',
          'params' : arDataRest
        }
        arResult = self.__callCurl(arPost)

    return arResult

  # Getting a new authorization and sending a request for the 2nd time
  # var arParams array request when authorization error returned
  # return array query result from $arParams
  def __GetNewAuth(self, arParams):
    result = {}
    arSettings = self.__getAppSettings()
    if arSettings:
      arParamsAuth = {
        'this_auth' : 'Y',
        'params'    :
          {
            'client_id'     : self.C_REST_CLIENT_ID,
            'grant_type'    : 'refresh_token',
            'client_secret' : self.C_REST_CLIENT_SECRET,
            'refresh_token' : arSettings.get("refresh_token"),
          }
      }

      newData = self.__callCurl(arParamsAuth)

      if self.__setAppSettings(newData):
        arParams['this_auth'] = 'N'
        result = self.__callCurl(arParams)

    return result

  # var arSettings array settings application
  # var isInstall  boolean true if install app by installApp()
  # return boolean
  def __setAppSettings(self, arSettings, isInstall = False):
    try:
      with open("settings.json", "w") as outfile:
        json.dump(arSettings, outfile)
      return True
    except:
      return False

  # return mixed setting application for query
  def __getAppSettings(self):
    if self.C_REST_WEB_HOOK_URL != False:
      arData = {
        'client_endpoint' : self.C_REST_WEB_HOOK_URL,
        'is_web_hook'     : 'Y'
      }
      return arData
    else:
      try:
        with open("settings.json", "r") as my_file:
          capitals_json = my_file.read()

        return json.loads(capitals_json)
      except:
        return False
