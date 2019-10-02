#!/usr/bin/env python3

import kopf
from kvirt.config import Kconfig
from kvirt import common
import os
import shutil

DOMAIN = "kcli.karmalabs.local"


def process_vm(name, spec, operation='create'):
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
    if operation == "create" and not exists:
        profile = spec.get("profile")
        if profile is None:
            if 'template' in spec:
                profile = spec['template']
            else:
                profile = name
        overrides = spec
        print("Creating: %s" % name)
        if profile is not None:
            result = config.create_vm(name, profile, overrides=overrides)
            if result['result'] == 'success':
                print("Success : %s created" % name)
        else:
            print("Failure : %s not created because %s" % (name, result['reason']))
        return


def process_plan(plan, spec, operation='create'):
    inputstring = spec.get('plan')
    if inputstring is None:
        print("Failure : %s not created because of missing plan spec")
        return
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


def update(name, spec):
    config = Kconfig(quiet=True)
    k = config.k
    info = k.info(name)
    for arg in spec:
        if arg == 'plan':
            plan = spec[arg]
            if info['plan'] != plan:
                common.pprint("Updating plan of vm %s to %s..." % (name, plan))
                k.update_metadata(name, 'plan', plan)
        if arg == 'memory':
            memory = spec[arg]
            if info['memory'] != memory:
                common.pprint("Updating memory of vm %s to %s..." % (name, memory))
                k.update_memory(name, memory)
        if arg == 'numcpus':
            numcpus = spec[arg]
            if info['numcpus'] != numcpus:
                common.pprint("Updating numcpus of vm %s to %s..." % (name, numcpus))
                k.update_cpus(name, numcpus)
        if arg == 'autostart':
            autostart = spec[arg]
            common.pprint("Setting autostart for vm %s to %s..." % (name, autostart))
            k.update_start(name, start=autostart)
        if arg == 'information':
            information = spec[arg]
            common.pprint("Setting information for vm %s..." % name)
            k.update_information(name, information)
        if arg == 'iso':
            iso = spec[arg]
            common.pprint("Switching iso for vm %s to %s..." % (name, iso))
            k.update_iso(name, iso)
        if arg == 'flavor':
            flavor = spec[arg]
            if info['flavor'] != flavor:
                common.pprint("Updating flavor of vm %s to %s..." % (name, flavor))
                k.update_flavor(name, flavor)
        if arg == 'start':
            start = spec[arg]
            if start:
                common.pprint("Starting vm %s..." % name)
                k.start(name)
            else:
                common.pprint("Stopping vm %s..." % name)
                k.stop(name)


homedir = os.path.expanduser("~")
cmdir = "%s/.kcli_cm" % homedir
kclidir = "%s/.kcli" % homedir
if os.path.isdir(cmdir) and not os.path.isdir(kclidir):
    shutil.copytree(cmdir, kclidir)


@kopf.on.create('kcli.karmalabs.local', 'v1', 'vms')
def create_vm(meta, spec, status, namespace, logger, **kwargs):
    operation = 'create'
    name = meta.get('name')
    exist = status.get('create_vm', None)
    if exist is None:
        print("Handling %s on vm %s" % (operation, name))
        process_vm(name, spec, operation=operation)
        return {'exist': True}


@kopf.on.delete('kcli.karmalabs.local', 'v1', 'vms')
def delete_vm(meta, spec, namespace, logger, **kwargs):
    operation = 'delete'
    name = meta.get('name')
    keep = spec.get("keep", False)
    if not keep:
        print("Handling %s on vm %s" % (operation, name))
        process_vm(name, spec, operation=operation)


@kopf.on.update('kcli.karmalabs.local', 'v1', 'vms')
def update_vm(meta, spec, namespace, logger, **kwargs):
    operation = 'update'
    name = meta.get('name')
    print("Handling %s on vm %s" % (operation, name))
    update(name, spec)


@kopf.on.create('kcli.karmalabs.local', 'v1', 'plans')
def create_plan(meta, spec, status, namespace, logger, **kwargs):
    operation = 'create'
    name = meta.get('name')
    print("Handling %s on plan %s" % (operation, name))
    process_plan(name, spec, operation=operation)
    return {'exist': True}


@kopf.on.delete('kcli.karmalabs.local', 'v1', 'plans')
def delete_plan(meta, spec, namespace, logger, **kwargs):
    operation = 'delete'
    name = meta.get('name')
    if spec.get('plan') is not None:
        print("Handling %s on plan %s" % (operation, name))
        process_plan(name, spec, operation=operation)
        return {'exist': True}
