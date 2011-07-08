# -*- coding: utf-8 -*-
"""
Corpus Reader for data of the project Quantitative Language Comparison.
"""

import os.path
import codecs

_book_table_columns = {
    'title': 0,
    'author': 1,
    'year': 2,
    'bibtex_key': 3,
    'columns': 4,
    'pages': 5,
    'origfilepath': 6,
    'type': 7,
    'is_ready': 8,
}

_wordlistentry_table_columns = {
    'fullentry': 0,
    'startpage': 1,
    'endpage': 2,
    'startcolumn': 3,
    'endcloumn': 4,
    'pos_on_page': 5,
    'concept_id': 6,
    'wordlistdata_id': 7,
    'has_manual_annotations': 8
}

_wordlistdata_table_columns = {
    'startpage': 0,
    'endpage': 1,
    'language_bookname': 2,
    'language_id': 3,
    'book_id': 4,
    'component_id': 5
}

_language_table_columns = {
    'name': 0,
    'langcode': 1,
    'description': 2,
    'url': 3
}

_wordlistconcept_table_columns = {
    'concept': 0
}

class CorpusReaderDict(object):
    """
    The corpus reader class for dictionary data. API was designed to allow
    easy access to the data of the dictionaries, all methodes return data
    in Python data structures. Think of it as DB-less queries that return
    Key-Value-Stores.
    """
    
    def __init__(self, datapath):
        """
        Constructor of CorpusReaderDict class.
        
        Args:
            - datapath (obligatory): the path to the dictionary data files (*.csv) in the
                file system.
        
        Returns:
            - nothing
        """
        
        self.datapath = datapath
        self.books = {}
        self.languages = {}
        self.dictdata = {}
        self.entries = {}
        self.annotations = {}
        self.__dictdata_string_ids = {}

        # read book table
        is_first_line = True
        file = codecs.open(os.path.join(datapath, "book.csv"), "r", "utf-8")
        for line in file:
            if is_first_line:
                is_first_line = False
                continue
            line = line.strip()
            data = line.split("\t")
            self.books[data.pop(0)] = data

        # read dictdata table
        is_first_line = True
        file = codecs.open(os.path.join(datapath, "dictdata.csv"), "r", "utf-8")
        for line in file:
            if is_first_line:
                is_first_line = False
                continue
            line = line.strip()
            data = line.split("\t")
            self.dictdata[data.pop(0)] = data
            
        # read entry table
        is_first_line = True
        file = codecs.open(os.path.join(datapath, "entry.csv"), "r", "utf-8")
        for line in file:
            if is_first_line:
                is_first_line = False
                continue
            line = line.strip()
            data = line.split("\t")
            self.entries[data.pop(0)] = data

        # read annotation table
        is_first_line = True
        file = codecs.open(os.path.join(datapath, "annotation.csv"), "r", "utf-8")
        for line in file:
            if is_first_line:
                is_first_line = False
                continue
            line = line.strip()
            data = line.split("\t")
            self.annotations[data.pop(0)] = data
            
        # read language table
        is_first_line = True
        file = codecs.open(os.path.join(datapath, "language.csv"), "r", "utf-8")
        for line in file:
            if is_first_line:
                is_first_line = False
                continue
            line = line.strip()
            data = line.split("\t")
            self.languages[data.pop(0)] = data

        self.init_dictdata_string_ids()


    def init_dictdata_string_ids(self):
        """
        Initializer for Dictdata identification strings. Dictdata are parts of books that
        contain dictionary data (vs. Nondictdata). The string IDs are equal to the
        ID within URLs of the QuantHistLing website, i.e. something like "thiesen1998_10_244".
        The general structure of the ID is "key_startpage_endpage". The strings are saved into
        a private dict, mapping from the numerical ID to the string ID, to allow an easy
        lookup. This method is called by the constructor of the class and should not be
        called by the user.
        
        Args:
            - nothing
            
        Returns:
            - nothing
        """
        for dictdata_id in self.dictdata:
            book_id = self.dictdata[dictdata_id][7]
            bibtex_key = self.books[book_id][3]
            self.__dictdata_string_ids[dictdata_id] = "%s_%s_%s" % (bibtex_key, self.dictdata[dictdata_id][0], self.dictdata[dictdata_id][2])

    @property
    def dictdata_string_ids(self):
        """
        Returns the dict of the mappings from numerical IDs to strings IDs for the
        Dictdata entries. Dictdata are parts of books that contain dictionary data
        (vs. Nondictdata). The string IDs are equal to the ID within URLs of the
        QuantHistLing website, i.e. something like "thiesen1998_10_244". The general
        structure of the ID is "key_startpage_endpage".
        
        Args:
            - nothing
            
        Returns:
            - The dict of numerical IDs to string IDs
        """
        return self.__dictdata_string_ids
    
    def dictdata_string_id_for_dictata_id(self, dictdata_id):
        """
        Return the string ID to a given numerical ID of a Dictdata entry.
        Dictdata are parts of books that contain dictionary data
        (vs. Nondictdata). The string IDs are equal to the ID within URLs of the
        QuantHistLing website, i.e. something like "thiesen1998_10_244". The general
        structure of the ID is "key_startpage_endpage".
        
        Args:
            - dictdata_id (obligatory): numerical ID of the Dictdata entry
        Returns:
            - String containing the string ID of the given Dictdata entry
        """
        return self.__dictdata_string_ids[dictdata_id]

    def dictdata_ids_for_bibtex_key(self, param_bibtex_key):
        """Return an array of dicionary parts IDs for a given book. The book
        is identified by the so-called bibtex key, which is the string for
        the book from the URL. For example: "thiesen1998".
        
        Args:
            - param_bibtex_key (obligatory): a string with the bibtex key.
        Returns:
            - An array containing all the dictdata IDs for the book.
        """
        ret = []
        for dictdata_id in self.dictdata:
            book_id = self.dictdata[dictdata_id][7]
            if self.books[book_id][3] == param_bibtex_key:
                ret.append(dictdata_id)
        return ret
        
    def heads_with_translations_for_dictdata_id(self, param_dictdata_id = None):
        """
        Returns a dictionary of all heads and translations for a given dictionary
        data part of a book. The keys of the dictionary are the numerical entry
        IDs. The values of the dictionaries are dictionaries with 4 keys: "heads",
        "translations", "dictdata_id", "dictdata_string_id". The values of
        "heads" and "translations" are arrays of strings, the "dictdata_id" and
        "dictdata_string_id" are strings. An example entry could look like:
        [ '12435': [
            "heads": [ "Hund", "Hunde" ],
            "translations": ["dog", "dogs", "hound", "hounds"],
            "dictdata_id": "7",
            "dictdata_string_id": "thiesen1998_12_125"
            ]
        ]
        
        Args:
            - param_dictdata_id: the numerical ID of the dictionary part of a book.
                If not given: returns heads and translations of all dictionary parts
                of all books.
        Returns:
            - A dicionary containing heads and translations for each entry, as
                described above.
        """
        head_annotations = {}
        translation_annotations = {}
        
        for annotation_id, annotation_data in self.annotations.items():
            entry_id = annotation_data[0]
            dictdata_id = self.entries[entry_id][4]

            if (param_dictdata_id == None) or (dictdata_id == param_dictdata_id):
                if annotation_data[4] == 'head':
                    if annotation_data[0] in head_annotations:
                        head_annotations[entry_id].append(annotation_data[5])
                    else:
                        head_annotations[entry_id] = [annotation_data[5]]
                        
                elif annotation_data[4] == 'translation':
                    if annotation_data[0] in translation_annotations:
                        translation_annotations[entry_id].append(annotation_data[5])
                    else:
                        translation_annotations[entry_id] = [annotation_data[5]]

        ret = {}
        for entry_id in head_annotations:
            # only add an entry if both head and translation have data
            if entry_id in translation_annotations:
                ret[entry_id] = {}
                ret[entry_id]['heads'] = head_annotations[entry_id]
                ret[entry_id]['translations'] = translation_annotations[entry_id]
                ret[entry_id]['dictdata_id'] = self.entries[entry_id][4]
                ret[entry_id]['dictdata_string_id'] = self.__dictdata_string_ids[ self.entries[entry_id][4] ]
        
        return ret


    def heads_with_translations(self):
        """
        Convinience method to return heads and translations for all dictionary parts
        of all books. See headsWithTranslationsForDictdataId() for a description
        """
        return self.heads_with_translations_for_dictdata_id()


    def phonology_for_dictdata_id(self, param_dictdata_id = None):
        """Returns a python dict for all phonology annotations of the given
        dictionary part of a book. The returned dict structure is equivalent to
        the structure of the method headsWithTranslationsForDictdataId():
        [ '12435': [
            "phonology": [ "hund", "hunde" ],
            "startpage": "120",
            "pos_on_page": "12"
            ]
        ]
        
        Args:
            - param_dictdata_id: the numerical ID of the dictionary part of a book.
                If not given: returns phonology of all dictionary parts
                of all books.
        Returns:
            - A dicionary containing phonology for each entry, as
                described above.
        """
        phonology_annotations = {}
        for annotation_id, annotation_data in self.annotations.items():
            entry_id = annotation_data[0]
            dictdata_id = self.entries[entry_id][4]

            if (param_dictdata_id == None) or (dictdata_id == param_dictdata_id):
                if annotation_data[4] == 'phonology':
                    if annotation_data[0] in phonology_annotations:
                        phonology_annotations[entry_id].append(annotation_data[5])
                    else:
                        phonology_annotations[entry_id] = [annotation_data[5]]
        
        ret = {}
        for entry_id in phonology_annotations:
            ret[entry_id] = {}
            ret[entry_id]['phonology'] = phonology_annotations[entry_id]
            #ret[entry_id]['dictdata_id'] = self.entries[entry_id][4]
            ret[entry_id]['startpage'] = self.entries[entry_id][5]
            ret[entry_id]['pos_on_page'] = self.entries[entry_id][9]
            #ret[entry_id]['dictdata_string_id'] = self.dictdata_string_ids[ self.entries[entry_id][4] ]
        
        return ret


