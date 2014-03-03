AppFirst's Poll-aroid
=====================

A module for pulling snapshots of data from RESTful services into the AF Data stream

This module is designed to allow a simpler configuration for service consumption by enabling the build of plugins and configuration files for various RESTful services. The initial release of this module supports AWS Cloudwatch and AppDynamics, New Relic. 

Properly configured, this script will run with the periodicity as set in the Administration panel (or you can utilize crontab), and will provide these metrics to StatsD widgets across the product.

*Dependencies*
* Recommended install path: `/usr/share/appfirst/plugins/libexec/`
* Requires python module: requests
* Requires python module: afstatsd

* `python AfPoller.py -h` will detail configuration flags


AppDynamics
-----------
`python AfPoller.py --plugin=appdynamics`

## AppDynamics Options
 `-u <username>` - Username as provided by AD (ie, user@user)
 `-p <password>`
 `-H <controller address>`

From the metric browser, using 'Copy Full Path':
 `-m <metric path>` - from the metric browser (ie, "Business Transaction Performance|Business Transactions|<instance>|/my.aspx/results|Calls per Minute)
 `-a <application>` - Application to define on AppFirst's portal

You can use the wildcard character (*) to get multiple levels of Metrics from AppDynamics. 

You can also use 'Copy REST URL' to collect metrics that way:
 `--url <REST URL>`
 Ensure the last parameter is &output=JSON for proper parsing


AWS CloudWatch
--------------
`python AfPoller.py --plugin=cloudwatch`

## CloudWatch Options
 `--amazon-access-key-id=<ID>`
 `--amazon-access-secret-key=<SECRET>`
 `--metricname=`  - i.e., VolumeWriteBytes
 `--namespace=`   - i.e., AWS/Billing, AWS/EBS
 `--dimension=`   - i.e., VolumeId:vol-e259792bd
 `--application=` - What name you want prepended in statsD
 `--region=`      - Where are these metrics on AWS (US-WEST, US-WEST-2)
 `--unit=`	  - Bytes, USD, etc

Included is a check_cloudwatch.sh script which iterates through various metrics and provides the data to statsd. It is recommended to rename this script and employ it for each namespace you are collecting metrics from, and is provided as an alternative to adding the full path and commandline to the polled data script.
It also outputs a nagios-plugin friendly OK so that the script call can be seen in the polled-data window of the workbench to verify the script was called.

New Relic
-----------
`python AfPoller.py --plugin=newrelic`

## New Relic Options
 `--newrelic-access-key-id <key>` - API key provided by New Relic https://rpm.newrelic.com/accounts/*acc-id*/integrations?page=data_sharing
 `--newrelic-access-app-id <app_id>` - application ID to get metrics from https://rpm.newrelic.com/api/explore/applications/list
 `-a <application>` - Application to define on AppFirst's portal
 `-m` - metric path for example "Agent/MetricsReported/count" or
  Apdex%count, Apdex%score, Agent/MetricsReported/count%min_response_time
  where text started from % is a reqierd value from metric,
  if value not set script will poll all values of the metric.
  
  Also it is possible to specify custom application name for each
  metric path, for example:
   *[CustomAppName]Apdex%count, Agent/MetricsReported/count%min_response_time*
   - where string between square brackets is a custom application name wich will be pre appended in statsD.


Configuration file
-----------
`python AfPoller.py --config=/path/to/configuration/file`
Please see config.cfg in INI format witch you can use to specify
metrics and parametrs for module. 
```
[common]
# define wich plugin will be used
plugin = pluginName
# common application name wich will be pre appended in statsD
application = AppName
metricpath = metric path for REST service from wich you collecting the data

[newrelic]
#add parametrs here for newRelic

[appdynamics]
# add parametrs here for appdynamics

[cloudwatch]
# add parametrs here for cloudwatch
```




Upcoming Changes
----------------
 * Interval period per metric
 * Multithreading
 * Daemon mode
