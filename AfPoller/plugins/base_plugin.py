"""
base

"""
import logging
import requests
import json
import os.path
from requests.auth import HTTPBasicAuth
from urllib import urlencode
from urllib import quote
import base64,hashlib,hmac,datetime
import xml.etree.ElementTree as Xml_Tree
import re

# from urllib2 import build_opener, install_opener,urlopen,HTTPPasswordMgrWithDefaultRealm,HTTPBasicAuthHandler
from urlparse import urlparse

LOGGER = logging.getLogger(__name__)

class Plugin(object):
    ID = "com.generic"

    @staticmethod
    def reformat_metric_name(ad_metric_name):
        fixups = [(r'\.| |\\+|/+', '_'),('\|', '.'),(r'\(|\)','_'),(r'-','_'),(r'\:','_')]
        final_fixups = [(r'_+', '_'),(r'(_+$)|(^_+)','')]

        clean_metric_name = ad_metric_name
        for (look_for,replace_with) in fixups + final_fixups:
            clean_metric_name = re.sub(look_for,replace_with, clean_metric_name)

        return clean_metric_name

    def __init__(self):
        self.current_data = None
        self.metric_data = None
        self.pref_file_name = os.path.dirname(os.path.realpath(__file__)) + '/pref.json'
        self.pref = {}

    def add_metrics(self, data):
        raise Exception("Must override this method")

    @staticmethod
    def load_json_from_file(self, filename):
        data = {}
        if os.path.isfile(filename):
            json_data = open(filename)
            if (json_data):
                data = json.load(json_data)
        else:
            self.save_pref()
        return data

    def get_pref(self):
        self.pref = self.load_json_from_file(self, self.pref_file_name)

        return self.pref

    def save_pref(self):
        with open(self.pref_file_name, 'w') as outfile:
            json.dump(self.pref, outfile)

    def append_value_to_metrics(self, metrics, key, val):
        try:
            print(' append_value_to_metrics  ', metrics, key, val)
            if not key in metrics.keys():
                    metrics[key] = []
            if val:
                metrics[key].append( val )

        except Exception as e:
            LOGGER.error('Faild to append value to metrics dict: %r', e)

    def parse_metricpath(self, metricpath):
        metrics = {}
        # trim spaces
        metricpath = metricpath.replace(' ', '')
        ms = metricpath.split(',')

        for v in ms:
            if (v.find('%') > 0):
                val = v.split('%')
                self.append_value_to_metrics(metrics, val[0], val[1])
            else:
                self.append_value_to_metrics(metrics, v, None)

        return metrics



class AmazonAPIPlugin(Plugin):
    """
    Extend plugin class for Amazon signed requests and XML responses
    """

    XML_EMPTY = Xml_Tree.XML("<xml />")

    def __init__(self, appname, key_id, secret_key, action, params,hostname='monitoring.amazonaws.com',
                 data=None,last_run_data=None):
        super(AmazonAPIPlugin, self).__init__()
        self.appname = appname
        self.key_id = key_id
        self.secret_key = secret_key
        self.hostname = hostname
        self.action = action
        self.params = params
        self.data = data
        self.last_run_data = last_run_data
        if data is None:
            self.no_network = False
        else:
            self.no_network = True

    def get_data(self, extra_params=None):
        """
        Get a response from a signed Amazon AWS url
        """
        if not extra_params:
            extra_params = {}
        std_params = {'Version': '2010-08-01', 'AWSAccessKeyId': self.key_id, 'SignatureMethod': 'HmacSHA256',
                      'SignatureVersion': '2', 'Action': self.action}

        now = datetime.datetime.utcnow()
        std_params['Timestamp'] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        params = std_params.copy()
        params.update(self.params)
        params.update(extra_params)
        # self.extra = extra_params

        keys = sorted(params.keys())
        values = []
        for k in keys:
            values.append(unicode(params.get(k)))
        # values = map(params.get, keys)
        query_string = urlencode( list(zip(keys,values)) )

        # construct the string to sign
        string_to_sign = '\n'.join(['GET', self.hostname, '/', query_string])

        # sign the request
        signature = quote(base64.b64encode(hmac.new(
            key=self.secret_key,
            msg=string_to_sign.encode('UTF-8'),
            digestmod=hashlib.sha256).digest()))

        url = 'https://' + self.hostname + '/?' + query_string + '&Signature=' + signature
        LOGGER.debug("%s",params)
        LOGGER.debug("%s",url)
        if self.no_network:
            return self.data

        try:
            response = requests.get(url)
            data = response.text
            LOGGER.debug("RAW Amazon RESULT\n%s" % data)
            return Xml_Tree.fromstring(data) if data else AmazonAPIPlugin.XML_EMPTY
        except Exception as error:
            LOGGER.error('Amazon error: %r', error)

        return AmazonAPIPlugin.XML_EMPTY

    def poll(self, extra_params=None):
        """Poll data source to get metrics"""
        if not extra_params: extra_params = {}
        data = self.get_data(extra_params)
        if data != AmazonAPIPlugin.XML_EMPTY:
            self.add_metrics(data)

