#!/usr/bin/python3.1
"""
#!/Library/Frameworks/Python.framework/Versions/3.1/bin/python3.1
#!/usr/bin/python
"""

import sys

def printProb():
#    print (total)
#    if total > 0:
#        raise Exception ("All counts for prev are 0.\n")
    prob = yes * 1.0 / total
    print (str(prev)+"\t"+str(prob))

prev = ""
total = 0
yes = 0

with open(sys.argv[1], "rt", encoding="utf-8") as file:
    for line in file:
        line = line.replace('"', "")
        columns = line.split()
        (current, is_diphthong, count) = columns
        if current != prev:
            # Hit the next current, so print the prob for the previous one.
            if prev != "":
                printProb()
            prev = current
            total = 0
            yes = 0

        total += int(count)
        if is_diphthong == "yes":
            yes += int(count)
        elif is_diphthong != "no":
            raise "Second column should be 'yes' or 'no': "+line
#        print (columns)


# Reached the end, so print the prob for the last current (which is prev).
printProb()


