#!/usr/bin/env python3

from kvirt.config import Kconfig
import json
import yaml
from kubernetes import client, config, watch
from kubernetes.client.models.v1beta1_custom_resource_definition_status import V1beta1CustomResourceDefinitionStatus
import os

DOMAIN = "kcli.karmalabs.local"
goodbrands = ['coleclark', 'fender', 'gibson', 'ibanez', 'martin', 'seagull', 'squier', 'washburn']
badbrands = ['epiphone', 'guild', 'gretsch', 'jackson', 'ovation', 'prs', 'rickenbauer', 'taylor', 'yamaha']

# manual workarounds for  https://github.com/kubernetes-client/python/issues/376


def set_stored_versions(self, stored_versions):
    if stored_versions is None:
        stored_versions = []
    self._stored_versions = stored_versions


def set_conditions(self, conditions):
    if conditions is None:
        conditions = []
    self._conditions = conditions


def process_machine(crds, obj, operation):
    metadata = obj.get("metadata")
    if not metadata:
        print("No metadata in object, skipping: %s" % json.dumps(obj, indent=1))
        return
    name = metadata.get("name")
    namespace = metadata.get("namespace")
    spec = obj.get("spec")
    providerspec = spec["providerSpec"]["value"]
    vmkind = providerspec.get("kind")
    if vmkind != "KcliMachineProviderSpec":
        return
    config = Kconfig(quiet=True)
    if operation == "DELETED":
        config.k.delete(name)
        print("prout")
        return
    profile = providerspec.get("profile")
    overrides = providerspec.get("parameters", {})
    print("Creating: %s" % name)
    if profile is not None:
        result = config.create_vm(name, profile, overrides=overrides)
        if result['result'] == 'success':
            obj["spec"]["state"] = "created"
        crds.replace_namespaced_custom_object(DOMAIN, "v1", namespace, "machines", name, obj)
    else:
        print("Missing data: %s not created" % name)
        return


if __name__ == "__main__":
    setattr(V1beta1CustomResourceDefinitionStatus, 'stored_versions',
            property(fget=V1beta1CustomResourceDefinitionStatus.stored_versions.fget, fset=set_stored_versions))
    setattr(V1beta1CustomResourceDefinitionStatus, 'conditions',
            property(fget=V1beta1CustomResourceDefinitionStatus.conditions.fget, fset=set_conditions))
    if 'KUBERNETES_PORT' in os.environ:
        config.load_incluster_config()
        definition = '/tmp/machine.yml'
    else:
        config.load_kube_config()
        definition = 'machine.yml'
    configuration = client.Configuration()
    configuration.assert_hostname = False
    client.Configuration.set_default(client)
    api_client = client.api_client.ApiClient(configuration=configuration)
    v1 = client.ApiextensionsV1beta1Api(api_client)
    current_crds = [x['spec']['names']['kind'].lower() for x in v1.list_custom_resource_definition().to_dict()['items']]
    if 'machine' not in current_crds:
        print("Creating machine definition")
        with open(definition) as data:
            body = yaml.load(data)
        v1.create_custom_resource_definition(body)
    crds = client.CustomObjectsApi(api_client)

    print("Waiting for Machines to come up...")
    resource_version = ''
    while True:
        stream = watch.Watch().stream(crds.list_cluster_custom_object, DOMAIN, "v1", "machines",
                                      resource_version=resource_version)
        for event in stream:
            obj = event["object"]
            operation = event['type']
            spec = obj.get("spec")
            if not spec:
                continue
            metadata = obj.get("metadata")
            resource_version = metadata['resourceVersion']
            name = metadata['name']
            print("Handling %s on %s" % (operation, name))
            done = spec.get("review", False)
            state = obj["spec"].get("state")
            if state is not None and state == "created":
                continue
            else:
                process_machine(crds, obj, operation)
