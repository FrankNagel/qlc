CREATE INDEX book_bibtexkey on book(bibtex_key);

CREATE INDEX nondictdata_bookid on nondictdata(book_id);

CREATE INDEX dictdata_bookid on dictdata(book_id);

CREATE INDEX wordlistdata_bookid on wordlistdata(book_id);
CREATE INDEX wordlistdata_languagebooknameid on wordlistdata(language_bookname_id);

CREATE INDEX annotation_entryid on annotation(entry_id);
CREATE INDEX annotation_value on annotation(value);

CREATE INDEX entry_issubsentryofentryid on entry(is_subentry_of_entry_id);
CREATE INDEX entry_issubsentry on entry(is_subentry);
CREATE INDEX entry_bookid on entry(book_id);
CREATE INDEX entry_startpage on entry(startpage);
CREATE INDEX entry_endpage on entry(endpage);
CREATE INDEX entry_posonpage on entry(pos_on_page);
CREATE INDEX entry_dictdataid on entry(dictdata_id);

CREATE INDEX wordlistentry_wordlistdataid on wordlist_entry(wordlistdata_id);
CREATE INDEX wordlistentry_startpage on wordlist_entry(startpage);
CREATE INDEX wordlistentry_endpage on wordlist_entry(endpage);
CREATE INDEX wordlistentry_posonpage on wordlist_entry(pos_on_page);

CREATE INDEX languagebookname_name on language_bookname(name);