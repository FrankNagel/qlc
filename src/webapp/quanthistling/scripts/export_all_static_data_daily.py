import exportbookdata
import sys

def main(argv):

    if len(argv) < 2:
        print "call: export_all_static_data.py ini_file"
        exit(1)

    ini_file = argv[1]
    
    exportbookdata.main(["exportbookdata.py", ini_file])

if __name__ == "__main__":
    main(sys.argv)