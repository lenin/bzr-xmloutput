#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright (C) 2007 Guillermo Gonzalez
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
#               Martin Albisetti

"""This code is a modified copy from bzrlib.info (see there for copyrights and licensing)"""

__all__ = ['show_bzrdir_info_xml']

from bzrlib.lazy_import import lazy_import
lazy_import(globals(), """
import os, sys, time
from bzrlib import (
    bzrdir,
    diff,
    errors,
    osutils,
    urlutils,
    info,
    missing,
    )
""")

from bzrlib.errors import (NoWorkingTree, NotBranchError,
                           NoRepositoryPresent, NotLocalUrl)
from bzrlib.symbol_versioning import (deprecated_function,
        zero_eighteen)

def get_lines_xml(self):
    return ["<%s>%s</%s>" % (l.replace(' ', '_'), u, l.replace(' ', '_')) for l, u in self.locs ]
info.LocationList.get_lines_xml = get_lines_xml

def show_bzrdir_info_xml(a_bzrdir, verbose=False, outfile=None):
    """Output to stdout the 'info' for a_bzrdir."""
    if outfile is None:
        outfile = sys.stdout
    try:
        tree = a_bzrdir.open_workingtree(
            recommend_upgrade=False)
    except (NoWorkingTree, NotLocalUrl):
        tree = None
        try:
            branch = a_bzrdir.open_branch()
        except NotBranchError:
            branch = None
            try:
                repository = a_bzrdir.open_repository()
            except NoRepositoryPresent:
                # Return silently; cmd_info already returned NotBranchError
                # if no bzrdir could be opened.
                return
            else:
                lockable = repository
        else:
            repository = branch.repository
            lockable = branch
    else:
        branch = tree.branch
        repository = branch.repository
        lockable = tree

    lockable.lock_read()
    try:
        outfile.write('<?xml version="1.0"?>')
        outfile.write('<info>')
        show_component_info_xml(a_bzrdir, repository, branch, tree, verbose, 
                                outfile)
        outfile.write('</info>')
    finally:
        lockable.unlock()
        
def show_component_info_xml(control, repository, branch=None, 
                            working=None, verbose=1, outfile=None):
    """Write info about all bzrdir components to stdout"""
    if outfile is None:
        outfile = sys.stdout
    if verbose is False:
        verbose = 1
    if verbose is True:
        verbose = 2
    layout = info.describe_layout(repository, branch, working)
    formats = info.describe_format(control, repository, branch, working).split(' or ')
    outfile.write('<layout>%s</layout>' % layout)
    outfile.write('<formats>')
    if len(formats) > 1:
        for format in formats:
            outfile.write('<format>%s</format>' % format)
    else:
        outfile.write('<format>%s</format>' % formats[0])
    outfile.write('</formats>')
    _show_location_info_xml(info.gather_location_info(repository, branch, 
                            working), outfile)
    if branch is not None:
        _show_related_info_xml(branch, outfile)
    if verbose == 0:
        return
    _show_format_info_xml(control, repository, branch, working, outfile)
    _show_locking_info_xml(repository, branch, working, outfile)
    if branch is not None:
        _show_missing_revisions_branch_xml(branch, outfile)
    if working is not None:
        _show_working_stats_xml(working, outfile)
    elif branch is not None:
        _show_missing_revisions_branch_xml(branch, outfile)
    if branch is not None:
        stats = _show_branch_stats_xml(branch, verbose==2, outfile)
    else:
        stats = repository.gather_stats()
    if branch is None and working is None:
        _show_repository_info_xml(repository, outfile)
    _show_repository_stats_xml(stats, outfile)


def _show_location_info_xml(locs, outfile):
    """Show known locations for working, branch and repository."""
    outfile.write('<location>')
    path_list = info.LocationList(osutils.getcwd())
    for name, loc in locs:
        path_list.add_url(name, loc)
    outfile.writelines(path_list.get_lines_xml())
    outfile.write('</location>')
    
def _show_related_info_xml(branch, outfile):
    """Show parent and push location of branch."""
    locs = info._gather_related_branches(branch)
    if len(locs.locs) > 0:
        outfile.write('<related_branches>')
        outfile.writelines(locs.get_lines_xml())
        outfile.write('</related_branches>')
        
def _show_format_info_xml(control=None, repository=None, 
                          branch=None, working=None, outfile=None):
    """Show known formats for control, working, branch and repository."""
    outfile.write('<format>')
    if control:
        outfile.write('<control>%s</control>' % 
                      control._format.get_format_description())
    if working:
        outfile.write('<working_tree>%s</working_tree>' % 
                      working._format.get_format_description())
    if branch:
        outfile.write('<branch>%s</branch>' % 
                      branch._format.get_format_description())
    if repository:
        outfile.write('<repository>%s</repository>' % 
               repository._format.get_format_description())
    outfile.write('</format>')


