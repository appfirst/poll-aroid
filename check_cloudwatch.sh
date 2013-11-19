#!/bin/bash

# Include path so we can execute commands like 'python'
PATH=$PATH:/usr/bin
export PATH

# script location
AfPath=/usr/share/appfirst/plugins/libexec/AfPoller

# IFS is field separator
IFS=","

# Count the total run
let "metricTotal=0"

## Application Name
## Name metrics are sorted with in statsd buckets
appname=AWSdemo


## any additional program execution flags, IE --test or --dry-run (or both)
flags="--test --dry-run"

## AWS IAM Role Credentials, Recommended CloudWatch Read Only
access_key="" 
access_secret=""

## Single Namespace (recommend one script per namespace)
## ie, aws_billing for AWS/Billing, aws_ec2_metrics for AWS/EC2, etc
namespace="AWS/EBS"

## IFS separator list, if you have multiple items to collect
instances=""

## IFS separator list of regions
region="us-west"

# IFS separated list of all the metrics you wish to collect
metriclist=""

for instance in $instances
do
  for metric in $metriclist
  do
# increment the counter
let "metricTotal++"
python $AfPath/AfPoller.py --plugin=cloudwatch --amazon-access-key-id=$access_key --amazon-access-secret-key=$access_secret --metricname=$metric --namespace=$namespace --dimension=VolumeId:$instance --application=$appname --region=$region
  done
done

## Output basic nagios-format "OK" so the polled data script knows this executed
echo "$0 OK $metricTotal"
