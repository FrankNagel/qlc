# -*- coding: utf-8 -*-
"""
Corpus Reader for data of the project Quantitative Language Comparison.
"""

import os.path
import codecs

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
        self.dictdata = {}
        self.entries = {}
        self.annotations = {}
        self.dictdata_string_ids = {}

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

        # read dictdata table
        is_first_line = True
        file = codecs.open(os.path.join(datapath, "annotation.csv"), "r", "utf-8")
        for line in file:
            if is_first_line:
                is_first_line = False
                continue
            line = line.strip()
            data = line.split("\t")
            self.annotations[data.pop(0)] = data
            
        self.initDictdataStringIds()


    def initDictdataStringIds(self):
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
            self.dictdata_string_ids[dictdata_id] = "%s_%s_%s" % (bibtex_key, self.dictdata[dictdata_id][0], self.dictdata[dictdata_id][2])


    def dictdataStringIds(self):
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
        return self.dictdata_string_ids
    

    def dictdataStringIdForDictataId(self, dictdata_id):
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
        return self.dictdata_string_ids[dictdata_id]


    def headsWithTranslationsForDictdataId(self, param_dictdata_id = None):
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
                ret[entry_id]['dictdata_string_id'] = self.dictdata_string_ids[ self.entries[entry_id][4] ]
        
        return ret


    def headsWithTranslations(self):
        """
        Convinience method to return heads and translations for all dictionary parts
        of all books. See headsWithTranslationsForDictdataId() for a description
        """
        return self.headsWithTranslationsForDictdataId()