def _show_locking_info_xml(repository, branch=None, working=None, outfile=None):
    """Show locking status of working, branch and repository."""
    if (repository.get_physical_lock_status() or
        (branch and branch.get_physical_lock_status()) or
        (working and working.get_physical_lock_status())):
        outfile.write('<lock_status>')
        if working:
            if working.get_physical_lock_status():
                status = 'locked'
            else:
                status = 'unlocked'
            outfile.write('<working_tree>%s</<working_tree>' % status)
        if branch:
            if branch.get_physical_lock_status():
                status = 'locked'
            else:
                status = 'unlocked'
            outfile.write('<branch>%s</branch>' % status)
        if repository:
            if repository.get_physical_lock_status():
                status = 'locked'
            else:
                status = 'unlocked'
            outfile.write('<repository>%s</repository>' % status)
        outfile.write('</lock_status>')

def _show_missing_revisions_branch_xml(branch, outfile):
    """Show missing master revisions in branch."""
    # Try with inaccessible branch ?
    master = branch.get_master_branch()
    if master:
        local_extra, remote_extra = missing.find_unmerged(branch, master)
        if remote_extra:
            outfile.write('<branch_stats>')
            outfile.write('<missing_revisions>%d<missing_revisions>' % 
                          len(remote_extra))
            outfile.write('</branch_stats>')


def _show_missing_revisions_working_xml(working, outfile):
    """Show missing revisions in working tree."""
    branch = working.branch
    basis = working.basis_tree()
    work_inv = working.inventory
    branch_revno, branch_last_revision = branch.last_revision_info()
    try:
        tree_last_id = working.get_parent_ids()[0]
    except IndexError:
        tree_last_id = None

    if branch_revno and tree_last_id != branch_last_revision:
        tree_last_revno = branch.revision_id_to_revno(tree_last_id)
        missing_count = branch_revno - tree_last_revno
        outfile.write('<missing_revisions>%d</missing_revisions>' % 
                      missing_count)

def _show_working_stats_xml(working, outfile):
    """Show statistics about a working tree."""
    basis = working.basis_tree()
    work_inv = working.inventory
    delta = working.changes_from(basis, want_unchanged=True)

    outfile.write('<working_tree_stats>')
    _show_missing_revisions_working_xml(working, outfile)
    outfile.write('<unchanged>%s</unchanged>' % len(delta.unchanged))
    outfile.write('<modified>%d</modified>' % len(delta.modified))
    outfile.write('<added>%d</added>' % len(delta.added))
    outfile.write('<removed>%d</removed>' % len(delta.removed))
    outfile.write('<renamed>%d</renamed>' % len(delta.renamed))

    ignore_cnt = unknown_cnt = 0
    for path in working.extras():
        if working.is_ignored(path):
            ignore_cnt += 1
        else:
            unknown_cnt += 1
    outfile.write('<unknown>%d</unknown>' % unknown_cnt)
    outfile.write('<ignored>%d</ignored>' % ignore_cnt)

    dir_cnt = 0
    for file_id in work_inv:
        if (work_inv.get_file_kind(file_id) == 'directory' and 
            not work_inv.is_root(file_id)):
            dir_cnt += 1
    outfile.write('<versioned_subdirectories>%d</versioned_subdirectories>' % 
                 (dir_cnt))
    
    outfile.write('</working_tree_stats>')

def _show_branch_stats_xml(branch, verbose, outfile):
    """Show statistics about a branch."""
    revno, head = branch.last_revision_info()
    outfile.write('<branch_history>')
    outfile.write('<revisions>%d</revisions>' % (revno))
    stats = branch.repository.gather_stats(head, committers=verbose)
    if verbose:
        committers = stats['committers']
        outfile.write('<committers>%d</committers>' % (committers))
    if revno:
        timestamp, timezone = stats['firstrev']
        age = int((time.time() - timestamp) / 3600 / 24)
        outfile.write('<days_old>%d</days_old>' % (age))
        outfile.write('<first_revision>%s</first_revision>' % \
               osutils.format_date(timestamp, timezone))
        timestamp, timezone = stats['latestrev']
        outfile.write('<latest_revision>%s</latest_revision>' % \
               osutils.format_date(timestamp, timezone))
    outfile.write('</branch_history>')
    return stats

def _show_repository_info_xml(repository, outfile):
    """Show settings of a repository."""
    ## FIXME/TODO: is this needed in the xml output?
    #if repository.make_working_trees():
    #    print 'Create working tree for new branches inside the repository.'


def _show_repository_stats_xml(stats, outfile):
    """Show statistics about a repository."""
    if 'revisions' in stats or 'size' in stats:
        outfile.write('<repository_stats>')
    if 'revisions' in stats:
        revisions = stats['revisions']
        outfile.write('<revisions>%d</revisions>' % (revisions))
    if 'size' in stats:
        outfile.write('<size unit="KiB">%d</size>' % (stats['size']/1024))
    if 'revisions' in stats or 'size' in stats:
        outfile.write('</repository_stats>')
