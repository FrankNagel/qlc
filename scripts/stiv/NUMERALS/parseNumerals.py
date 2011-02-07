#!/usr/bin/python3
# -*- coding: utf-8 -*-

# textutil -stdout -convert html INPUT_FILE_NAME.htm | grep '"p2"' > OUTPUT_FILE_NAME.html

import os
import re

def repairHtmlFiles():
    """ loops through the data_lgs directory where the old HTM files are and 
    uses Unix textutil to repair the HTML files and write them to output_data_lgs

    Note: breaks on filenames that contain an appostrophe or space in filename

    """
    dir = os.listdir("data_lgs/")
    for filename in dir:
        os.system("textutil -stdout -convert html data_lgs/"+filename+" | grep '"+'"p2"'+"' > output_data_lgs/"+filename+"l")


def extractChineseMetadata():
    # chinese string for "language:"
    #chinese_string_file = codecs.open("chinese_string", "r", "utf-8")
    #chinese_string = chinese_string_file.readline().strip()    
    pass


def testLength(list, n):
    if len(list) != n:
        print (list)
        raise Exception("length doesn't match")

def extractMetadata(filename, file):
    data = []
    data.append(filename)
 
    # method to test that the list is full of data
    testLength(data, 1)

    header = file.readline()
    while not header.__contains__("logue"):
        header += file.readline()
    
    header = header.strip()
    header = header.replace("\n", "")
    header = stripJunk(header)

    # match code
    lang_code_pattern = re.compile("(code=)(.*)(\">)")
    
    # look for Ethnologue link types
    if header.__contains__("[Refer to"):
        cols = header.split("[Refer to")
    elif header.__contains__("[Ref "):
        cols = header.split("[Ref")
    elif header.__contains__("[Ref"):
        cols = header.split("[Ref")
    elif header.__contains__("[Refer to<"):
        cols = header.split("[Refer to<")
    elif header.__contains__(" [Refer to"):
        cols = header.split(" [Refer to")

    # if no ethnologue links
    elif header.__contains__("[Not mentioned"):
        cols = header.split("[Not mentioned")
    elif not header.__contains__("http://www.ethnologue.com/show_language.asp?code="):
        cols = header.split("</p>")

    # deal first with language name and countries
    language = cols[0].strip()
    language = language.replace("</p>", "")

    # split out country data
    # first grab exceptions cases without countries
    if not language.__contains__(","):
        data.append(language)
        data.append("") # append an empty country

    # deal with countries
    elif language.__contains__(","):
        lang_country = language.split(",")
        # append language name to data
        data.append(lang_country[0])

        testLength(data, 2)

        # deal with multiple countries
        countries = ""
        for i in range(1, len(lang_country)):
            lang_country[i] = lang_country[i].strip()
            lang_country[i] = lang_country[i].strip("")
            # deal with Kurmanji.html case
            countries += lang_country[i]+","
        countries = countries.rstrip(",")

        if not countries == "":
            data.append(countries)
        else:
            data.append("")
    
    # check that all "countries" are in
    testLength(data, 3)
            
    # next deal with language code mess
    code_string = cols[1].strip()
    code_match = lang_code_pattern.search(code_string)
    if code_match != None:
        code_match_str = code_match.group(2)
        code_part = code_match_str.partition('"')
        code = code_part[0]
        # deal with cases where *a* code is provided, but apparently not the right one
        if header.__contains__("Not mention"):
            data.append("NM-"+code)
        else:
            data.append(code)

    testLength(data, 4)
    #print (data)
    return data

def stripJunk(line):
    """ function to strip different human/html crap from the string
    """
    line = line.replace('<span class="s1">ː</span> ', "")
    line = line.replace("ː ", "")
    line = line.replace('<span class="s1"></span>', "")
    line = line.replace("ː<b> </b>", "")
    line = line.replace('<span class="s1">', "")
    line = line.replace('</span>', "")
    line = line.replace("<b>", "")
    line = line.replace("</b>", "")
    line = line.replace('<span class="s2">', "")
    line = line.replace(": ", "")
    line = line.replace(" ,", ",")
    line = line.replace("( ", "(")
    line = line.replace(" )", ")")
    line = line.replace("<i>", "")
    line = line.replace("</i>", "")
    line = line.replace('<span class="s1">ː</span>', "ː")
    line = line.replace('<p class="p2">', "")
    line = line.replace('Language name and location', "")
    line = line.replace(" ", "")
    line = line.strip()

    return line




