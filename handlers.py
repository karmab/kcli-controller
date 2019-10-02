#!/usr/bin/env python3

import kopf
from kvirt.config import Kconfig
import os
import shutil

DOMAIN = "kcli.karmalabs.local"


def process_vm(name, namespace, spec, operation='create'):
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
        overrides = spec.get("parameters", {})
        print("Creating: %s" % name)
        if profile is not None:
            result = config.create_vm(name, profile, overrides=overrides)
            if result['result'] == 'success':
                print("Success : %s created" % name)
        else:
            print("Failure : %s not created because %s" % (name, result['reason']))
        return


def process_plan(plan, namespace, spec, operation='create'):
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
        process_vm(name, namespace, spec, operation=operation)
        return {'exist': True}


@kopf.on.delete('kcli.karmalabs.local', 'v1', 'vms')
def delete_vm(meta, spec, namespace, logger, **kwargs):
    operation = 'delete'
    name = meta.get('name')
    keep = spec.get("keep", False)
    if not keep:
        print("Handling %s on vm %s" % (operation, name))
        process_vm(name, namespace, spec, operation=operation)


@kopf.on.create('kcli.karmalabs.local', 'v1', 'plans')
def create_plan(meta, spec, status, namespace, logger, **kwargs):
    operation = 'create'
    name = meta.get('name')
    print("Handling %s on plan %s" % (operation, name))
    process_plan(name, namespace, spec, operation=operation)
    return {'exist': True}


@kopf.on.delete('kcli.karmalabs.local', 'v1', 'plans')
def delete_plan(meta, spec, namespace, logger, **kwargs):
    operation = 'delete'
    name = meta.get('name')
    if spec.get('plan') is not None:
        print("Handling %s on plan %s" % (operation, name))
        process_plan(name, namespace, spec, operation=operation)
        return {'exist': True}
