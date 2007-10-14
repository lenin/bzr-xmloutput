#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright (C) 2007 Martin Albisetti
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
# Contributors:
#               Guillermo Gonzalez

# (most of this code was modified from bzrlib.cmd_missing and bzrlib.missing)

"""Show unmerged/unpulled revisions between two branches.

OTHER_BRANCH may be local or remote.
"""


from bzrlib import ui, urlutils, errors
from bzrlib.branch import Branch
from bzrlib.log import LogRevision, log_formatter, log_formatter_registry
from bzrlib.missing import (
        iter_log_data, 
        iter_log_revisions, 
        find_unmerged, 
        _shortcut, 
        _after, 
        _get_history, 
        _get_ancestry, 
        sorted_revisions)

def show_missing_xml(self, other_branch=None, reverse=False, mine_only=False,
        theirs_only=False, log_format=None, long=False, short=False, line=False, 
        show_ids=False, verbose=False, this=False, other=False):
        
    self.outf.write('<missing>')
        
    if this:
      mine_only = this
    if other:
      theirs_only = other

    local_branch = Branch.open_containing(u".")[0]
    parent = local_branch.get_parent()
    if other_branch is None:
        other_branch = parent
        if other_branch is None:
            raise errors.BzrCommandError("No peer location known"
                                          " or specified.")
    display_url = urlutils.unescape_for_display(parent,
                                                self.outf.encoding)
    self.outf.write('<last_location>' + display_url + '</last_location>')
    
    remote_branch = Branch.open(other_branch)
    
    if remote_branch.base == local_branch.base:
        remote_branch = local_branch
    local_branch.lock_read()
    try:
        remote_branch.lock_read()
        try:
            local_extra, remote_extra = find_unmerged(local_branch,
                                                      remote_branch)
            if log_format is None:
                registry = log_formatter_registry
                log_format = registry.get_default(local_branch)
            lf = log_format(to_file=self.outf,
                            show_ids=show_ids,
                            show_timezone='original')
            if reverse is False:
                local_extra.reverse()
                remote_extra.reverse()
            if local_extra and not theirs_only:
                self.outf.write('<extra_revisions>%d</extra_revisions>' %
                                len(local_extra))
                self.outf.write('</missing>')
                for revision in iter_log_revisions(local_extra,
                                    local_branch.repository,
                                    verbose):
                    lf.log_revision(revision)
                printed_local = True
            else:
                printed_local = False
            if remote_extra and not mine_only:
                # if printed_local is True:
                    # self.outf.write("\n\n\n")
                self.outf.write('<missing_revisions>%d</missing_revisions>' %
                                len(remote_extra))
                self.outf.write('</missing>')
                for revision in iter_log_revisions(remote_extra,
                                    remote_branch.repository,
                                    verbose):
                    lf.log_revision(revision)
            if not remote_extra and not local_extra:
                status_code = 0
                # self.outf.write("Branches are up to date.\n")
            else:
                status_code = 1
        finally:
            remote_branch.unlock()
    finally:
        local_branch.unlock()
    
    if printed_local == False:
        self.outf.write('</missing>')
        
    if not status_code and parent is None and other_branch is not None:
        local_branch.lock_write()
        try:
            # handle race conditions - a parent might be set while we run.
            if local_branch.get_parent() is None:
                local_branch.set_parent(remote_branch.base)
        finally:
            local_branch.unlock()
    return status_code


