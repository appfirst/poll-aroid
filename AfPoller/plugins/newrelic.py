#!/usr/bin/env python

'''
NewRelic

'''
import logging
import time
from time import gmtime, strftime
from datetime import datetime, timedelta
from urllib import quote_plus
from base_plugin import RESTAPINotAuthPlugin, Plugin

LOGGER = logging.getLogger(__name__)


class NewRelic(RESTAPINotAuthPlugin):
    '''
    take in NewRelic metric path string and convert to StatsD dotted, no spaced format remove all '/', space and period characters
    replace '/' with '.' for
    '''

    def __init__(self, key, app_id, metricpath):
        super(NewRelic, self).__init__(key, app_id, metricpath)

        pref = self.get_pref()

    
    @staticmethod
    def default_url(app_id):

        return u'https://api.newrelic.com/v2/applications/%s/metrics/data.json' % (app_id)


    def last_sync(self, update=0):
        '''
        Get last sync time
        '''


        if update:
            now = time.time()
            localtime = time.localtime(now)
            offset = localtime.tm_hour - datetime.utcnow().hour
            if offset >= 0:
                offset = '+' + '%02d' % offset
            else:
                offset = '-' + '%02d' % offset
            # @TODO 
            # current_time = strftime('%Y-%m-%dT%H:%M:%S+00:00', gmtime())
            current_time = strftime('%Y-%m-%dT%H:%M:%S', gmtime())
            # current_time = current_time.replace('+00', offset) 
            LOGGER.debug(' last sync time updated to: ' + current_time)


            self.pref['last_sync'] = current_time;
            self.save_pref()
        else:
            if  self.pref.has_key('last_sync'):
                return self.pref['last_sync']
            else:
                return None


    def add_metrics(self, data):

        statsd_data = []

        if (data['metric_data'] and data['metric_data']['metrics']):
            print (u'metrics from date %s' %data['metric_data']['from'])
            for chunk in data['metric_data']['metrics']:
                LOGGER.debug(u'metrics found for %s' %chunk['name'])
                if (chunk['timeslices']):
                    for metric in chunk['timeslices']:
                        print(metric['values'])
                        statsd_data.append(metric['values'])

        else:
            raise Exception('no metrics found in response')

        self.metric_data = {'metrics' : {}}
        m = Plugin.reformat_metric_name(chunk['name'])
        if len(statsd_data) > 0:
            last_metric = statsd_data[-1]
            mname = self.metricpath.replace('/', '.')
            for n, v in last_metric.items():
                n = n.replace('_', '.')
                self.metric_data['metrics'][n] = v
    


