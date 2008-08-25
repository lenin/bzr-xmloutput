# Copyright (C) 2008  Martin Albisetti <argentina@gmail.com>
# Copyright (C) 2008  Robert Collins
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
import os, sys
from service import redirect_output
from xml_errors import XMLError
from bzrlib.errors import EXIT_ERROR

try:
    from bzrlib.plugins.search import errors
    from bzrlib.plugins.search import index as _mod_index
    from bzrlib.plugins.search.index import FileTextHit, RevisionHit, PathHit
except ImportError:
    _mod_index = None
    
is_available = _mod_index is not None

@redirect_output
def search(branch_location, query_list, suggest=False):
    """Search using bzr-search plugin to find revisions matching the query.
    
    param branch_location: location of the branch to search in
    param query_list: string to search
    param suggest: Optional flag to request suggestions instead of results
    return: A dict containing a list for each type of hit, i.e:
        {'file_hits':[], 'path_hits':[], 'revid_hits':[]}
    """
    if _mod_index is None:
        return None # None indicates could-not-search
    try:
        index = _mod_index.open_index_url(branch_location)
    except errors.NoSearchIndex, e:
        sys.stderr.write(str(XMLError(e)))
        sys.stderr.flush();
        sys.stdout.flush();
        return (EXIT_ERROR, sys.stdout.getvalue(), sys.stderr.getvalue())
    query = query_list
    query = [(term,) for term in query]
    file_hits = []
    path_hits = []
    revid_hits = []
    index._branch.lock_read()

    try:
        if suggest:
            terms = index.suggest(query)
            terms = list(terms)
            terms.sort()
            return terms
        else:
            seen_count = 0
            for result in index.search(query):
                if isinstance(result, FileTextHit):
                    file_hits.append(get_file_text_hit_dict(result))
                if isinstance(result, PathHit):
                    path_hits.append(result.document_name())
                elif isinstance(result, RevisionHit):
                    revid_hits.append(get_revision_hit_dict(result))
                seen_count += 1
            if seen_count == 0:
                raise errors.NoMatch(query_list)
    finally:
        index._branch.unlock()
    return {'file_hits':file_hits, 'path_hits':path_hits,
        'revid_hits':revid_hits}


def get_file_text_hit_dict(file_text_hit):
    """Converts a TextHit into a dict conatining the revid and path"""
    path = file_text_hit.index.search((file_text_hit.text_key,)).next()
    revision_id = file_text_hit.text_key[1]
    return {'revid':revision_id, 'path':path.document_name()}
    

def get_revision_hit_dict(revision_hit):
    """Converts a RevisionHit into a dict conatining: revid, author, message, 
    timestamp, timezone and properties"""
    revision = revision_hit.repository.get_revision(
        revision_hit.revision_key[-1])
    return {'revid':revision.revision_id, 
        'author':revision.get_apparent_author(),
        'message':revision.message, 'timestamp':revision.timestamp,
        'timezone':revision.timezone, 'properties':revision.properties}
