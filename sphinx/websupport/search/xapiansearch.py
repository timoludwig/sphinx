# -*- coding: utf-8 -*-
"""
    sphinx.websupport.search.xapian
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Xapian search adapter.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from os import path

import xapian

from sphinx.util.osutil import ensuredir
from sphinx.websupport.search import BaseSearch

class XapianSearch(BaseSearch):
    # Adapted from the GSOC 2009 webapp project.

    # Xapian metadata constants
    DOC_PATH = 0
    DOC_TITLE = 1

    def __init__(self, db_path):
        self.db_path = db_path

    def create_index(self):
        ensuredir(self.db_path)
        self.database = xapian.WritableDatabase(self.db_path, 
                                                xapian.DB_CREATE_OR_OPEN)
        self.indexer = xapian.TermGenerator()
        stemmer = xapian.Stem("english")
        self.indexer.set_stemmer(stemmer)
       
    def add_document(self, path, title, text):
        self.database.begin_transaction()
        doc = xapian.Document()
        doc.set_data(text)
        doc.add_value(self.DOC_PATH, path)
        doc.add_value(self.DOC_TITLE, title)
        self.indexer.set_document(doc)
        self.indexer.index_text(text)
        for word in text.split():
            doc.add_posting(word, 1)
        self.database.add_document(doc)
        self.database.commit_transaction()

    def prune(self, keep):
        pass

    def handle_query(self, q):
        database = xapian.Database(self.db_path)
        enquire = xapian.Enquire(database)
        qp = xapian.QueryParser()
        stemmer = xapian.Stem("english")
        qp.set_stemmer(stemmer)
        qp.set_database(database)
        qp.set_stemming_strategy(xapian.QueryParser.STEM_SOME)
        query = qp.parse_query(q)

        # Find the top 100 results for the query.
        enquire.set_query(query)
        matches = enquire.get_mset(0, 100)

        results_found = matches.get_matches_estimated()
        results_displayed = matches.size()

        results = []

        for m in matches:
            context = self.extract_context(m.document.get_data(), q)
            results.append((m.document.get_value(self.DOC_PATH),
                            m.document.get_value(self.DOC_TITLE),
                            ''.join(context) ))

        return results, results_found, results_displayed
        
