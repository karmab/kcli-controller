#!/usr/bin/env python3

import kopf
from kvirt.config import Kconfig
import os
import shutil

DOMAIN = "kcli.karmalabs.local"


def process(name, namespace, spec, operation='create'):
    config = Kconfig(quiet=True)
    exists = config.k.exists(name)
    if operation == "delete" and exists:
        print("Deleting: %s" % name)
        result = config.k.delete(name)
        if result['result'] == 'success':
            print("Success : %s deleted" % name)
        else:
            print("Failure : %s not deleted because %s" % name, result['reason'])
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
            print("Failure : %s not created because %s" % name, result['reason'])
        return


homedir = os.path.expanduser("~")
cmdir = "%s/.kcli_cm" % homedir
kclidir = "%s/.kcli" % homedir
if os.path.isdir(cmdir) and not os.path.isdir(kclidir):
    shutil.copytree(cmdir, kclidir)


@kopf.on.create('kcli.karmalabs.local', 'v1', 'vms')
def create(meta, spec, status, namespace, logger, **kwargs):
    operation = 'create'
    name = meta.get('name')
    exist = status.get('create', None)
    if exist is None:
        print("Handling %s on %s" % (operation, name))
        process(name, namespace, spec, operation=operation)
        return {'exist': True}


@kopf.on.delete('kcli.karmalabs.local', 'v1', 'vms')
def delete(meta, spec, namespace, logger, **kwargs):
    operation = 'delete'
    name = meta.get('name')
    keep = spec.get("keep", False)
    if not keep:
        print("Handling %s on %s" % (operation, name))
        process(name, namespace, spec, operation=operation)
