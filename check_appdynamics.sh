#!/bin/bash

# Include path so we can execute commands like 'python'
PATH=$PATH:/usr/bin
export PATH

# script location
AfPath=/usr/share/appfirst/plugins/libexec/poll-aroid/AfPoller

## AppDynamics Specific Values
controllerHostname=
accountName=
userName=
accessKey=

## From Metrics Browser, "Copy Full Path"
metricPath=""

## Application Name
## Name metrics are sorted with in statsd buckets
appName=

## any additional program execution flags, IE --test or --dry-run (or both)
flags="--test --dry-run"

python $AfPath/AfPoller.py --plugin=appdynamics -u $accountName@$userName -p $accessKey -H $controllerHostname -m "$metricPath"  -a $appName $flags

## Output basic nagios-format "OK" so the polled data script knows this executed
echo "$0 OK"
