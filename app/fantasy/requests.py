import datetime
import hashlib
import os
import re
import sys
import time

import requests
from requests.exceptions import HTTPError
from django.conf import settings

HOST = 'https://api.sportsdata.io/v3/mlb/'
KEY = os.environ.get('SPORTDATAIO_KEY', '')

def get(url, args=[], stream=False):
  try:
    if args:
      params = dict(f.split('=') for f in args)
    else:
      params = {}

    params.update(get_auth())

    url = HOST + url
    response = requests.get(
      url,
      params=params,
      stream=stream
    )
    response.raise_for_status()

    return {
      'status': settings.RESPONSE['STATUS_OK'],
      'response': response.json()
    }

  except requests.Timeout:
    return {
      'status': settings.RESPONSE['STATUS_ERROR'],
      'response': f'HTTP timeout when downloading: {url}'
    }
  except requests.exceptions.ConnectionError as e:
    return {
      'status': settings.RESPONSE['STATUS_ERROR'],
      'response': f'HTTP Connection Error when downloading: {url}'
    }
  except HTTPError as http_err:
    return {
      'status': settings.RESPONSE['STATUS_ERROR'],
      'response': f'HTTP error occurred: {http_err}'
    }

def get_auth():
  params = {
    'key': KEY
  }
  
  return params
