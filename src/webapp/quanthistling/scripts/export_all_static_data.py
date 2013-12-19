import exportgraf
import exportbookdata
import exportcsv_books
import exportcsv_wordlists
import create_datapackages
import exporttables
import sys

def main(argv):

    if len(argv) < 2:
        print "call: export_all_static_data.py ini_file"
        exit(1)

    ini_file = argv[1]
    
    exporttables.main(["exporttables.py", ini_file])
    exportcsv_books.main(["exportcsv_books.py", ini_file])
    exportcsv_wordlists.main(["exportcsv_wordlists.py", ini_file])
    exportgraf.main(["exportgraf.py", ini_file])
    exportbookdata.main(["exportbookdata.py", ini_file])
    create_datapackages.main(["create_datapackages.py", ini_file])

if __name__ == "__main__":
    main(sys.argv)