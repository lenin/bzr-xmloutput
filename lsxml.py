#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright (C) 2008 Mirko Friedenhagen
#
# The code taken from bzrlib is under: Copyright (C) 2005, 2006, 2007 Canonical Ltd
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

from bzrlib.lazy_import import lazy_import
lazy_import(globals(), """
from bzrlib import bzrdir, errors, osutils
""")

from writer import _escape_cdata


def show_ls_xml(outf, revision=None, non_recursive=False,
            from_root=False, unknown=False, versioned=False,
            ignored=False, kind=None, path=None, verbose=False):

    if kind and kind not in ('file', 'directory', 'symlink'):
        raise errors.BzrCommandError('invalid kind specified')

    all = not (unknown or versioned or ignored)

    selection = {'I':ignored, '?':unknown, 'V':versioned}
    long_status_kind = {'I':'ignored', '?':'unknown', 'V':'versioned'}

    if path is None:
        fs_path = '.'
    else:
        if from_root:
            raise errors.BzrCommandError('cannot specify both --from-root'
                                         ' and PATH')
        fs_path = path
    tree, branch, relpath = bzrdir.BzrDir.open_containing_tree_or_branch(
            fs_path)

    prefix = None
    if from_root:
        if relpath:
            prefix = relpath + '/'
    elif fs_path != '.':
        prefix = fs_path + '/'

    if revision is not None:
        tree = branch.repository.revision_tree(
            revision[0].as_revision_id(branch))
    elif tree is None:
        tree = branch.basis_tree()

    tree.lock_read()
    try:
        outf.write('<list>')
        for fp, fc, fkind, fid, entry in tree.list_files(include_root=False,
                from_dir=relpath, recursive=not non_recursive):
            if not all and not selection[fc]:
                continue
            if kind is not None and fkind != kind:
                continue
            if prefix:
                fp = osutils.pathjoin(prefix, fp)
            if fid is None:
                fid = ''
            else:
                fid = '<id>%s</id>' % _escape_cdata(fid)
            fkind = '<kind>%s</kind>' % fkind
            status_kind = '<status_kind>%s</status_kind>' % long_status_kind[fc]
            fpath = '<path>%s</path>' % _escape_cdata(fp)
            if fc == 'I' and ignored:
                # get the pattern
                if tree.basedir in fp:
                    pat = tree.is_ignored(tree.relpath(fp))
                else:
                    pat = tree.is_ignored(fp)
                pattern = '<pattern>%s</pattern>' % _escape_cdata(pat)
            else:
                pattern = ''
            outstring = '<item>%s%s%s%s%s</item>' % (fid, fkind, fpath,
                                                   status_kind, pattern)
            outf.write(outstring)
    finally:
        outf.write('</list>')
        tree.unlock()


