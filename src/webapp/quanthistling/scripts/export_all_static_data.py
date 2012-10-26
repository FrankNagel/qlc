#import exportheads
#import exportheads_with_translation
#import exportpos
#import exporttranslations
#import exportexamples
import exportxmldata2
import exportbookdata
import sys

def main(argv):

    if len(argv) < 2:
        print "call: export_all_static_data.py ini_file"
        exit(1)

    ini_file = argv[1]
    
    exportbookdata.main(["exportgraf.py", ini_file])
    exportbookdata.main(["exportbookdata.py", ini_file])

if __name__ == "__main__":
    main(sys.argv)