'''systemd mock template base
'''

# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option) any
# later version.  See http://www.gnu.org/copyleft/lgpl.html for the full text
# of the license.

__author__ = 'Jonas Ådahl'
__copyright__ = '(c) 2021 Red Hat'

from gi.repository import GLib

BUS_NAME = 'org.freedesktop.systemd1'
MAIN_OBJ = '/org/freedesktop/systemd1'
MAIN_IFACE = 'org.freedesktop.systemd1.Manager'


def load_base(mock, _parameters):
    mock.next_job_id = 1
    mock.units = {}

    mock.AddMethod(MAIN_IFACE,
                   'StartUnit',
                   'ss', 'o',
                   'ret = self.StartUnit(self, args[0], args[1])')
    mock.AddMethod(MAIN_IFACE,
                   'StartTransientUnit',
                   'ssa(sv)a(sa(sv))', 'o',
                   'ret = self.StartTransientUnit(self, args[0], args[1], args[2], args[3])')
    mock.AddMethod(MAIN_IFACE,
                   'StopUnit',
                   'ss', 'o',
                   'ret = self.StopUnit(self, args[0], args[1])')

    mock.StartUnit = StartUnit
    mock.StartTransientUnit = StartTransientUnit
    mock.StopUnit = StopUnit


def escape_unit_name(name):
    for s in ['.', '-']:
        name = name.replace(s, '_')


def emit_job_new_remove(self, job_id, job_path, name):
    self.EmitSignal('org.freedesktop.systemd1.Manager', 'JobNew', 'uos',
                    [job_id, job_path, name])
    self.EmitSignal('org.freedesktop.systemd1.Manager', 'JobRemoved', 'uoss',
                    [job_id, job_path, name, 'done'])


def StartUnit(self, name, _mode):
    job_id = self.next_job_id
    self.next_job_id += 1

    job_path = '/org/freedesktop/systemd1/Job/%d' % (job_id)
    GLib.idle_add(lambda: emit_job_new_remove(self, job_id, job_path, name))

    unit_path = '/org/freedesktop/sytemd1/unit/%s' % (escape_unit_name(name))
    self.AddObject(unit_path,
                   'org.freedesktop.systemd1.Unit',
                   {'Id': name,
                    'Names': [name]},
                   [])
    self.units[name] = unit_path
    return job_path


def StartTransientUnit(self, name, _mode, _properties, _aux):
    job_id = self.next_job_id
    self.next_job_id += 1

    job_path = '/org/freedesktop/systemd1/Job/%d' % (job_id)
    GLib.idle_add(lambda: emit_job_new_remove(self, job_id, job_path, name))

    return job_path


def StopUnit(self, name, _mode):
    job_id = self.next_job_id
    self.next_job_id += 1

    job_path = '/org/freedesktop/systemd1/Job/%d' % (job_id)
    GLib.idle_add(lambda: emit_job_new_remove(self, job_id, job_path, name))

    unit_path = self.units[name]
    del self.units[name]
    self.RemoveObject(unit_path)
    return job_path
