#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# @author Martin Albisetti
# (most of this code was modified from bzrlib.cmd_missing and bzrlib.missing)
# @version 0.1

"""Show unmerged/unpulled revisions between two branches.

OTHER_BRANCH may be local or remote.
"""


from bzrlib import ui, urlutils, errors
from bzrlib.branch import Branch
from bzrlib.log import LogRevision, log_formatter, log_formatter_registry
from bzrlib.missing import find_unmerged, iter_log_revisions

from bzrlib.symbol_versioning import (
    deprecated_function,
    zero_seventeen,
    )


def show_missing_xml(self, other_branch=None, reverse=False, mine_only=False,
        theirs_only=False, log_format=None, long=False, short=False, line=False, 
        show_ids=False, verbose=False, this=False, other=False):

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
        self.outf.write('<last_location="' + display_url + '">')

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
    if not status_code and parent is None and other_branch is not None:
        local_branch.lock_write()
        try:
            # handle race conditions - a parent might be set while we run.
            if local_branch.get_parent() is None:
                local_branch.set_parent(remote_branch.base)
        finally:
            local_branch.unlock()
    return status_code


@deprecated_function(zero_seventeen)
def iter_log_data(revisions, revision_source, verbose):
    for revision in iter_log_revisions(revisions, revision_source, verbose):
        yield revision.revno, revision.rev, revision.delta


def iter_log_revisions(revisions, revision_source, verbose):
    last_tree = revision_source.revision_tree(None)
    last_rev_id = None
    for revno, rev_id in revisions:
        rev = revision_source.get_revision(rev_id)
        if verbose:
            remote_tree = revision_source.revision_tree(rev_id)
            parent_rev_id = rev.parent_ids[0]
            if last_rev_id == parent_rev_id:
                parent_tree = last_tree
            else:
                parent_tree = revision_source.revision_tree(parent_rev_id)
            revision_tree = revision_source.revision_tree(rev_id)
            last_rev_id = rev_id
            last_tree = revision_tree
            delta = revision_tree.changes_from(parent_tree)
        else:
            delta = None
        yield LogRevision(rev, revno, delta=delta)


def find_unmerged(local_branch, remote_branch):
    progress = ui.ui_factory.nested_progress_bar()
    local_branch.lock_read()
    try:
        remote_branch.lock_read()
        try:
            local_rev_history, local_rev_history_map = \
                _get_history(local_branch, progress, "local", 0)
            remote_rev_history, remote_rev_history_map = \
                _get_history(remote_branch, progress, "remote", 1)
            result = _shortcut(local_rev_history, remote_rev_history)
            if result is not None:
                local_extra, remote_extra = result
                local_extra = sorted_revisions(local_extra, 
                                               local_rev_history_map)
                remote_extra = sorted_revisions(remote_extra, 
                                                remote_rev_history_map)
                return local_extra, remote_extra

            local_ancestry = _get_ancestry(local_branch.repository, progress, 
                                           "local", 2, local_rev_history)
            remote_ancestry = _get_ancestry(remote_branch.repository, progress,
                                            "remote", 3, remote_rev_history)
            progress.update('pondering', 4, 5)
            extras = local_ancestry.symmetric_difference(remote_ancestry) 
            local_extra = extras.intersection(set(local_rev_history))
            remote_extra = extras.intersection(set(remote_rev_history))
            local_extra = sorted_revisions(local_extra, local_rev_history_map)
            remote_extra = sorted_revisions(remote_extra, 
                                            remote_rev_history_map)
                    
        finally:
            remote_branch.unlock()
    finally:
        local_branch.unlock()
        progress.finished()
    return (local_extra, remote_extra)

def _shortcut(local_rev_history, remote_rev_history):
    local_history = set(local_rev_history)
    remote_history = set(remote_rev_history)
    if len(local_rev_history) == 0:
        return set(), remote_history
    elif len(remote_rev_history) == 0:
        return local_history, set()
    elif local_rev_history[-1] in remote_history:
        return set(), _after(remote_rev_history, local_rev_history)
    elif remote_rev_history[-1] in local_history:
        return _after(local_rev_history, remote_rev_history), set()
    else:
        return None

def _after(larger_history, smaller_history):
    return set(larger_history[larger_history.index(smaller_history[-1])+1:])

def _get_history(branch, progress, label, step):
    progress.update('%s history' % label, step, 5)
    rev_history = branch.revision_history()
    rev_history_map = dict(
        [(rev, rev_history.index(rev) + 1)
         for rev in rev_history])
    return rev_history, rev_history_map

def _get_ancestry(repository, progress, label, step, rev_history):
    progress.update('%s ancestry' % label, step, 5)
    if len(rev_history) > 0:
        ancestry = set(repository.get_ancestry(rev_history[-1],
                       topo_sorted=False))
    else:
        ancestry = set()
    return ancestry
    

def sorted_revisions(revisions, history_map):
    revisions = [(history_map[r],r) for r in revisions]
    revisions.sort()
    return revisions
