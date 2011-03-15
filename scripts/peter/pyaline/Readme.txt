INTRODUCTION
------------
The PyAline script expects the data to be in a CSV table format. Each language
has a row in this table. The first column is the language name, than several
columns of unknown content, then the 100 strings for the concepts in this
language (if there are two strings for a concept they are separated by a pipe
symbol "|"). The comparison script supports two kinds of (phonetic) notations,
one is ALINE notation format, the other is the ASJP format. The default is the
ALINE format, if you use ASJP you have to give a parameter "-a". The other
paramter is the CSV file, i.e. "-f filename.csv".

Right now there are three scripts to handle the data from the ASJP project:

1) An extraction script (in Perl) that writes the CSV table suitable for
PyAline. It takes the data file downloaded from the ASJP website as input
("listss13.txt").
2) An adapted version of PyAline to write a distance matrix.
3) R code to display a tree derived from the distance matrix.

EXTRACTING THE DATA
-------------------
To extract the data from the file "listss13.txt" there is a Perl script that
writes a csv table, one row for each language. The first three columns are
reserved for the language and family names (there are two kinds of family
notation in the ASJP file). The phonetic strings start from column 4. To extract
the data to a file "salish.csv", just call the script like this:

$ perl generate_pyaline_format.pl listss13.txt > salish.csv

The script currently exports only the languages from the Salish family. Modify
the script to geht other families or to extract all data.

PYALINE AND DISTANCE MATRIX
---------------------------
To write a distance matrix to the file "salish_matrix.xt" call the script
"compare_languages.py" like this:

python compare_languages.py -a -f salish.csv > salish_matrix.txt

Option "-a" is given here as we use the ASJP notation. The script writes
progress to STDERR and the matrix to STDOUT. I made two modifications to the
original script:

1) I prefer TAB as seperator over commas, so my Perl script writes the data
TAB-seperated. I had to change the CSV loader within the Python script to
split at TABs.
2) The data starts at column 4, so I had to change the script to expect the
data there. In the original version the data starts in other columns.

To allow IPA strings in the data file should be as easy (or difficult) as adding
an IPAString class to pyaline.py. The string classes in pyaline.py create a
feature vector for each phonetic symbol, if I understood correctly.

A TREE IN R
-----------
This is just a basic example how to print a NJ tree for the distance matrix. I
am not too familiar with R, so the code is quit ugly... (I don't know how to
set the row and column names from the distance matrix file, for example).
Please correct the code where necessary. There are also other visualization
approaches for distance matrices, please add code for this, if you know how to
do this.

This code plots a NJ tree for the matrix in "salish_matrix.txt":

> M <- read.table("salish_matrix.txt", header=T)
> rownames(M) <- colnames(M)
> M2 <- data.matrix(M, rownames.force=T)
> library(ape)
> tr <- nj(M2)
> plot(tr)

FIRST APPROACH TO ZIP
---------------------
There is another script here "compare_languages_zip.py", that prints a distance
matrix by comparing zipped data. It uses gzip and the compression ratio of
files. It writes three files first:

1) All the 100 strings for one languages, twice, in one file.
2) All the 100 strings for a second languages, twice, in one file.
3) All the 100 strings for the first and the second language in one file.

So each file contains 200 strings in the end. The idea is to compare the
compression of 1 and 2 againt 3. 1 and 2 should compress better, because they
contain all string twice. The more similar the two languages are, the better
the compression should be in 3, compared to 1 and 2.

This is just a first approach and gives some starting point how to use ZIP
utilities to get a distance matrix. The original ZIP programm did not compress
those files on Linux, ZIP might consider the files too small to compress. That
is why I used GZIP, which compressed also small files without problems.