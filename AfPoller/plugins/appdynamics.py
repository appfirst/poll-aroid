"""
AppDynamics

"""
import logging
from urllib import quote_plus
from base_plugin import JSONStatsPlugin, Plugin

LOGGER = logging.getLogger(__name__)


class AppDynamics(JSONStatsPlugin):
    """
    take in AppDynamics metric path string and convert to StatsD dotted, no spaced format remove all '|', space and period characters
    replace '|' with '.' for
    """
    
    @staticmethod
    def default_url(hostname,appname,metricpath):
        return u"http://%s/controller/rest/applications/%s/metric-data?metric-path=%s&time-range-type=BEFORE_NOW&duration-in-mins=5&rollup=false&output=JSON" % (hostname, quote_plus(appname), quote_plus(metricpath))


    def add_metrics(self,data):
        # Fix up metric names
        statsd_data = [] 
        for chunk in data:
            chunk['statsd'] = Plugin.reformat_metric_name(chunk['metricPath'])
            statsd_data.append(chunk)
            
        self.current_data = statsd_data
        self.metric_data = self.calc_offset(last_run_data=None, current_data=self.current_data) # Don't use a last_run data structure for now
    
    @staticmethod
    def calc_offset(last_run_data,current_data):
        """For each metric value lookup last_run value by using the metric name as a key
        then subtract last_run value from the current value and store in new dictionary with a key of metric name
        return the new dictionary
        """
        if last_run_data is None:
            last_run_data = {'metrics' : {}} # initialize this to an empty set of metrics
        results = {'metrics' : {}}
        for chunk in current_data:
            statsd_name = chunk['statsd']
            # get the last metrics value
            if len(chunk['metricValues']) > 0:
                metric_value = chunk['metricValues'][-1]['current']
                last_metric_value = last_run_data['metrics'].get(statsd_name,0)  # lookup key in last value or 0 if not found
                results['metrics'][statsd_name] = metric_value - last_metric_value
        #m[0]['metricValues'][0]['current']
        return results


