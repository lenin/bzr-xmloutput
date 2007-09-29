#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# @author Guillermo Gonzalez
# This code is a modified copy from bzrlib.info (see there for copyrights and licensing)

__all__ = ['show_bzrdir_info_xml']

import os
import time
import sys

from bzrlib import (
    bzrdir,
    diff,
    errors,
    osutils,
    urlutils,
    )
from bzrlib.errors import (NoWorkingTree, NotBranchError,
                           NoRepositoryPresent, NotLocalUrl)
from bzrlib.missing import find_unmerged
from bzrlib.symbol_versioning import (deprecated_function,
        zero_eighteen)
from bzrlib.info import gather_location_info, describe_format, describe_layout, LocationList, _gather_related_branches;

def get_lines_xml(self):
    return ["<%s>%s</%s>" % (l.replace(' ', '_'), u, l.replace(' ', '_')) for l, u in self.locs ]
LocationList.get_lines_xml = get_lines_xml

def show_bzrdir_info_xml(a_bzrdir, verbose=False):
    """Output to stdout the 'info' for a_bzrdir."""
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
        print '<?xml version="1.0"?>'
        print '<info>'
        show_component_info_xml(a_bzrdir, repository, branch, tree, verbose)
        print '</info>'
    finally:
        lockable.unlock()
        
def show_component_info_xml(control, repository, branch=None, working=None,
    verbose=1):
    """Write info about all bzrdir components to stdout"""
    if verbose is False:
        verbose = 1
    if verbose is True:
        verbose = 2
    layout = describe_layout(repository, branch, working)
    formats = describe_format(control, repository, branch, working).split(' or ')
    print '<layout>%s</layout>' % layout
    print '<formats>'
    if len(formats) > 1:
        for format in formats:
            print '<format>%s</format>' % format
    else:
        print '<format>%s</format>' % formats[0]
    print '</formats>'
    _show_location_info_xml(gather_location_info(repository, branch, working))
    if branch is not None:
        _show_related_info_xml(branch, sys.stdout)
    if verbose == 0:
        return
    _show_format_info_xml(control, repository, branch, working)
    _show_locking_info_xml(repository, branch, working)
    if branch is not None:
        _show_missing_revisions_branch_xml(branch)
    if working is not None:
        _show_missing_revisions_working_xml(working)
        _show_working_stats_xml(working)
    elif branch is not None:
        _show_missing_revisions_branch_xml(branch)
    if branch is not None:
        stats = _show_branch_stats_xml(branch, verbose==2)
    else:
        stats = repository.gather_stats()
    if branch is None and working is None:
        _show_repository_info_xml(repository)
    _show_repository_stats_xml(stats)


def _show_location_info_xml(locs):
    """Show known locations for working, branch and repository."""
    print '<location>'
    path_list = LocationList(osutils.getcwd())
    for name, loc in locs:
        path_list.add_url(name, loc)
    sys.stdout.writelines(path_list.get_lines_xml())
    print '</location>'
    
def _show_related_info_xml(branch, outfile):
    """Show parent and push location of branch."""
    locs = _gather_related_branches(branch)
    if len(locs.locs) > 0:
        print >> outfile, '<related_branches>'
        outfile.writelines(locs.get_lines_xml())
        print >> outfile, '</related_branches>'
        
def _show_format_info_xml(control=None, repository=None, branch=None, working=None):
    """Show known formats for control, working, branch and repository."""
    print '<format>'
    if control:
        print '<control>%s</control>' % control._format.get_format_description()
    if working:
        print '<working_tree>%s</working_tree>' % working._format.get_format_description()
    if branch:
        print '<branch>%s</branch>' % branch._format.get_format_description()
    if repository:
        print '<repository>%s</repository>' % repository._format.get_format_description()
    print '</format>'


