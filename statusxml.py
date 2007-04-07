#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# @author Guillermo Gonzalez
# (most of this code was modified from from bzrlib.cmd_status, bzrlib.status and bzrlib.delta.TreeDelta.show)
# @version 0.1

from bzrlib.diff import _raise_if_nonexistent

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
            print >>to_file, '<?xml version="1.0"?>'
            print >>to_file, '<status workingtree_root="%s">' % \
                          wt.id2abspath(wt.get_root_id())
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
                       show_unchanged=show_unchanged)
            conflict_title = False
            # show the new conflicts only for now. XXX: get them from the delta.
            if len(new.conflicts()) > 0: 
                print >> to_file, "<conflicts>"
                for conflict in new.conflicts():
                    print >> to_file, "<conflict>%s</conflict>" % (conflict)
                print >> to_file, "</conflicts>"
            if new_is_working_tree and show_pending:
                show_pending_merges(new, to_file)
            print >>to_file, '</status>'
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
    print >>to_file, '<pending_merges>'
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
            prefix = ' '
            print >> to_file, prefix, line_log(m_revision, width - 4)
            inner_merges = branch.repository.get_ancestry(merge)
            assert inner_merges[0] is None
            inner_merges.pop(0)
            inner_merges.reverse()
            for mmerge in inner_merges:
                if mmerge in ignore:
                    continue
                mm_revision = branch.repository.get_revision(mmerge)
                prefix = '   '
                print >> to_file, prefix, line_log(mm_revision, width - 5)
                ignore.add(mmerge)
        except errors.NoSuchRevision:
            prefix = ' '
            print >> to_file, prefix, merge
    print >>to_file, '</pending_merges>'

def show_tree_xml(delta, to_file, show_ids=False, show_unchanged=False):
    """output this delta in a (xml) status-like form to to_file.
    
    """
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
                print >>to_file, '<%s %s>%s</%s>' % (kind, kind_id, path, kind)
            else:
                print >>to_file, '<%s>%s</%s>' % (kind, path, kind)

    if delta.removed:
        print >>to_file, '<removed>'
        show_list(delta.removed)
        print >>to_file, '</removed>'
    
    if delta.added:
        print >>to_file, '<added>'
        show_list(delta.added)
        print >>to_file, '</added>'
    
    extra_modified = []
    if delta.renamed:
        print >>to_file, '<renamed>'
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
                print >>to_file, '<%s oldpath="%s" %s %s>%s</%s>' % \
                        (kind, oldpath, metamodified, kind_id, newpath, kind)
            else: 
                print >>to_file, '<%s oldpath="%s" %s >%s</%s>' % \
                        (kind, oldpath, metamodified, newpath, kind)
        print >>to_file, '</renamed>'

    if delta.kind_changed:
        print >>to_file, '<kind changed>'
        for (path, fid, old_kind, new_kind) in delta.kind_changed:
            if show_ids:
                suffix = 'suffix="%s"' % fid
            else:
                suffix = ''
            print >>to_file, '<%s oldkind="%s" newkind="%s" %s>%s</%s>' % \
                       (new_kind, old_kind, new_kind, suffix, path, new_kind)
        print >>to_file, '</kind changed>'

    if delta.modified or extra_modified:
        print >>to_file, '<modified>'
        show_list(delta.modified)
        show_list(extra_modified)
        print >>to_file, '</modified>'
            
    if show_unchanged and delta.unchanged:
        print >>to_file, '<unchanged>'
        show_list(delta.unchanged)
        print >>to_file, '</unchanged>'

    if delta.unversioned:
        print >>to_file, '<unknown>'
        show_list(delta.unversioned)
        print >>to_file, '</unknown>'

def get_kind_id_element(kind, fid):
    kind_id=''
    if kind == 'directory':
        kind_id='suffix="%s"' % fid
    elif kind == 'symlink':
        kind_id=''
    else:
        kind_id='fid="%s"' %fid
    return kind_id
