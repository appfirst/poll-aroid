#!/usr/bin/env python

'''
NewRelic

'''
import logging
import time
from time import gmtime, strftime
from datetime import datetime
from base_plugin import RESTAPINotAuthPlugin, Plugin

LOGGER = logging.getLogger(__name__)


class NewRelic(RESTAPINotAuthPlugin):
    '''
    take in NewRelic metric path string and convert to StatsD dotted, no spaced format remove all '/', space and period characters
    replace '/' with '.' for
    '''

    def __init__(self, key, app_id, metricpath, appname):
        super(NewRelic, self).__init__(key, app_id, metricpath, appname)

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


    def add_metrics(self, data, metricName, appName):

        statsdData = {}

        if (data['metric_data'] and data['metric_data']['metrics']):

            LOGGER.debug (u'metrics from date %s' %data['metric_data']['from'])
            for chunk in data['metric_data']['metrics']:
                mName = chunk['name']
                LOGGER.debug(u'metrics found for %s' %mName)
                if (chunk['timeslices']):
                    for metric in chunk['timeslices']:
                        if not mName in statsdData.keys():
                            statsdData[mName] = []
                        statsdData[mName].append(metric['values'])

        else:
            raise Exception('no metrics found in response')

        if self.metric_data:
            LOGGER.debug(u' previous metric found %s' % (data['metric_data']['from']))
            self.pref['last_metric_found'] = 1;
        else:
            self.metric_data = {'metrics' : {}}

        if len(statsdData) > 0:
            for metric, values in statsdData.items():
                last_metric = values[-1]
                mName = metric.replace('/', '_')
                for n, v in last_metric.items():
                    if len(appName) > 0:
                        fName = appName + '.' + mName + '.' + n
                    else:
                        fName = self.appname + '.' + mName + '.' + n
                    LOGGER.debug(u' ---- add metric %s' % fName)
                    LOGGER.debug(u' ---- add value  %s' % (v))
                    self.metric_data['metrics'][fName] = v




