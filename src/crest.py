from logging import info
from time import sleep
import requests
import urllib.parse
import os
import json

class CRest(object):
  BATCH_COUNT = 50

  C_REST_CLIENT_ID = 'local.638648ab1a8025.42091559' # Application ID
  C_REST_CLIENT_SECRET = 'I2NHy1okBCaz3MukwZeKlVkER2U1hW3IyYWu62JH7q5yssDXXO'# Application key

  C_REST_CURRENT_ENCODING = 'UTF-8' #set current encoding site if encoding unequal UTF-8 to use iconv() windows-1251

  C_REST_IGNORE_SSL = True # turn off validate ssl by curl

  C_REST_TIMEOUT = 30 # ttimeout by curl

  def __init__(self, member_id):
    self.member_id = member_id

  # Can overridden this method to change the data storage location.
  # return array setting for getAppSettings()
  def __getSettingData(self):
    try:
      with open("settings.json", "r") as my_file:
        capitals_json = my_file.read()

      return json.loads(capitals_json)
    except:
      return False

  # Can overridden this method to change the data storage location.
  # var $arSettings array settings application
  # return boolean is successes save data for setSettingData()
  def __setSettingData(self, arSettings):
    try:
      with open("settings.json", "w") as outfile:
        json.dump(arSettings, outfile)
      return True
    except:
      return False

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

    self.__setLog(
      {
        'request': arParams,
        'result': result
      },
      'installApp'
    )

    return result

  # var $arParams array
  # $arParams = [
  #    'method'  => 'some rest method',
  #    'params'  => []//array params of method
  # ];
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

    try:
      session = requests.Session()
      session.verify = self.C_REST_IGNORE_SSL
      session.timeout = self.C_REST_TIMEOUT
      params = arParams.get('params')

      req  = session.post(url, data=params)

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
        result['error'] = 'Maybe set up for a retry, or continue in a retry loop'
    except requests.exceptions.TooManyRedirects:
        result['error'] = 'Tell the user their URL was bad and try a different one'
    except requests.exceptions.RequestException as e:
        result['error'] = e


    self.__setLog(
        {
              'url'    : url,
              'params' : arParams,
              'result' : result
        },
        'callCurl'
    )

    return result

  # Generate a request for callCurl()
  # var $method string
  # var $params array method params
  # return mixed array|string|boolean curl-return or error
  def call(self, method, params = {}):
    arPost = {
      'method': method,
      'params': params
    }

    if self.C_REST_CURRENT_ENCODING != 'UTF-8':
      arPost['params'] = self.__changeEncoding(arPost.get('params'))

    result = self.__callCurl(arPost)
    return result

  # example $arData:
  # $arData = [
  #    'find_contact' => [
  #      'method' => 'crm.duplicate.findbycomm',
  #      'params' => [ "entity_type" => "CONTACT",  "type" => "EMAIL", "values" => array("infobitrix24.com") ]
  #    ],
  #    'get_contact' => [
  #      'method' => 'crm.contact.get',
  #      'params' => [ "id" => '$result[find_contact][CONTACT][0]' ]
  #    ],
  #    'get_company' => [
  #      'method' => 'crm.company.get',
  #      'params' => [ "id" => '$result[get_contact][COMPANY_ID]', "select" => ["*"],]
  #    ]
  # ];
  # var $arData array
  # var $halt   integer 0 or 1 stop batch on error
  # return array
  def callBatch(self, arData, halt = 0):
    arResult = {}
    if type(arData) is dict:
      if self.C_REST_CURRENT_ENCODING != 'UTF-8':
        arData = self.__changeEncoding(arData)

      arDataRest = {}

      if len(arDataRest) > 0:
        arDataRest['halt'] = halt
        arPost = {
          'method' : 'batch',
          'params' : arDataRest
        }
        arResult = self.__callCurl(arPost)
    
    return arResult

  # Getting a new authorization and sending a request for the 2nd time
  # var $arParams array request when authorization error returned
  # return array query result from $arParams
  def __GetNewAuth(self, arParams):
    result = {}
    arSettings = self.__getAppSettings()
    if arSettings != False:
      arParamsAuth = {
        'this_auth' : 'Y',
        'params'    :
          {
            'client_id'     : arSettings.get('C_REST_CLIENT_ID'),
            'grant_type'    : 'refresh_token',
            'client_secret' : arSettings.get('C_REST_CLIENT_SECRET'),
            'refresh_token' : arSettings.get("refresh_token"),
          }
      }

      newData = self.__callCurl(arParamsAuth)

      if self.__setAppSettings(newData):
        arParams['this_auth'] = 'N'
        result = self.__callCurl(arParams)

    return result

  # var $arSettings array settings application
  # var $isInstall  boolean true if install app by installApp()
  # return boolean
  def __setAppSettings(self, arSettings, isInstall = False):
    config = False
    if len(arSettings):
      oldData = self.__getAppSettings();
      if isInstall != True and len(oldData):
          arSettings = oldData.update(arSettings)
      config = self.__setSettingData(arSettings)
    return config

  # return mixed setting application for query
  def __getAppSettings(self):
    return self.__getSettingData()

  # var $data mixed
  # var $encoding boolean true - encoding to utf8, false - decoding
  # return string json_encode with encoding
  def __changeEncoding(self, data, encoding = True):
    return True

  # Can overridden this method to change the log data storage location.
  # var $arData array of logs data
  # var $type   string to more identification log data
  # return boolean is successes save log data
  def __setLog(self, arData, type = ''):
    info([arData, type])
  
    
