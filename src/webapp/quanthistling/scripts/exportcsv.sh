QUANTHISTLINGPATH=/media/Daten/Projects/svn-googlecode/qlc/src/webapp/quanthistling
psql -c "copy (select * from entry) to STDOUT DELIMITER AS E'\t' CSV HEADER;" quanthistling > $QUANTHISTLINGPATH/tmp/csv/entry.csv
psql -c "copy (select * from annotation) to STDOUT DELIMITER AS E'\t' CSV HEADER;" quanthistling > $QUANTHISTLINGPATH/tmp/csv/annotation.csv
psql -c "copy (select * from dictdata) to STDOUT DELIMITER AS E'\t' CSV HEADER;" quanthistling > $QUANTHISTLINGPATH/tmp/csv/dictdata.csv
psql -c "copy (select * from nondictdata) to STDOUT DELIMITER AS E'\t' CSV HEADER;" quanthistling > $QUANTHISTLINGPATH/tmp/csv/nondictdata.csv
psql -c "copy (select * from book) to STDOUT DELIMITER AS E'\t' CSV HEADER;" quanthistling > $QUANTHISTLINGPATH/tmp/csv/book.csv
psql -c "copy (select * from language) to STDOUT DELIMITER AS E'\t' CSV HEADER;" quanthistling > $QUANTHISTLINGPATH/tmp/csv/language.csv
psql -c "copy (select * from component) to STDOUT DELIMITER AS E'\t' CSV HEADER;" quanthistling > $QUANTHISTLINGPATH/tmp/csv/component.csv
psql -c "copy (select * from corpusversion) to STDOUT DELIMITER AS E'\t' CSV HEADER;" quanthistling > $QUANTHISTLINGPATH/tmp/csv/corpusversion.csv
psql -c "copy (select * from wordlist_entry) to STDOUT DELIMITER AS E'\t' CSV HEADER;" quanthistling > $QUANTHISTLINGPATH/tmp/csv/wordlistentry.csv
psql -c "copy (select * from wordlist_annotation) to STDOUT DELIMITER AS E'\t' CSV HEADER;" quanthistling > $QUANTHISTLINGPATH/tmp/csv/wordlistannotation.csv
psql -c "copy (select * from wordlist_concept) to STDOUT DELIMITER AS E'\t' CSV HEADER;" quanthistling > $QUANTHISTLINGPATH/tmp/csv/wordlistconcept.csv
psql -c "copy (select * from wordlistdata) to STDOUT DELIMITER AS E'\t' CSV HEADER;" quanthistling > $QUANTHISTLINGPATH/tmp/csv/wordlistdata.csv
zip -uj $QUANTHISTLINGPATH/quanthistling/public/downloads/csv.zip $QUANTHISTLINGPATH/tmp/csv/*.csv