def _show_locking_info_xml(repository, branch=None, working=None):
    """Show locking status of working, branch and repository."""
    if (repository.get_physical_lock_status() or
        (branch and branch.get_physical_lock_status()) or
        (working and working.get_physical_lock_status())):
        print '<lock_status>'
        if working:
            if working.get_physical_lock_status():
                status = 'locked'
            else:
                status = 'unlocked'
            print '<working_tree>%s</<working_tree>' % status
        if branch:
            if branch.get_physical_lock_status():
                status = 'locked'
            else:
                status = 'unlocked'
            print '<branch>%s</branch>' % status
        if repository:
            if repository.get_physical_lock_status():
                status = 'locked'
            else:
                status = 'unlocked'
            print '<repository>%s</repository>' % status
        print '</lock_status>'

def _show_missing_revisions_branch_xml(branch):
    """Show missing master revisions in branch."""
    # Try with inaccessible branch ?
    master = branch.get_master_branch()
    if master:
        local_extra, remote_extra = find_unmerged(branch, master)
        if remote_extra:
            print
            print 'Branch is out of date: missing %d revision%s.' % (
                len(remote_extra), plural(len(remote_extra)))


def _show_missing_revisions_working_xml(working):
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
        print
        print 'Working tree is out of date: missing %d revision%s.' % (
            missing_count, plural(missing_count))

def _show_working_stats_xml(working):
    """Show statistics about a working tree."""
    basis = working.basis_tree()
    work_inv = working.inventory
    delta = working.changes_from(basis, want_unchanged=True)

    print '<working_tree_stats>'
    print '<unchanged>%s</unchanged>' % len(delta.unchanged)
    print '<modified>%d</modified>' % len(delta.modified)
    print '<added>%d</added>' % len(delta.added)
    print '<removed>%d</removed>' % len(delta.removed)
    print '<renamed>%d</renamed>' % len(delta.renamed)

    ignore_cnt = unknown_cnt = 0
    for path in working.extras():
        if working.is_ignored(path):
            ignore_cnt += 1
        else:
            unknown_cnt += 1
    print '<unknown>%d</unknown>' % unknown_cnt
    print '<ignored>%d</ignored>' % ignore_cnt

    dir_cnt = 0
    for file_id in work_inv:
        if (work_inv.get_file_kind(file_id) == 'directory' and 
            not work_inv.is_root(file_id)):
            dir_cnt += 1
    print '<versioned_subdirectories>%d</versioned_subdirectories>' % (dir_cnt)
    
    print '</working_tree_stats>'

def _show_branch_stats_xml(branch, verbose):
    """Show statistics about a branch."""
    revno, head = branch.last_revision_info()
    print '<branch_history>'
    print '<revisions>%d</revisions>' % (revno)
    stats = branch.repository.gather_stats(head, committers=verbose)
    if verbose:
        committers = stats['committers']
        print '<committers>%d</committers>' % (committers)
    if revno:
        timestamp, timezone = stats['firstrev']
        age = int((time.time() - timestamp) / 3600 / 24)
        print '<days_old>%d</days_old>' % (age)
        print '<first_revision>%s</first_revision>' % osutils.format_date(timestamp,
            timezone)
        timestamp, timezone = stats['latestrev']
        print '<latest_revision>%s</latest_revision>' % osutils.format_date(timestamp,
            timezone)
    print '</branch_history>'
    return stats

def _show_repository_info_xml(repository):
    """Show settings of a repository."""
    if repository.make_working_trees():
        print
        print 'Create working tree for new branches inside the repository.'


def _show_repository_stats_xml(stats):
    """Show statistics about a repository."""
    if 'revisions' in stats or 'size' in stats:
        print '<repository_stats>'
    if 'revisions' in stats:
        revisions = stats['revisions']
        print '<revisions>%d</revisions>' % (revisions)
    if 'size' in stats:
        print '<size unit="KiB">%d</size>' % (stats['size']/1024)
    if 'revisions' in stats or 'size' in stats:
        print '</repository_stats>'
