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

import bzrlib
from bzrlib.diff import _raise_if_nonexistent
from bzrlib.trace import warning
import bzrlib.errors as errors
from bzrlib.xml_serializer import _escape_cdata
from logxml import line_log

def show_tree_status_xml(wt, show_unchanged=None,
                     specific_files=None,
                     show_ids=False,
                     to_file=None,
                     show_pending=True,
                     revision=None,
                     versioned=False):
    """Display summary of changes as XML.

    Almost equal to status.show_tree_status, except the --short option and the
    output is in xml format.
    This reports on versioned and unknown files, reporting them
    grouped by state.  Possible states are:

    <added/>
    <removed/>
    <renamed/>
    <modified/>
    <kind changed/>
    <unknown/>
    
    Each group can have multiple child's of this element's:

    <file [oldpath] [oldkind, newkind] [fid]>
    <directory [oldpath] [oldkind, newkind] [suffix]>

    A simple example: 
    <status workingtree_root="/home/guillo/Unison-root/sandbox/bazaar/bzr/0.15/">
        <renamed>
            <file oldpath="INSTALL"  >INSTALL.txt</file>
        </renamed>
        <kind-changed>
            <directory oldkind="file" newkind="directory">NEWS</directory>
        </kind-changed>
        <modified>
            <file>bzrlib/symbol_versioning.py</file>
        </modified>
        <unknown>
            <file>.project</file>
            <directory>bzrlib/dir/</directory>
        </unknown>
    </status>

    By default this compares the working tree to a previous revision. 
    If the revision argument is given, summarizes changes between the 
    working tree and another, or between two revisions.

    The result is written out as Unicode and to_file should be able 
    to encode that.

    If showing the status of a working tree, extra information is included
    about unknown files, conflicts, and pending merges.

    :param show_unchanged: Deprecated parameter. If set, includes unchanged 
        files.
    :param specific_files: If set, a list of filenames whose status should be
        shown.  It is an error to give a filename that is not in the working 
        tree, or in the working inventory or in the basis inventory.
    :param show_ids: If set, includes each file's id.
    :param to_file: If set, write to this file (default stdout.)
    :param show_pending: If set, write pending merges.
    :param revision: If None the compare latest revision with working tree
        If not None it must be a RevisionSpec list.
        If one revision show compared it with working tree.
        If two revisions show status between first and second.
    :param versioned: If True, only shows versioned files.
    """
    if show_unchanged is not None:
        warn("show_status_trees with show_unchanged has been deprecated "
             "since bzrlib 0.9", DeprecationWarning, stacklevel=2)

    if to_file is None:
        to_file = sys.stdout
    
    wt.lock_read()
    try:
        new_is_working_tree = True
        if revision is None:
            if wt.last_revision() != wt.branch.last_revision():
                warning("working tree is out of date, run 'bzr update'")
            new = wt
            old = new.basis_tree()
        elif len(revision) > 0:
            try:
                rev_id = revision[0].in_history(wt.branch).rev_id
                old = wt.branch.repository.revision_tree(rev_id)
            except errors.NoSuchRevision, e:
                raise errors.BzrCommandError(str(e))
            if (len(revision) > 1) and (revision[1].spec is not None):
                try:
                    rev_id = revision[1].in_history(wt.branch).rev_id
                    new = wt.branch.repository.revision_tree(rev_id)
                    new_is_working_tree = False
                except errors.NoSuchRevision, e:
                    raise errors.BzrCommandError(str(e))
            else:
                new = wt
        old.lock_read()
        new.lock_read()
        try:
            _raise_if_nonexistent(specific_files, old, new)
            want_unversioned = not versioned
            to_file.write('<?xml version="1.0" encoding="%s"?>' % \
                        bzrlib.user_encoding)
            to_file.write('<status workingtree_root="%s">' % \
                        wt.id2abspath(wt.get_root_id()))
            delta = new.changes_from(old, want_unchanged=show_unchanged,
                                  specific_files=specific_files,
                                  want_unversioned=want_unversioned)
            # filter out unknown files. We may want a tree method for
            # this
            delta.unversioned = [unversioned for unversioned in
                delta.unversioned if not new.is_ignored(unversioned[0])]
            #delta.show(to_file,
            show_tree_xml(delta, to_file,
                       show_ids=show_ids,
                       show_unchanged=show_unchanged, 
                       show_unversioned=want_unversioned)
            conflict_title = False
            # show the new conflicts only for now. XXX: get them from the delta.
            conflicts = new.conflicts()
            if specific_files is not None:
                conflicts = conflicts.select_conflicts(new, specific_files,
                        ignore_misses=True, recurse=True)[1]
            if len(conflicts) > 0:
                to_file.write("<conflicts>")
                for conflict in conflicts:
                    to_file.write('<conflict type="%s">%s</conflict>' % 
                                  (conflict.typestring, _escape_cdata(conflict.path)))
                to_file.write("</conflicts>")
            if new_is_working_tree and show_pending:
                show_pending_merges(new, to_file)
            to_file.write('</status>')
        finally:
            old.unlock()
            new.unlock()
    finally:
        wt.unlock()

