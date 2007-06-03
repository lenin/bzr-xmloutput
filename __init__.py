#!/usr/bin/env python2.4

# @author Guillermo Gonzalez
# @version 0.1
"""
This plugin provides xml output for three commands (status, log, annotate)
adding a --xml option to each

(most of this is code was modified from bzrlib.cmd_status, 
bzrlib.status, bzrlib.delta.TreeDelta.show and bzrlib.log.LongLogFormatter)
"""
from bzrlib.commands import display_command, register_command
from bzrlib import builtins
from bzrlib.log import LogFormatter, log_formatter_registry, LogRevision
from bzrlib.option import Option
from bzrlib.workingtree import WorkingTree
import sys

class cmd_status(builtins.cmd_status):
    builtins.cmd_status.takes_options.append(Option('xml', help='show status in xml format'))
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

class cmd_annotate(builtins.cmd_annotate):
    builtins.cmd_annotate.takes_options.append(Option('xml', help='show annotations in xml format'))
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
                        file_id=file_id, to_file=sys.stdout,
                        show_ids=show_ids, wt_root_path=wt_root_path, file_path=relpath)
            finally:
                branch.unlock()
        else:
            annotate_class.run(self, filename=filename, all=all, long=long, revision=revision,
            show_ids=show_ids)

class cmd_log(builtins.cmd_log):
    __doc__ = builtins.cmd_log.__doc__
    
    @display_command
    def run(self, location=None, timezone='original',
            verbose=False,
            show_ids=False,
            forward=False,
            revision=None,
            log_format=None,
            message=None,
            limit=None):

        if log_format is XMLLogFormatter:
            print >>sys.stdout, '<?xml version="1.0"?>'
            print >>sys.stdout, '<logs>'
            log_class.run(self, location=location, timezone=timezone, 
                    verbose=verbose, show_ids=show_ids, forward=forward, 
                    revision=revision, log_format=log_format, message=message, limit=limit)
            print >>sys.stdout, '</logs>'
        else:
            log_class.run(self, location=location, timezone=timezone, 
                    verbose=verbose, show_ids=show_ids, forward=forward, 
                    revision=revision, log_format=log_format, message=message, limit=limit)

class XMLLogFormatter(LogFormatter):
    """ add a --xml format to 'bzr log'"""
    def __init__(self, to_file, show_ids=False, show_timezone='original'):
        super(XMLLogFormatter, self).__init__(to_file=to_file, 
                               show_ids=show_ids, show_timezone=show_timezone)

    def show(self, revno, rev, delta, tags=None):
        lr = LogRevision(rev, revno, 0, delta, tags)
        return self.log_revision(lr)

    def show_merge_revno(self, rev, merge_depth, revno):
        """a call to self._show_helper, XML don't care about formatting """
        lr = LogRevision(rev, merge_depth=merge_depth, revno=revno)
        return self.log_revision(lr)

    def log_revision(self, revision):
        """Log a revision, either merged or not."""
        from xml.sax import saxutils
        from bzrlib.osutils import format_date
        indent = '    '*revision.merge_depth
        to_file = self.to_file
        print >>to_file,  '<log>',
        if revision.revno is not None:
            print >>to_file,  '<revno>%s</revno>' % revision.revno,
        if revision.tags:
            print >>to_file,  '<tags>'
            for tag in revision.tags:
                print >>to_file, indent+'<tag>%s</tag>' % tag
            print >>to_file,  '</tags>'
        if self.show_ids:
            print >>to_file,  '<revision-id>%s</revision_id>' % revision.rev.revision_id,
            if len(revision.rev.parent_ids) > 0:
                print >>to_file, '<parents>',
            for parent_id in revision.rev.parent_ids:
                print >>to_file, '<parent>%s</parent>' % parent_id,
            if len(revision.rev.parent_ids) > 0:
                print >>to_file, '</parents>',

        print >>to_file,  '<committer>%s</committer>' % \
                        saxutils.escape(revision.rev.committer),

        try:
            print >>to_file, '<branch-nick>%s</branch-nick>' % \
                saxutils.escape(revision.rev.properties['branch-nick']),
        except KeyError:
            pass
        date_str = format_date(revision.rev.timestamp,
                               revision.rev.timezone or 0,
                               self.show_timezone)
        print >>to_file,  '<timestamp>%s</timestamp>' % date_str,

        print >>to_file,  '<message>',
        if not revision.rev.message:
            print >>to_file,  indent+'(no message)'
        else:
            message = revision.rev.message.rstrip('\r\n')
            for l in message.split('\n'):
                print >>to_file, saxutils.escape(l)
            #print >>to_file,  saxutils.escape(rev.message),
        print >>to_file,  '</message>',
        if revision.delta is not None:
            from statusxml import show_tree_xml
            show_tree_xml(delta, to_file, self.show_ids)
        print >>to_file,  '</log>',

status_class = register_command(cmd_status, decorate=True)
annotate_class = register_command(cmd_annotate, decorate=True)
log_class = register_command(cmd_log, decorate=True)
log_formatter_registry.register('xml', XMLLogFormatter,
                              'Detailed (not well formed?) XML log format')