class CorpusReaderWordlist(object):
    """
    The corpus reader class for wordlist data. API was designed to allow
    easy access to the data of the dictionaries, all methodes return data
    in Python data structures. Think of it as DB-less queries that return
    Key-Value-Stores.
    """
    
    def __init__(self, datapath):
        """
        Constructor of CorpusReaderWordlist class.
        
        Args:
            - datapath (obligatory): the path to the dictionary data files (*.csv) in the
                file system.
        
        Returns:
            - nothing
        """
        
        self.datapath = datapath
        self.books = {}
        self.languages = {}
        self.wordlistdata = {}
        self.wordlistentries = {}
        self.wordlistannotations = {}
        self.wordlistconcepts = {}
        self.wordlistdata_string_ids = {}

        # read book table
        is_first_line = True
        file = codecs.open(os.path.join(datapath, "book.csv"), "r", "utf-8")
        for line in file:
            if is_first_line:
                is_first_line = False
                continue
            line = line.strip()
            data = line.split("\t")
            self.books[data.pop(0)] = data

        # read worlistdata table
        is_first_line = True
        file = codecs.open(os.path.join(datapath, "wordlistdata.csv"), "r", "utf-8")
        for line in file:
            if is_first_line:
                is_first_line = False
                continue
            line = line.strip()
            data = line.split("\t")
            self.wordlistdata[data.pop(0)] = data

        # read wordlist entry table
        is_first_line = True
        file = codecs.open(os.path.join(datapath, "wordlistentry.csv"), "r", "utf-8")
        for line in file:
            if is_first_line:
                is_first_line = False
                continue
            line = line.strip()
            data = line.split("\t")
            self.wordlistentries[data.pop(0)] = data

        # read wordlist annotation table
        is_first_line = True
        file = codecs.open(os.path.join(datapath, "wordlistannotation.csv"), "r", "utf-8")
        for line in file:
            if is_first_line:
                is_first_line = False
                continue
            line = line.strip()
            data = line.split("\t")
            self.wordlistannotations[data.pop(0)] = data
            
        # read language table
        is_first_line = True
        file = codecs.open(os.path.join(datapath, "language.csv"), "r", "utf-8")
        for line in file:
            if is_first_line:
                is_first_line = False
                continue
            line = line.strip()
            data = line.split("\t")
            self.languages[data.pop(0)] = data

        # read concept table
        is_first_line = True
        file = codecs.open(os.path.join(datapath, "wordlistconcept.csv"), "r", "utf-8")
        for line in file:
            if is_first_line:
                is_first_line = False
                continue
            line = line.strip()
            data = line.split("\t")
            self.wordlistconcepts[data.pop(0)] = data

        self.init_wordlistdata_string_ids()

    def init_wordlistdata_string_ids(self):
        """
        Initializer for Worlistdata identification strings. Wordlistdata are parts of books that
        contain wordlist data (vs. Nondictdata and Dictdata). The string IDs are equal to the
        ID within URLs of the QuantHistLing website, i.e. something like "huber1992_10_392".
        The strings are saved into a private dict, mapping from the numerical ID to the
        string ID, to allow an easy lookup. This method is called by the constructor of
        the class and should not be called by the user.
        
        Args:
            - nothing
            
        Returns:
            - nothing
        """
        for wordlistdata_id in self.wordlistdata:
            book_id = self.wordlistdata[wordlistdata_id][_wordlistdata_table_columns['book_id']]
            bibtex_key = self.books[book_id][_book_table_columns['bibtex_key']]
            self.wordlistdata_string_ids[wordlistdata_id] = "%s_%s_%s" % (
                bibtex_key,
                self.wordlistdata[wordlistdata_id][_wordlistdata_table_columns['startpage']],
                self.wordlistdata[wordlistdata_id][_wordlistdata_table_columns['endpage']]
                )
    
    def wordlistdata_string_ids(self):
        """
        Returns the dict of the mappings from numerical IDs to strings IDs for the
        Wordlistdata entries. Wordlistdata are parts of books that contain wordlists
        (vs. Dictdata and Nondictdata). The string IDs are equal to the ID within URLs of the
        QuantHistLing website, i.e. something like "huber1992_10_244". The general
        structure of the ID is "key_startpage_endpage".
        
        Args:
            - nothing
            
        Returns:
            - The dict of numerical IDs to string IDs
        """
        return self.wordlistdata_string_ids
        
    def wordlist_ids_for_bibtex_key(self, param_bibtex_key):
        """Return an array of wordlist parts IDs for a given book. The book
        is identified by the so-called bibtex key, which is the string for
        the book from the URL. For example: "huber1992".
        
        Args:
            - param_bibtex_key (obligatory): a string with the bibtex key.
        Returns:
            - An iterator over all the wordlistdata IDs for the book.
        """
        ret = []
        for wordlistdata_id in self.wordlistdata:
            book_id = self.wordlistdata[wordlistdata_id][_wordlistdata_table_columns['book_id']]
            if self.books[book_id][_book_table_columns['bibtex_key']] == param_bibtex_key:
                yield wordlistdata_id

    def get_language_bookname_for_wordlist_data_id(self, wordlistdata_id):
        """Returns the language string that is used in the book for a given
        Wordlistdata ID.
        
        Args:
            - wordlistdata_id (obligatory): ID of the wordlistdata part of a book
        Returns:
            - A string of the language string in the book
        """
        return self.wordlistdata[wordlistdata_id][_wordlistdata_table_columns['language_bookname']]
        
    def counterparts_for_wordlistdata_id(self, param_wordlistdata_id = None):
        """Returns an iterator for all counterpart annotations of the given
        wordlist part of a book. The entries over which you can iterate are
        a python dict each, with additional information for the counterpart.
        The dict looks like this:
        {
            "counterpart": [ "hund", "hunde" ],
            "concept": "DOG",
            "language_bookname": "Deutsch",
            "language_code": "de",
            "bibtex_key": "huber1949"
        }
        The values of the counterpart lists are all counterparts that exist
        for an wordlist entry.
        
        Args:
            - param_wordlistdata_id: the numerical ID of the wordlist part of a
            book. If not given: returns counterparts of all wordlist parts
                of all books.
        Returns:
            - An iterator over dicts containing counterparts for each entry, as
                described above.
        """
        counterpart_annotations = {}
        for annotation_id, annotation_data in self.wordlistannotations.items():
            if len(annotation_data) < 6:
                continue

            entry_id = annotation_data[0]
            wordlistdata_id = self.wordlistentries[entry_id][_wordlistentry_table_columns['wordlistdata_id']]

            if (param_wordlistdata_id == None) or (wordlistdata_id == param_wordlistdata_id):
                if annotation_data[4] == 'counterpart':
                    if annotation_data[0] in counterpart_annotations:
                        counterpart_annotations[entry_id].append(annotation_data[5])
                    else:
                        counterpart_annotations[entry_id] = [annotation_data[5]]
        
        #ret = {}
        for entry_id in counterpart_annotations:
            #string_id = "%s_%s_%s" % (self.wordlistdata_string_ids[ self.entries[entry_id][4] ], '', '')
            wordlistdata_id = self.wordlistentries[entry_id][_wordlistentry_table_columns['wordlistdata_id']]
            language_bookname = self.wordlistdata[wordlistdata_id][_wordlistdata_table_columns['language_bookname']]
            language_id = self.wordlistdata[wordlistdata_id][_wordlistdata_table_columns['language_id']]
            if language_id != '':
                language_code = self.languages[language_id][_language_table_columns['langcode']]
            else:
                language_code = "n/a"
            concept = self.wordlistconcepts[self.wordlistentries[entry_id][_wordlistentry_table_columns['concept_id']]][_wordlistconcept_table_columns['concept']]
            ret = {}
            ret['counterpart'] = counterpart_annotations[entry_id]
            ret['language_code'] = language_code
            ret['language_bookname'] = language_bookname
            ret['concept'] = concept
            ret['bibtex_key'] = self.books [self.wordlistdata[wordlistdata_id][_wordlistdata_table_columns['book_id']]] [_book_table_columns['bibtex_key']]
            yield ret