def parseFileContents(file, filename):
    for line in file:
        line = line.strip()

        # regex the language code from the ethnologue string
        lang_code_match = lang_code_pattern.search(line)
        if lang_code_match != None:
            lang_code = lang_code_match.group(2).strip()    

        # regex the language name - handles 1919 cases
        #        lang_name_match = lang_name_pattern.search(line)
        #        if lang_name_match != None:
        #            lang_name = lang_name_match.group(2).strip()

        # match with normal location
        lang_name_match2 = lang_name_pattern2.search(line)
        if lang_name_match2 != None:
            lang_name = lang_name_match2.group(2).strip()

        # match with the <i>'s in location
        lang_name_match3 = lang_name_pattern3.search(line)
        if lang_name_match3 != None:
            lang_name = lang_name_match3.group(2).strip()

        # match "Language name and locatio<span class="s1">nː"
        lang_name_match4 = lang_name_pattern4.search(line)
        if lang_name_match4 != None:
            lang_name = lang_name_match4.group(2).strip()

    


def parseNumberEthnologueStrings(file, filename):
    count = 0
    for line in file:
        line = line.strip()
        if line.__contains__("http://www.ethnologue.com/show_language.asp?code="):
            count += 1
    if count == 1:
        print (filename)


def parseNumerals(filename, file):
    # loop throgh all lines in the file searching for numeral match
    numeral_pattern = re.compile('(<p class="p2">)(\d+)(\.)(.+)(</p>)')
    note_pattern = re.compile("(\(\s*\d+.*\))")
    # Zuni.html 1000  tapnimte miːɬ  ( 'miːɬ'&lt; Spanish )
    from_note_pattern = re.compile("(\()(.*&lt;.*)(\))")
    note_parens_pattern = re.compile("((.*)(\()(.*)(\)))")
    two_less_than_ten_pattern = re.compile("(\(\s*)(.*)(\s*\))")

    list = []
    count = 0
    # loop through lines in the file
    for line in file:
        line = line.strip()

        # short cut rest of file
        temp_line = line.replace('<p class="p2">', "")
        if temp_line.startswith("Linguist") or temp_line.startswith("Linguists") or temp_line.startswith("Note that"):
            # print ("returning")
            return

        numeral = ""
        linguistic_form = ""
        notes = ""
        from_notes = ""
 
        # match a numeral line in the file
        match = numeral_pattern.search(line)
        if match != None:
            count += 1
            numeral = match.group(2).strip() # get numeral: (\d+)
            linguistic_form = match.group(4).strip() # get form: (.+)

            # special cases like tone - remove the <sup>s
            # <span class="s4"><sup>1 </sup></span>ɬip<span class="s4"><sup>7</sup></span>
            linguistic_form = linguistic_form.replace('<span class="s7">', "")
            linguistic_form = linguistic_form.replace('<span class="s6">', "")
            linguistic_form = linguistic_form.replace('<span class="s5">', "")
            linguistic_form = linguistic_form.replace('<span class="s4">', "")
            linguistic_form = linguistic_form.replace('<span class="s3">', "")
            linguistic_form = linguistic_form.replace('<span class="s2">', "")
            linguistic_form = linguistic_form.replace('<span class="s1">', "")
            linguistic_form = linguistic_form.replace("</span>", "")
            linguistic_form = linguistic_form.replace("</sup>", "")
            linguistic_form = linguistic_form.replace('<sup>', "")
            linguistic_form = linguistic_form.replace('<b>', "")
            linguistic_form = linguistic_form.replace('</b>', "")
            linguistic_form = linguistic_form.replace('<i>', "")
            linguistic_form = linguistic_form.replace('</i>', "")

            # special cases - notes
            # match lines with notes with the pattern form: ( \d+.* )
            if note_pattern.search(linguistic_form) != None:
                note_match = note_pattern.search(linguistic_form)
                linguistic_form_wo_notes = ""
                if note_match != None:
                    notes = note_match.group()
                    linguistic_form_wo_notes = linguistic_form.replace(notes, "")
                    print (filename, line)
                    print (filename, numeral, "\t", linguistic_form_wo_notes, "##", notes)
                    print ()
                else:
                    print (filename, line)
                    print (filename, numeral, "\t", linguistic_form, "\t##", "no notes")
                    print ()

            # Zuni.html 1000  tapnimte miːɬ  ( 'miːɬ'&lt; Spanish )
            # from_note_pattern = re.compile("(\()(.*&lt;.*)(\))")
            elif from_note_pattern.search(line) != None:
                from_note_match = from_note_pattern.search(linguistic_form)
                linguistic_form_wo_notes = ""
                if from_note_match != None:
                    from_notes = from_note_match.group()
                    linguistic_form_wo_notes = linguistic_form.replace(from_notes, "")
                    from_notes = from_notes.replace("&lt;", "<")
                    print (filename, line)
                    print ("&lt;", filename, numeral, "\t", linguistic_form_wo_notes, "##", from_notes)
                    print ()

            # two_less_than_ten_pattern = re.compile("(\(\s*)(\w+)(\s*\))")
            elif two_less_than_ten_pattern.search(line) != None:
                print ("match")
                two_less_than_ten_match = two_less_than_ten_pattern.search(linguistic_form)
                linguistic_form_wo_notes = ""
                if two_less_than_ten_match != None:
                    two_less_than_ten = two_less_than_ten_match.group()
                    linguistic_form_wo_notes = linguistic_form.replace(two_less_than_ten, "")
                    print (filename, line)
                    print ("tlt", filename, numeral, "\t", linguistic_form_wo_notes, "##", two_less_than_ten)
                    print ()
                    
            

            # match split forms with "/"
            # print each occurence 
            elif linguistic_form.__contains__("/") and linguistic_form.__contains__("&lt;"):
                linguistic_form = linguistic_form.replace("&lt;", "<")
                partition = linguistic_form.partition("/")
                if partition[0] == "":
                    raise Exception("uh oh")
                print (filename, line)
                print (filename, numeral, "\t", partition[0], "##", linguistic_form)
                print ()

            elif linguistic_form.__contains__("/"):
                partition = linguistic_form.partition("/")
                # special case of missing first form: Yuchi.html / ʔyuštʼæ̜ʔæ̜nǫwæ̜
                if partition[0] == "":
                    print (filename, line)
                    print (filename, numeral, "\t", partition[2], "##", linguistic_form)                    
                    print ()
                else:
                    print (filename, line)
                    print (filename, numeral, "\t", partition[0], "##", linguistic_form)                    
                    print ()
