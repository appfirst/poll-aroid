"""
Created on Oct 1, 2013

@author: AppFirst, Inc.

Pluggable framework for polling for, collecting metrics and posting metrics to AppFirst StatsD

"""

import sys
import json
import logging
import os
import ConfigParser
import argparse
from codecs import open
from plugins.appdynamics import AppDynamics
from plugins.cloudwatch import CloudWatch
from plugins.newrelic import NewRelic

LOGGER = logging.getLogger(__name__)

def get_options(parser, config = None):

    parser.add_argument('-P','--plugin', dest='plugin', required=False, help="[REQUIRED] Name of plug in appdynamics or cloudwatch")
    parser.add_argument('-C','--config', dest='config', help="Path to configuration file")
    parser.add_argument('-u','--username', dest='username', help="AppDynamics username (usually name@domain format)")
    parser.add_argument('-p','--password', dest='password', help="AppDynamics password")
    parser.add_argument('-a','--application', dest='appname', help="Name of your AppDynamics Application")
    parser.add_argument('-H','--hostname', dest='hostname', help="Host name (including port) of your AppFirst Controller")
    parser.add_argument('-m','--metricpath', dest='metricpath', help="AppDynamics path (with \| separators) to the metric to poll.  You may use wildcards '*'")
    parser.add_argument('-r','--region', dest='region', help="Amazon AWS region - like us-west-1 or us-east-2")
    parser.add_argument('-i','--amazon-access-key-id', dest='amazon_key_id', help="Amazon key identifier")
    parser.add_argument('-k','--amazon-access-secret-key', dest='amazon_secret_key', help="Amazon secret access key")
    parser.add_argument('-M','--metricname', dest='metric_name', help="Name of CloudWatch metric")
    parser.add_argument('-c','--namespace', dest='namespace', help="Namespace of CloudWatch metric eg. AWS/EBS, AWS/EC2")
    parser.add_argument('-n','--dimension', dest='dimension', help="Name of CloudWatch dimension & value eg. InstanceId:i-9999999 you may have any number", type=str, action="append")
    parser.add_argument('-s','--statistic', dest='statistic', help="Name of CloudWatch dimension's Average, Sum, Mininum, Maximum - default Average", default="Average")
    parser.add_argument('-t','--unit', dest='unit', default=None, help="Name of CloudWatch dimension unit eg Seconds, Bytes, Bytes/Second")
    parser.add_argument('-o','--offset', dest='offset', help="time offset for CloudWatch in minutes",default=60,type=int)
    parser.add_argument('-U','--url', dest='url', help="full AppDynamics url to the metric as copied from AppDynamics metric browser.  You may use wildcards '*'")
    parser.add_argument('-d','--dry-run',dest='dryrun', action='store_true',default=False,help="Get metric value but do not send to AppFirst, print results to console")
    parser.add_argument('-v','--verbose', dest='verbose', action='count',default=2, help="Set log level higher you can add multiple")
    parser.add_argument('-V','--very_verbose', dest='verbose', action='store_const', const=4, help="Set log level to highest level of detail")
    parser.add_argument('-f','--log-to-file', dest='log_to_file', help="Store output log to file")
    parser.add_argument('-e','--test', dest='verbose', action='store_const', const=4, help="Set log level to highest level of detail")

    parser.add_argument('-K','--newrelic-access-key-id', dest='nrelic_key', help="API key provided by New Relic")
    parser.add_argument('-I','--newrelic-access-app-id', dest='nrelic_app_id', help="application ID to get metrics from New Relic")

    no_args_flag = True if len(sys.argv[1:]) == 0 else False

    if config is None:
        options = parser.parse_args()
    else:
        options = parser.parse_args(config)

    level = {
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG
    }.get(options.verbose, logging.ERROR)
    options.verbose = level
    if no_args_flag:
        parser.print_help()
        exit()

    return options


def get_json_from_file(file_name):
    f = open(file_name)
    data = f.read()
    return json.loads(data, "utf-8")


def parse_cfg(config, sections):
    args = []
    if sections:
        for (section) in sections:
            try:
                items = config.items(section)
                for item in items:
                    args.append(item)
            except Exception as e:
                LOGGER.info('Section: %s not found in configuration file', section)
    return args


def parse_arguments(list):

    if list:
        args = []
        for (key, val) in list:
            if (key.find('--') == 0):
                args.append(key)
            else:
                args.append('--' + key)
            args.append(val)

    return args



def setup_logger(options):

    ch = logging.StreamHandler()
    fh = None
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    ch.setFormatter(formatter)

    if options.verbose and options.log_to_file:
        filename = os.path.dirname(os.path.realpath(__file__)) + '/af-poller.log'
        fh = logging.FileHandler(filename, mode='a', encoding=None, delay=False)
        fh.setFormatter(formatter)

    logger_components = [LOGGER]
    logger_components.append(logging.getLogger(name="plugins.base_plugin"))
    logger_components.append(logging.getLogger(name="plugins.appdynamics"))
    logger_components.append(logging.getLogger(name="plugins.cloudwatch"))
    logger_components.append(logging.getLogger(name="plugins.newrelic"))


    for l in logger_components:
        l.setLevel(options.verbose)
        l.addHandler(ch)
        if fh:
            l.addHandler(fh)

    component_logger = logging.getLogger(name="requests.packages.urllib3.connectionpool")
    component_logger.setLevel(logging.WARN)

