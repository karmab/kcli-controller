# kcli-controller repository

[![](https://images.microbadger.com/badges/image/karmab/kcli-controller.svg)](https://microbadger.com/images/karmab/kcli-controller "Get your own image badge on microbadger.com")

This is a controller leveraging [kcli](https://github.com/karmab/kcli) and using vm an plan crds to create vms the same way, regardless of the infrastructure.

## Requisites

- a running kubernetes/openshift cluster
- some infrastructure somewhere and the corresponding credentials (libvirt, ovirt, gcp, aws, openstack, vsphere, kubevirt)

## Running

On openshift, first run the following commands

```
oc new-project kcli
oc adm policy add-cluster-role-to-user cluster-admin -z default -n kcli
```

If you're already running kcli locally, create first configmaps to share your credentials and ssh keys

```
kubectl create configmap kcli-config --from-file=$HOME/.kcli
kubectl create configmap ssh-config --from-file=$HOME/.ssh
```

Then deploy the controller

```
kubectl create -f crd.yml
kubectl create -f deploy.yml
```


## How to use

Create/Delete some vm and check on your infrastructure

```
oc create -f samplecrd/vm_cirros.yml
oc get vms -o yaml
```

Create plans

```
oc create -f samplecrd/plan_simple.yml
oc get vms -o yaml
```

## Copyright

Copyright 2017 Karim Boumedhel

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Problems?

Send me a mail at [karimboumedhel@gmail.com](mailto:karimboumedhel@gmail.com) !

Mc Fly!!!

karmab