#                print (filename, "match /:", linguistic_form.partition("/"))

            # match the "<"
            elif linguistic_form.__contains__("&lt;"):
                partition = linguistic_form.partition("&lt;")
                if partition[0] == "":
                    # special no data case for Paumari.html "< Portuguese"
                    if partition[2].strip() == "Portuguese":
                        continue
                    print (line)
                    raise Exception("uh oh")
                print (filename, line)
                print (filename, numeral, "\t", partition[0], "##", linguistic_form)
                print ()

            # final case - no exceptions
            else:
                print (filename, line)
                print (filename, numeral, "\t", linguistic_form, "##", "no notes")
                print ()

#            print ("og:", filename, numeral, "\t", linguistic_form)

            # match line with: * 
            #if linguistic_form.endswith("*"):
            #    print (filename, numeral, "\t", linguistic_form)

            # match line with: &lt;
            #if linguistic_form.__contains__("&lt;"):
                #print (filename, "\t", linguistic_form)


if __name__=="__main__":
    # batch repair files
    #repairHtmlFiles()

    # test dir with some files
    #dir = os.listdir("test")
    
    # path to all output files
    dir = "output_data_lgs/"

    # full dir files
    dir_list = os.listdir("output_data_lgs")

    # list of files that have 1 ethnologue link
    # first past - 2635 of 2965 files
    ethnologue_1_files = open("2635", "r")

    # test files
    test_dir_list = os.listdir("test")
    test_files = open

    count = 0
    metadata_hash = {}
    #for filename in dir_list:
    #for filename in ethnologue_1_files:
    # parse out metadata
    for filename in test_dir_list:
        count += 1
        filename = filename.strip()

        # extract metadata from first lines of file
        file = open(dir+filename, "r", encoding="utf-8")        
        metadata = extractMetadata(filename, file)

        if not metadata[0] in metadata_hash:
            metadata_hash[metadata[0]] = metadata
        else:
            raise Exception("duplicates in your metadata hash")
        file.close()


    # parse out numerals
    #for filename in test_dir_list:
    for filename in ethnologue_1_files:
        filename = filename.strip()
        file = open(dir+filename, "rt", encoding="utf-8")
        parseNumerals(filename, file)
        file.close()