def show_pending_merges(new, to_file):
    """Write out a display of pending merges in a working tree."""
    parents = new.get_parent_ids()
    if len(parents) < 2:
        return
    pending = parents[1:]
    branch = new.branch
    last_revision = parents[0]
    to_file.write('<pending_merges>')
    if last_revision is not None:
        try:
            ignore = set(branch.repository.get_ancestry(last_revision))
        except errors.NoSuchRevision:
            # the last revision is a ghost : assume everything is new 
            # except for it
            ignore = set([None, last_revision])
    else:
        ignore = set([None])
    # TODO: this could be improved using merge_sorted - we'd get the same 
    # output rather than one level of indent.
    for merge in pending:
        ignore.add(merge)
        try:
            from bzrlib.osutils import terminal_width
            width = terminal_width()
            m_revision = branch.repository.get_revision(merge)
            to_file.write(line_log(m_revision))
            inner_merges = branch.repository.get_ancestry(merge)
            assert inner_merges[0] is None
            inner_merges.pop(0)
            inner_merges.reverse()
            for mmerge in inner_merges:
                if mmerge in ignore:
                    continue
                mm_revision = branch.repository.get_revision(mmerge)
                prefix = '   '
                to_file.write(prefix, line_log(mm_revision))
                ignore.add(mmerge)
        except errors.NoSuchRevision:
            to_file.write('<pending_merge>%s</pending_merge>' % merge)
    to_file.write('</pending_merges>')

def show_tree_xml(delta, to_file, show_ids=False, show_unchanged=False,
        short_status=False, show_unversioned=False):
    """output this delta in a (xml) status-like form to to_file."""
    def show_list(files):
        for item in files:
            path, fid, kind = item[:3]
            if kind == 'directory':
                path += '/'
            elif kind == 'symlink':
                path += '@'
            if len(item) == 5 and item[4]:
                path += '*'
            if show_ids:
                kind_id=''
                if fid:
                    kind_id=get_kind_id_element(kind, fid)
                to_file.write('<%s %s>%s</%s>' % (kind, kind_id, 
                                                  _escape_cdata(path), kind))
            else:
                to_file.write('<%s>%s</%s>' % (kind, _escape_cdata(path), kind))

    if delta.removed:
        to_file.write('<removed>')
        show_list(delta.removed)
        to_file.write('</removed>')
    
    if delta.added:
        to_file.write('<added>')
        show_list(delta.added)
        to_file.write('</added>')
    
    extra_modified = []
    if delta.renamed:
        to_file.write('<renamed>')
        for (oldpath, newpath, fid, kind, 
             text_modified, meta_modified) in delta.renamed:
            if text_modified or meta_modified:
                extra_modified.append((newpath, fid, kind, 
                                text_modified, meta_modified))
            metamodified = ''
            if meta_modified:
                metamodified = 'meta_modified="true"'
            if show_ids:
                kind_id=''
                if fid:
                    kind_id=get_kind_id_element(kind, fid)
                to_file.write('<%s oldpath="%s" %s %s>%s</%s>' % \
                        (kind, _escape_cdata(oldpath), metamodified, 
                         kind_id, _escape_cdata(newpath), kind))
            else: 
                to_file.write('<%s oldpath="%s" %s >%s</%s>' % \
                        (kind, _escape_cdata(oldpath), metamodified, 
                         _escape_cdata(newpath), kind))
        to_file.write('</renamed>')

    if delta.kind_changed:
        to_file.write('<kind_changed>')
        for (path, fid, old_kind, new_kind) in delta.kind_changed:
            if show_ids:
                suffix = 'suffix="%s"' % fid
            else:
                suffix = ''
            to_file.write('<%s oldkind="%s" %s>%s</%s>' % \
                       (new_kind, old_kind, suffix, 
                        _escape_cdata(path), new_kind))
        to_file.write('</kind_changed>')

    if delta.modified or extra_modified:
        to_file.write('<modified>')
        show_list(delta.modified)
        show_list(extra_modified)
        to_file.write('</modified>')
            
    if show_unchanged and delta.unchanged:
        to_file.write('<unchanged>')
        show_list(delta.unchanged)
        to_file.write('</unchanged>')

    if show_unversioned and delta.unversioned:
        to_file.write('<unknown>')
        show_list(delta.unversioned)
        to_file.write('</unknown>')

def get_kind_id_element(kind, fid):
    kind_id=''
    if kind == 'directory':
        kind_id='suffix="%s"' % fid
    elif kind == 'symlink':
        kind_id=''
    else:
        kind_id='fid="%s"' %fid
    return kind_id

