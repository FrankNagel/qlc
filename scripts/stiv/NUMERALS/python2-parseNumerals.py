#!/usr/bin/python3
# -*- coding: utf-8 -*-

# textutil -stdout -convert html INPUT_FILE_NAME.htm | grep '"p2"' > OUTPUT_FILE_NAME.html

import os
import re
import codecs

def repairHtmlFiles():
    """ loops through the data_lgs directory where the old HTM files are and 
    use Unix textutil to repair the HTML files and write them to output_data_lgs

    Note: breaks on filenames that contain an appostrophe or space in filename

    """
    dir = os.listdir("data_lgs/")
    for filename in dir:
        os.system("textutil -stdout -convert html data_lgs/"+filename+" | grep '"+'"p2"'+"' > output_data_lgs/"+filename+"l")


def parseFileContents(file, filename):
    # chinese string for "language:"
    #chinese_string_file = codecs.open("chinese_string", "r", "utf-8")
    #chinese_string = chinese_string_file.readline().strip()

    # not going to work - first two lines not consistently header info
#    header_english = file.readline()
#    header_chinese = file.readline()

    lang_name_pattern = re.compile("(<\/span>)(.*)(\[)")
    lang_name_pattern2 = re.compile("(Language name and location)(.*)(\[)")
    lang_code_pattern = re.compile("(http:\/\/www.ethnologue.com\/show_language.asp\?code=)(.*)(\"><span)")

    lang_name = ""
    lang_code = ""

    # main loop
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

        lang_name_match2 = lang_name_pattern2.search(line)
        if lang_name_match2 != None:
            lang_name = lang_name_match2.group(2).strip()



    if lang_name != "":
        print lang_name.encode("utf-8")
#    print filename, "\t", lang_code, "\t", lang_name.encode("utf-8")

    """
        if line.__contains__(chinese_string):
            print file, line.encode("utf-8")

        if line.__contains__("Not") and line.__contains__("Ethnologue"):
            lang_code = "xxx"

        if line.__contains__("Language name and location"):
            print line.encode("utf-8")

        if line.__contains__("[Not yet reported in Ethnologue]"):
            lang_code = "xxx"

        # [Not reported on the Ethnologue]
        if line.__contains__("[Not reported on the Ethnologue]"):
            lang_code = "yyy"

        # Not listed in
        if line.__contains__("Not listed in"):
            lang_code = "yyy"



        t = (lang_code, file)
        """

#    if t[0] == "":
#        print t

# <p class="p2">30. t'q'ɑ.it:' ( 20 + 10 )</p>

#    print lang_name, "\t", lang_code

# </span> Akan, Ghana [Refer to<a href="http://www.ethnologue.com/show_language.asp?code=aka"><span class="s2"> </span><span class="s3">Ethnologue</span></a>]</p>

def parseNumberEthnologueStrings(file, filename):
    count = 0
    for line in file:
        line = line.strip()
        if line.__contains__("http://www.ethnologue.com/show_language.asp?code="):
            count += 1
    if count == 1:
        print filename


if __name__=="__main__":
    # batch repair files
    #repairHtmlFiles()

    # test dir with some files
    #dir = os.listdir("test")
    
    # path to output files
    dir = "output_data_lgs/"

    # full dir files
    dir_list = os.listdir("output_data_lgs")

    # list of files that have 1 ethnologue link
    ethnologue_1_files = open("2635", "r")

    #for filename in dir_list:
    for filename in ethnologue_1_files:
        filename = filename.strip()
        file = codecs.open(dir+filename, "r", "utf-8")
        parseFileContents(file, filename)
        file.close()
