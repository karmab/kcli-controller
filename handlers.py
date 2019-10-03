#!/usr/bin/env python3

import kopf
from kubernetes import client
from kvirt.config import Kconfig
from kvirt import common
import os
from re import sub

DOMAIN = "kcli.karmalabs.local"
VERSION = "v1"


def update_vm_cr(name, namespace, newspec):
    configuration = client.Configuration()
    configuration.assert_hostname = False
    api_client = client.api_client.ApiClient(configuration=configuration)
    crds = client.CustomObjectsApi(api_client)
    crds.patch_namespaced_custom_object(DOMAIN, VERSION, namespace, "vms", name, newspec)


def process_vm(name, namespace, spec, operation='create', timeout=60):
    config = Kconfig(quiet=True)
    exists = config.k.exists(name)
    if operation == "delete" and exists:
        print("Deleting: %s" % name)
        result = config.k.delete(name)
        if result['result'] == 'success':
            print("Success : %s deleted" % name)
        else:
            print("Failure : %s not deleted because %s" % (name, result['reason']))
        return
    if operation == "create":
        if not exists:
            profile = spec.get("profile")
            if profile is None:
                if 'template' in spec:
                    profile = spec['template']
                else:
                    profile = name
            print("Creating: %s" % name)
            if profile is not None:
                result = config.create_vm(name, profile, overrides=spec)
                if result['result'] == 'success':
                    print("Success : %s created" % name)
            else:
                print("Failure : %s not created because %s" % (name, result['reason']))
        info = config.k.info(name)
        template = info.get('template')
        if template is not None and 'ip' not in info:
            raise kopf.TemporaryError("Waiting to populate ip", delay=10)
        newspec = {'spec': {'info': info}}
        update_vm_cr(name, namespace, newspec)


def process_plan(plan, spec, operation='create'):
    workdir = spec.get('workdir', '/workdir')
    inputstring = spec.get('plan')
    if inputstring is None:
        print("Failure : %s not created because of missing plan spec")
        return
    elif os.path.exists("/i_am_a_container"):
        inputstring = sub(r"origin:( *)", r"origin:\1%s/" % workdir, inputstring)
    overrides = spec.get('parameters', {})
    config = Kconfig(quiet=True)
    if operation == "delete":
        print("Deleting plan: %s" % plan)
        result = config.plan(plan, delete=True)
        if result['result'] == 'success':
            print("Success : %s deleted" % plan)
        else:
            print("Failure : %s not deleted because %s" % plan, result['reason'])
        return
    if operation == "create":
        print("Creating plan: %s" % plan)
        result = config.plan(plan, inputstring=inputstring, overrides=overrides)
        if result['result'] == 'success':
            print("Success : %s created" % plan)
        else:
            print("Failure : %s not created because %s" % plan, result['reason'])
        return


def update(name, namespace, diff):
    config = Kconfig(quiet=True)
    k = config.k
    for entry in diff:
        if entry[0] not in ['add', 'change']:
            continue
        arg = entry[1][1]
        value = entry[3]
        if arg == 'plan':
            plan = value
            common.pprint("Updating plan of vm %s to %s..." % (name, plan))
            k.update_metadata(name, 'plan', plan)
        if arg == 'memory':
            memory = value
            common.pprint("Updating memory of vm %s to %s..." % (name, memory))
            k.update_memory(name, memory)
        if arg == 'numcpus':
            numcpus = value
            common.pprint("Updating numcpus of vm %s to %s..." % (name, numcpus))
            k.update_cpus(name, numcpus)
        if arg == 'autostart':
            autostart = value
            common.pprint("Setting autostart for vm %s to %s..." % (name, autostart))
            k.update_start(name, start=autostart)
        if arg == 'information':
            information = value
            common.pprint("Setting information for vm %s..." % name)
            k.update_information(name, information)
        if arg == 'iso':
            iso = value
            common.pprint("Switching iso for vm %s to %s..." % (name, iso))
            k.update_iso(name, iso)
        if arg == 'flavor':
            flavor = value
            common.pprint("Updating flavor of vm %s to %s..." % (name, flavor))
            k.update_flavor(name, flavor)
        if arg == 'start':
            start = value
            if start:
                common.pprint("Starting vm %s..." % name)
                k.start(name)
            else:
                common.pprint("Stopping vm %s..." % name)
                k.stop(name)
        info = config.k.info(name)
        newspec = {'spec': {'info': info}}
        update_vm_cr(name, namespace, newspec)


@kopf.on.create(DOMAIN, VERSION, 'vms')
def create_vm(meta, spec, status, namespace, logger, **kwargs):
    operation = 'create'
    name = meta.get('name')
    exist = status.get('create_vm', None)
    if exist is None:
        print("Handling %s on vm %s" % (operation, name))
        process_vm(name, namespace, spec, operation=operation)
        return {'exist': True}


@kopf.on.delete(DOMAIN, VERSION, 'vms')
def delete_vm(meta, spec, namespace, logger, **kwargs):
    operation = 'delete'
    name = meta.get('name')
    keep = spec.get("keep", False)
    if not keep:
        print("Handling %s on vm %s" % (operation, name))
        process_vm(name, namespace, spec, operation=operation)


@kopf.on.update(DOMAIN, VERSION, 'vms')
def update_vm(meta, spec, namespace, old, new, diff, **kwargs):
    operation = 'update'
    name = meta.get('name')
    print("Handling %s on vm %s" % (operation, name))
    update(name, namespace, diff)


@kopf.on.create(DOMAIN, VERSION, 'plans')
def create_plan(meta, spec, status, namespace, logger, **kwargs):
    operation = 'create'
    name = meta.get('name')
    print("Handling %s on plan %s" % (operation, name))
    process_plan(name, spec, operation=operation)
    return {'exist': True}


@kopf.on.delete(DOMAIN, VERSION, 'plans')
def delete_plan(meta, spec, namespace, logger, **kwargs):
    operation = 'delete'
    name = meta.get('name')
    if spec.get('plan') is not None:
        print("Handling %s on plan %s" % (operation, name))
        process_plan(name, spec, operation=operation)
        return {'exist': True}
