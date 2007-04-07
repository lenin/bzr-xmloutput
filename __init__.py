#!/usr/bin/env python2.4

# @author Guillermo Gonzalez
# @version 0.1
"""
This plugin provides xml output for three commands (status, log, annotate)
adding a --xml option to each

(most of this is code was modified from bzrlib.cmd_status, 
bzrlib.status, bzrlib.delta.TreeDelta.show and bzrlib.log.LongLogFormatter)
"""
from bzrlib.commands import display_command, Command, register_command
from bzrlib import builtins
from bzrlib.log import log_formatter, show_log, LogFormatter, log_formatter_registry
from bzrlib.option import Option
from bzrlib.workingtree import WorkingTree
import sys

class cmd_status(builtins.cmd_status):
    builtins.cmd_status.takes_options.append(Option('xml', help='output in xml format'))
    __doc__ = builtins.cmd_status.__doc__
    @display_command
    def run(self, show_ids=False, file_list=None, revision=None, short=False,
            versioned=False, xml=False):
        if xml:
            from statusxml import show_tree_status_xml
            tree, file_list = builtins.tree_files(file_list)
            show_tree_status_xml(tree, show_ids=show_ids,
                    specific_files=file_list, revision=revision,
                    to_file=self.outf, versioned=False)
        else:
            status_class.run(self, show_ids=show_ids, file_list=file_list, 
                    revision=revision, short=short, versioned=versioned)

status_class = register_command(cmd_status, decorate=True)

class cmd_annotate(builtins.cmd_annotate):
    builtins.cmd_annotate.takes_options.append(Option('xml', help='output in xml format'))
    __doc__ = builtins.cmd_annotate.__doc__

    @display_command
    def run(self, filename, all=False, long=False, revision=None,
            show_ids=False, xml=False):
        if xml:
            from annotatexml import annotate_file_xml
            tree, relpath = WorkingTree.open_containing(filename)
            wt_root_path = tree.id2abspath(tree.get_root_id())
            branch = tree.branch
            branch.lock_read()
            try:
                if revision is None:
                    revision_id = branch.last_revision()
                elif len(revision) != 1:
                    raise errors.BzrCommandError('bzr annotate --revision takes exactly 1 argument')
                else:
                    revision_id = revision[0].in_history(branch).rev_id
                file_id = tree.path2id(relpath)
                tree = branch.repository.revision_tree(revision_id)
                file_version = tree.inventory[file_id].revision
                # always run with --all and --long option (to get the author of each line)
                annotate_file_xml(branch=branch, rev_id=file_version, 
                        file_id=file_id, verbose=True, full=True, to_file=sys.stdout,
                        show_ids=show_ids, wt_root_path=wt_root_path)
            finally:
                branch.unlock()
        else:
            annotate_class.run(self, filename=filename, all=all, long=long, revision=revision,
            show_ids=show_ids)

annotate_class = register_command(cmd_annotate, decorate=True)

class XMLLogFormatter(LogFormatter):
    """ add a --xml format to 'bzr log'"""
    def __init__(self, to_file, show_ids=False, show_timezone='original'):
        super(XMLLogFormatter, self).__init__(to_file=to_file, 
                               show_ids=show_ids, show_timezone=show_timezone)

    def show(self, revno, rev, delta):
        return self._show_helper(revno=revno, rev=rev, delta=delta)

    def show_merge_revno(self, rev, merge_depth, revno):
        """a call to self._show_helper, XML don't care about formatting """
        return self._show_helper(revno=revno, rev=rev, merged=True, delta=None)

    def _show_helper(self, rev=None, revno=None, indent='', 
                    merged=False, delta=None):
        """Show a revision, either merged or not."""
        from xml.sax import saxutils
        from bzrlib.osutils import format_date
        to_file = self.to_file
        print >>to_file,  '<log>',
        if revno is not None:
            print >>to_file,  '<revno>%s</revno>' % revno,
        if merged:
            print >>to_file,  '<merged>%s</merged>' % rev.revision_id,
        elif self.show_ids:
            print >>to_file,  '<revision-id>%s</revision_id>' % rev.revision_id,
        if self.show_ids:
            if len(rev.parent_ids) > 0:
                print >>to_file, '<parents>',
            for parent_id in rev.parent_ids:
                print >>to_file, '<parent>%s</parent>' % parent_id,
            if len(rev.parent_ids) > 0:
                print >>to_file, '</parents>',
        print >>to_file,  '<committer>%s</committer>' % \
                        saxutils.escape(rev.committer),
        try:
            print >>to_file, '<branch-nick>%s</branch-nick>' % \
                saxutils.escape(rev.properties['branch-nick']),
        except KeyError:
            pass
        date_str = format_date(rev.timestamp,
                               rev.timezone or 0,
                               self.show_timezone)
        print >>to_file,  '<timestamp>%s</timestamp>' % date_str,

        print >>to_file,  '<message>',
        if not rev.message:
            print >>to_file,  '  (no message)',
        else:
            print >>to_file,  saxutils.escape(rev.message),
        print >>to_file,  '</message>',
        if delta is not None:
            from statusxml import show_tree_xml
            #delta.show(to_file, self.show_ids)
            show_tree_xml(delta, to_file, self.show_ids)
        print >>to_file,  '</log>',

log_formatter_registry.register('xml', XMLLogFormatter,
                              'Detailed (not well formed) XML log format')



