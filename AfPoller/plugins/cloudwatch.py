"""
Amazon CloudWatch
"""
import logging
from base_plugin import AmazonAPIPlugin, Plugin
LOGGER = logging.getLogger(__name__)
import time
from datetime import datetime,timedelta
import re

class CloudWatch(AmazonAPIPlugin):
    """
    Take in CloudWatch dimensions and statistics and convert to StatsD dotted, no spaced format
    """
    def __init__(self,appname,key_id,secret_key,action,params,dimension,metricname,aws_namespace,
                 statistic="Average", unit='Percent', offset=60, hostname='monitoring.amazonaws.com',data=None,last_run_data=None):

        super(CloudWatch,self).__init__(appname,key_id,secret_key,action,params,hostname,data,last_run_data)
        self.offset = offset
        self.extra = {}
        self.extra.update(self._setup_dimension(dimension,statistic))

        self.statistic = statistic.capitalize()
        self.extra['Action'] = 'GetMetricStatistics'
        self.extra["MetricName"] = metricname
        self.extra["Namespace"] = aws_namespace
        self.extra["Period"] = 60
        if unit is not None:
            self.extra["Unit"] = unit
            self.unit = unit
        else:
            self.unit = None  # Wait for results then set Units from the result set

    @staticmethod
    def _setup_dimension(dimension, statistic):
        i = 1
        dim_values = {}
        for d in dimension:
            p = d.split(":")
            if len(p) == 2:
                dim_values["Dimensions.member.%s.Name" % i] = p[0]
                dim_values["Dimensions.member.%s.Value" % i] = p[1]
                dim_values["Statistics.member.%s" % i] = statistic
                i += 1
        return dim_values


    def poll(self,extra_params=None) :
        end = datetime.utcnow()
        start = end - timedelta(minutes=self.offset)
        self.extra['EndTime'] = end.strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.extra['StartTime'] = start.strftime('%Y-%m-%dT%H:%M:%S.%f')
        extra_params = {} if extra_params is None else extra_params
        extra_params.update(self.extra)
        super(CloudWatch,self).poll(extra_params=extra_params)


    @staticmethod
    def _get_xml_namespace(data):
        rr = re.compile(r"\{([^}]+)\}")  # use to extract toplevel namespace
        mm = rr.match(data.tag)
        xmlnamespace = "http://example.org"
        if mm.groups():
            xmlnamespace = mm.groups()[0]
        return xmlnamespace

    def add_metrics(self,data):
        # Fix up metric names
        metric_list = data.findall(".//xx:Datapoints/xx:member",namespaces={ "xx":self._get_xml_namespace(data)})
        result = {}
        ts_key = datetime.utcnow()
        for dp in metric_list:
            data = {}
            for measure in dp:
                key = re.sub("{.*\}","",measure.tag)
                if key == "Timestamp":
                    ts_key = time.strptime(measure.text, "%Y-%m-%dT%H:%M:%SZ")
                    data[key] = ts_key
                else:
                    data[key] = measure.text
                if key == "Unit" and self.unit is None:
                    self.unit = measure.text

            data["metricPath"] = "|".join([self.extra.get("Dimensions.member.1.Value","none"),self.extra.get("MetricName","none"),self.statistic,self.unit])
            result[ts_key] = data


        sorted_keys = sorted(result.keys())
        final_data = [result[x] for x in sorted_keys]
        chunk = {}
        if len(final_data) > 0:
            chunk = final_data[-1]  # get the last timestampped item
        chunk['statsd'] = Plugin.reformat_metric_name(chunk['metricPath'])
        LOGGER.debug(chunk)
        results = {'metrics' : {}}
        statsd_name = chunk['statsd']
        results["metrics"][statsd_name] = chunk[self.statistic]
        LOGGER.debug(results)
        self.current_data = [chunk]
        self.metric_data = results