class RESTAPIPlugin(Plugin):
    """Extend the Plugin class overriding poll for targets that provide data
    via HTTP protocol.

    """

    def __init__(self, url, username, password, data=None, last_run_data=None):
        super(RESTAPIPlugin, self).__init__()
        self.url = url
        self.username = username
        self.password = password
        pr = urlparse(url)
        self.hostname = pr.hostname
        if data is None:
            self.no_network = False
        else:
            self.no_network = True
        self.data = data
        self.last_run_data = last_run_data


    def get_data(self):
        """
        Get a response from a url with a user name and password
        """
        auth = HTTPBasicAuth(self.username,self.password)
        try:
            response = requests.get(self.url,auth=auth)
        except Exception as e:
            raise e
        return response



    def poll(self):
        """Poll data source to get metrics"""
        data = self.get_data()
        if data:
            self.add_metrics(data)


class JSONStatsPlugin(RESTAPIPlugin):
    """Extend the Plugin overriding poll for targets that provide JSON output
    for stats collection

    """
    def get_data(self):
        """Fetch the data from the stats URL

        :rtype: dict

        """
        if self.no_network:
            return self.data

        data = RESTAPIPlugin.get_data(self)
        try:
            LOGGER.debug("RAW APPDYNAMICS RESULT\n%s" % data.text)
            return data.json() if data else {}
        except Exception as error:
            LOGGER.error('JSON decoding error: %r', error)
        return {}

    def poll(self):
        """Poll HTTP JSON endpoint for stats data"""
        # self.initialize()
        data = self.get_data()
        if data:
            self.add_metrics(data)
        #self.finish()

class RESTAPINotAuthPlugin(Plugin):
    """Extend the Plugin class overriding poll for targets that provide data
    via HTTP protocol.

    """

    def __init__(self, key, app_id, metricpath, last_run_data=None):
        super(RESTAPINotAuthPlugin, self).__init__()
        self.key = key
        self.app_id = app_id
        self.metricpath = metricpath
        self.metrics = self.parse_metricpath(metricpath)
        self.url = self.default_url(app_id);
        self.last_run_data = last_run_data


    def get_data(self, metric, value, saveLastSync = 0):
        """
        Get a response from a url with a key in header
        """

        last_sync = self.last_sync()
        payload = {'names': metric}
        headers = {'X-Api-Key': self.key}

        if last_sync:
            LOGGER.debug('last sync found ' + last_sync)
            payload['from'] = last_sync

        if value:
            payload['values'] = value

        LOGGER.debug('metricpath ' + self.metricpath)
        try:
            response = requests.get(self.url, params=payload, headers=headers)
            LOGGER.debug('sending headers ' + response.url)
            if (response.status_code != 200):
                raise Exception(u"response code: %s from url %s" % (response.status_code, response.url))

            if saveLastSync:
                self.last_sync(update=1)

        except Exception as e:
            raise e

        return response.json() if response else {}


    def poll(self):
        """Poll data source to get metrics"""

        i = len(self.metrics)
        for n, v in self.metrics.items():

            if --i <= 0 :
                data = self.get_data(n, v, saveLastSync = 1)
            else:
                data = self.get_data(n, v)

            if data:
                LOGGER.debug('adding metric')
                self.add_metrics(data)


