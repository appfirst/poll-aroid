#!/bin/bash

# Include path so we can execute commands like 'python'
PATH=$PATH:/usr/bin
export PATH

# script location
AfPath=/usr/share/appfirst/plugins/libexec/af_newrelic/poll-aroid/AfPoller

## path to configuration file in yaml format
configPath=$AfPath/config.ini
echo $configPath

python $AfPath/AfPoller.py --config=$configPath -V
#pudb $AfPath/AfPoller.py --config=$configPath -V

## Output basic nagios-format "OK" so the polled data script knows this executed
echo "$0 OK"
