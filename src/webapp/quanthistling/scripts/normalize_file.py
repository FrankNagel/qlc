import sys
import codecs
import unicodedata
import importfunctions

def main(argv):
    if len(argv) < 3:
        print "call: updatelanguages.py in_file out_file"
        exit(1)

    in_file = argv[1]
    out_file = argv[2]

    in_file = codecs.open(in_file, "r", "utf-8")
    out_file = codecs.open(out_file, "w", "utf-8")
    
    for line in in_file:

        line = importfunctions.normalize_stroke(line)
        line = unicodedata.normalize("NFD", line)

        out_file.write(line)

    in_file.close()
    out_file.close()

if __name__ == "__main__":
    main(sys.argv)
