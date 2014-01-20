#!/bin/bash

# Include path so we can execute commands like 'python'
PATH=$PATH:/usr/bin
export PATH

# script location
AfPath=/usr/share/appfirst/plugins/libexec/poll-aroid/AfPoller

## NewRelic Specific Values
accessKey=""
## you can find you application ID at https://rpm.newrelic.com/api/explore/applications/list
accessAppId=""

## Application Name
## Name metrics are sorted with in statsd buckets
appName=


## From "Applications > Metric Names copy metric name"
## https://rpm.newrelic.com/api/explore/applications/names
## for example "Agent/MetricsReported/count"
metricPath=""


## any additional program execution flags, IE --test or --dry-run (or both)
flags="--test --dry-run"

python $AfPath/AfPoller.py --plugin=newrelic -V --newrelic-access-key-id=$accessKey --newrelic-access-app-id=$accessAppId -m $metricPath -a $appName

## Output basic nagios-format "OK" so the polled data script knows this executed
echo "$0 OK"
