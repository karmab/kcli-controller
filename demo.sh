#!/bin/bash

source `which util.sh`
HOST="192.168.122.225"
USER="developer"
PASSWORD="developer"
PROJECT="kcli"

backtotop
desc "Login in our project"
run "oc login --insecure-skip-tls-verify=true -u $USER -p $PASSWORD https://$HOST:8443"

backtotop
desc "Create a project and give enough permissions to default service account"
run "oc new-project kcli"
run "oc adm policy add-cluster-role-to-user cluster-admin -z default -n $PROJECT"

backtotop
desc "Deploy our custom controller"
run "oc new-app karmab/kcli-controller"

backtotop
desc "See how custom resource definition has been created for us"
run "oc get crd"

backtotop
desc "Create some machines and see the results"
run "oc create -f crd/stratocaster.yml"
run "oc create -f crd/lespaul.yml"
run "oc get machines -o yaml"

backtotop
desc "Clean things up"
run "oc project default"
run "oc delete project $PROJECT"
