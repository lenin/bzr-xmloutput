#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright (C) 2007-2009 Guillermo Gonzalez
#
# The code taken from bzrlib is under: Copyright (C) 2005-2007 Canonical Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#
# Contributors:
#               Radim Kolam

# This code is a modified copy from bzrlib.version (see there for copyrights
# and licensing)

"""modified (and refactored) from bzrlib.version to generate xml output"""

import os
import sys

import bzrlib
from bzrlib import (
    config,
    trace,
    )
from bzrlib.version import _get_bzr_source_tree
from bzrlib.xml_serializer import _escape_cdata


def show_version_xml(show_config=True, show_copyright=True, to_file=None):
    if to_file is None:
        to_file = sys.stdout
    to_file.write(u'<version>')
    _show_bazaar_version(to_file=to_file)
    _show_python_version(to_file=to_file)
    print >> to_file
    to_file.write(u'</version>')


def _show_python_version(to_file):
    to_file.write(u'<python>')
    # show path to python interpreter
    # (bzr.exe use python interpreter from pythonXY.dll
    # but sys.executable point to bzr.exe itself)
    if not hasattr(sys, u'frozen'):  # check for bzr.exe
        # python executable
        to_file.write(u'<executable>%s</executable>' % sys.executable)
    else:
        # pythonXY.dll
        basedir = os.path.dirname(sys.executable)
        python_dll = u'python%d%d.dll' % sys.version_info[:2]
        to_file.write(u'<dll>%s</dll>' % os.path.join(basedir, python_dll))
    # and now version of python interpreter
    to_file.write(u'<version>%s</version>' % \
                  '.'.join(map(str, sys.version_info)))
    to_file.write(u'<standard_library>%s</standard_library>' % \
                  os.path.dirname(os.__file__))
    to_file.write(u'</python>')


def _show_bazaar_version(show_config=True, show_copyright=True, to_file=None):
    to_file.write('<bazaar>')
    to_file.write('<version>%s</version>' % bzrlib.__version__)
    # is bzrlib itself in a branch?
    _show_source_tree(to_file)
    to_file.write('<bzrlib>%s</bzrlib>' % _get_bzrlib_path())
    if show_config:
        _show_bzr_config(to_file)
    if show_copyright:
        to_file.write('<copyright>')
        _show_copyright(to_file)
        to_file.write('</copyright>')
    to_file.write('</bazaar>')


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
        to_file.write(u'<source_tree>')
        to_file.write(u'<checkout>%s</checkout>' % src_tree.basedir)
        to_file.write(u'<revision>%s</revision>' % revno)
        to_file.write(u'<revid>%s</revid>' % src_revision_id)
        to_file.write(u'<branch_nick>%s</branch_nick>' % \
                      _escape_cdata(src_tree.branch.nick))
        to_file.write(u'</source_tree>')


def _show_bzr_config(to_file):
    config_dir = os.path.normpath(config.config_dir())  # use native slashes
    if not isinstance(config_dir, unicode):
        config_dir = config_dir.decode(bzrlib.osutils.get_user_encoding())
    bzr_log_filename = trace._bzr_log_filename
    if not isinstance(bzr_log_filename, unicode):
        bzr_log_filename = trace._bzr_log_filename.decode(
            bzrlib.osutils.get_user_encoding())
    to_file.write('<configuration>%s</configuration>' % config_dir)
    to_file.write('<log_file>%s</log_file>' % bzr_log_filename)


def _show_copyright(to_file):
    to_file.write(bzrlib.__copyright__)
    to_file.write("http://bazaar-vcs.org/")
    to_file.write('')
    to_file.write("bzr comes with ABSOLUTELY NO WARRANTY.  bzr is free "
                  "software, and")
    to_file.write("you may use, modify and redistribute it under the terms "
                  "of the GNU")
    to_file.write("General Public License version 2 or later.")

