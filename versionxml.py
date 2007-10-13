#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# @author Guillermo Gonzalez
# This code is a modified copy from bzrlib.version (see there for copyrights and licensing)

import os
import sys

import bzrlib
from bzrlib import (
    config,
    trace,
    )
from bzrlib.version import _get_bzr_source_tree

def show_version_xml(show_config=True, show_copyright=True, to_file=None):
    if to_file is None:
        to_file = sys.stdout
    print >>to_file, u'<version>'
    _show_bazaar_version(to_file)
    _show_python_version(to_file)
    print >>to_file
    print >>to_file, u'</version>'

def _show_python_version(to_file):
    print >>to_file, u'<python>'
    # show path to python interpreter
    # (bzr.exe use python interpreter from pythonXY.dll
    # but sys.executable point to bzr.exe itself)
    if not hasattr(sys, u'frozen'):  # check for bzr.exe
        # python executable
        print >>to_file, u'<executable>%s</executable>' % sys.executable
    else:
        # pythonXY.dll
        basedir = os.path.dirname(sys.executable)
        python_dll = u'python%d%d.dll' % sys.version_info[:2]
        print >>to_file, u'<dll>%s</dll>' % os.path.join(basedir, python_dll)
    # and now version of python interpreter
    print >>to_file, u'<version>%s</version>' % '.'.join(map(str, sys.version_info))
    print >>to_file, u'<standard_library>%s</standard_library>' % os.path.dirname(os.__file__)
    print >>to_file, u'</python>'

def _show_bazaar_version(show_config=True, show_copyright=True, to_file=None):
    print >>to_file, '<bazaar>'
    print >>to_file, '<version>%s</version>' % bzrlib.__version__
    # is bzrlib itself in a branch?
    _show_source_tree(to_file)
    print >>to_file, '<bzrlib>%s</bzrlib>' % _get_bzrlib_path()
    if show_config:
        _show_bzr_config(to_file)
    if show_copyright:
        print >>to_file, '<copyright>'
        _show_copyright(to_file)
        print >>to_file, '</copyright>'
    print >>to_file, '</bazaar>'

def _get_bzrlib_path():
    if len(bzrlib.__path__) > 1:
        # print repr, which is a good enough way of making it clear it's
        # more than one element (eg ['/foo/bar', '/foo/bzr'])
        return repr(bzrlib.__path__)
    else:
        return bzrlib.__path__[0]


def _show_source_tree(to_file):
    src_tree = _get_bzr_source_tree()
    if src_tree:
        src_revision_id = src_tree.last_revision()
        revno = src_tree.branch.revision_id_to_revno(src_revision_id)
        print >>to_file, u'<source_tree>'
        print >>to_file, u'<checkout>%s</checkout>' % src_tree.basedir
        print >>to_file, u'<revision>%s</revision>' % revno
        print >>to_file, u'<revid>%s</revid>' % src_revision_id
        print >>to_file, u'<branch_nick>%s</branch_nick>' % src_tree.branch.nick
        print >>to_file, u'</source_tree>'

def _show_bzr_config(to_file):
    config_dir = os.path.normpath(config.config_dir())  # use native slashes
    if not isinstance(config_dir, unicode):
        config_dir = config_dir.decode(bzrlib.user_encoding)
    print >>to_file, u'<configuration>%s</configuration>' % config_dir
    print >>to_file, u'<log_file>', trace._bzr_log_filename, u'</log_file>'

def _show_copyright(to_file):
    print >>to_file, bzrlib.__copyright__
    print >>to_file, "http://bazaar-vcs.org/"
    print >>to_file
    print >>to_file, "bzr comes with ABSOLUTELY NO WARRANTY.  bzr is free software, and"
    print >>to_file, "you may use, modify and redistribute it under the terms of the GNU"
    print >>to_file, "General Public License version 2 or later."

