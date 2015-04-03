from __future__ import (absolute_import, print_function, division,
                        unicode_literals)

import inspect
from importlib import import_module

available_services = {}

CLASS_MARKER = '_RUNBOT_SERVICE'

def service_class(cls):
    if inspect.isclass(cls):
        setattr(cls, CLASS_MARKER, True)
        return cls

def load_services(services):
    for service in services:
        importname = "{}.{}".format("plugins.runbot.services", service)
        try:
            component_ns = import_module(importname)
        except ImportError as e:
            raise ImportError('runbot failed to load (%s): %r' % (importname, e))
        
        for name, member in inspect.getmembers(component_ns):
            if inspect.isclass(member) and hasattr(member, CLASS_MARKER):
                available_services[service] = member
                break