def get_region_url(region) :
    RegionData = {
        'us-east-1': 'monitoring.us-east-1.amazonaws.com',
        'us-gov-west-1': 'monitoring.us-gov-west-1.amazonaws.com',
        'us-west-1': 'monitoring.us-west-1.amazonaws.com',
        'us-west-2': 'monitoring.us-west-2.amazonaws.com',
        'sa-east-1': 'monitoring.sa-east-1.amazonaws.com',
        'eu-west-1': 'monitoring.eu-west-1.amazonaws.com',
        'ap-northeast-1': 'monitoring.ap-northeast-1.amazonaws.com',
        'ap-southeast-1': 'monitoring.ap-southeast-1.amazonaws.com',
        'ap-southeast-2': 'monitoring.ap-southeast-2.amazonaws.com',
    }
    return RegionData.get(region,"monitoring.amazonaws.com")

def main():
    try:


        parser = argparse.ArgumentParser( epilog="use -h/--help to see full help", conflict_handler="resolve")
        options = get_options(parser)
        setup_logger(options)
        plugin = None

        # check if configuration file path is set
        if options.config is not None:
            LOGGER.debug("Loading configuration from file %s", options.config)
            if os.path.isfile(options.config):
                config = ConfigParser.RawConfigParser()
                config.read(options.config)

                argumentsFromFile = config.items("common")

                argumentsFromFile = parse_cfg(config, ["common", "newrelic", "appdynamics", "cloudwatch"])
                arguments = parse_arguments(argumentsFromFile)

                options = get_options(parser, config = arguments)
            else:
                parser.error("Configuration file not found")




        if options.plugin is None:
            parser.error("You must provide plugin name")

        if options.plugin.lower() == "appdynamics":
            if not (options.url or (options.hostname and options.metricpath)):
                parser.error("You must supply either a URL or hostname and metrics path")
            if options.url and (options.hostname or options.metricpath):
                parser.error("You must supply either a URL or hostname and metrics path, not both")
            if not(options.username and options.password and options.appname):
                parser.error("You must provide username, password and application name")
            if options.url is None:
                url = AppDynamics.default_url(options.hostname, options.appname, options.metricpath)
            else:
                url = options.url
        
            plugin = AppDynamics(url=url,
                                 username=options.username,
                                 password=options.password
                    )
        elif options.plugin.lower() == "cloudwatch":
            if not options.region:
                parser.error("You must provide an Amazon Region name like us-east-1 or us-west-2")
            if not options.appname:
                parser.error("You must provide an Application Name")
            if not(options.amazon_key_id and options.amazon_secret_key):
                parser.error("You must supply your Amazon Access Key Id and Amazon Secret Key")
            if not(options.namespace and options.metric_name and options.dimension):
                parser.error("You must provide an Amazon Cloudwatch namespace and metric name and at least one dimension")

            options.statistic = "Average" if not options.statistic else options.statistic
            hostname = get_region_url(options.region)
            plugin = CloudWatch(appname=options.appname,
                                key_id=options.amazon_key_id,
                                secret_key=options.amazon_secret_key,
                                action="ListMetrics",
                                params={},
                                dimension=options.dimension,
                                metricname=options.metric_name,
                                hostname=hostname,
                                aws_namespace=options.namespace,
                                statistic=options.statistic,
                                unit=options.unit,
                                offset=options.offset)

        elif options.plugin.lower() == "newrelic":

            if (not options.nrelic_key) and (not options.nrelic_app_id):
                parser.error("You must provide New Relic API key and application ID")

            if (not options.metricpath):
                parser.error("You must provide metric path")

            if not options.appname:
                parser.error("You must provide an Application Name")


            plugin = NewRelic(
                            key=options.nrelic_key,
                            app_id=options.nrelic_app_id,
                            metricpath=options.metricpath,
                            appname = options.appname
                        )

        else:
            parser.print_help()
            exit()

        if not options.dryrun:
            from afstatsd import Statsd
            from afstatsd.afclient import AFTransport

            Statsd.set_aggregation(True)
            Statsd.set_transport(AFTransport())
        else:
            #noinspection PyPep8Naming
            Statsd = None

        plugin.poll()
        # Need to add connection checking here, pulling data on a failed
        #  connection will generate a critical - response code and friendlier
        #  output is expected
        LOGGER.debug("plugin poll done")
        data = plugin.metric_data
        if data is None:
            raise Exception("No metric data recived from plugin")
        else:
            for (statsd_key, value) in data.get('metrics',{}).iteritems():

                if not options.dryrun:
                    if plugin.ignoreCommonAppName:
                        LOGGER.info(" *** polling metrics %s %s" % (statsd_key, value))
                        Statsd.gauge(str("%s" % (statsd_key)),value)
                    else:
                        LOGGER.info(" *** polling metrics %s.%s %s" % (options.appname, statsd_key, value))
                        Statsd.gauge(str("%s.%s" % (options.appname, statsd_key)),value)

    except Exception as e:
        LOGGER.critical('Serious Error occured: %s', e)

if __name__ == '__main__':
    main()
        
