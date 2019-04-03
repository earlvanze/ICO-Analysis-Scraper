#!/usr/bin/env python

"""
This simple module defines two alternate functions to use to display tracebacks.

The compact_traceback function formats the output like
asyncore.compact_traceback.  The verbose_traceback function formats the
output as usual, but also displays the variables in each active namespace.

To use, simply import and set sys.excepthook to the desired function, e.g.:

    import sys
    import tb
    sys.excepthook = tb.compact_traceback
"""

import sys
import inspect
import linecache
import types
import traceback

__all__ = ["compact_traceback", "verbose_traceback"]

# Stolen from asyncore with an api change.
def compact_traceback(t, v, tb):
    """Display a compact, two-line traceback.

    Stolen from the standard Python asyncore module with only slight changes.
    """
    tbinfo = []
    while tb is not None:
        tbinfo.append((
            tb.tb_frame.f_code.co_filename,
            tb.tb_frame.f_code.co_name,
            str(tb.tb_lineno)
            ))
        tb = tb.tb_next

    # just to be safe
    del tb

    print >> sys.stderr, ' '.join(['[%s|%s|%s]' % x for x in tbinfo])
    print >> sys.stderr, traceback.format_exception_only(t, v)[0].strip()

def verbose_traceback(t, v, tb):
    """Display a more verbose traceback which includes local variable values.

    Stolen from the standard Python traceback module with slight modifications.
    """
    print >> sys.stderr, 'Traceback (most recent call last):'
    print_tb(tb)
    print >> sys.stderr, traceback.format_exception_only(t, v)[0].strip()

def format_vars(localvars):
    lst = []
    keys = localvars.keys()
    keys.sort()
    for key in keys:
        # skip Python-special vars
        if key.startswith("__") and key.endswith("__"):
            continue
        val = localvars[key]
        # skip modules if the variable name and the module name are
        # identical
        if isinstance(val, types.ModuleType) and key == val.__name__:
            continue
        val = repr(val)
        if val != val[:30]:
            val = "%s..." % val[:30]
        lst.append('       %s: %s' % (key, val))
    return "\n".join(lst)
 
def print_tb(tb):
    while tb is not None:
        f = tb.tb_frame
        lineno = tb.tb_lineno
        co = f.f_code
        filename = co.co_filename
        name = co.co_name
        print >> sys.stderr, '  File "%s", line %d, in %s' % (filename, lineno, name)
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        if line:
            print >> sys.stderr, '    ' + line.strip()
        print >> sys.stderr, format_vars(inspect.getargvalues(f)[3])
        tb = tb.tb_next
    del tb
