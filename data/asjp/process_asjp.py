#!/usr/bin/env python
import sys, re, ethnologue_tree

class ASJPTextIterator(object):

    def __init__(self, file):
        self.file = file
        self.name_regex = re.compile('^([^{]*)\{([^}]*?)(\|([^}]*))?\}')
        self.lexeme_regex = re.compile('^(\d+)\.?\s+\S+\s+(.*?)\s*(//.*?)?$')
        self.first_data_line_regex = re.compile('GWI')

    def process_language_name(self, line):
        match = self.name_regex.search(line.strip())
        return (match.group(1), match.group(2), match.group(4) if match.group(4) else '')

    def process_lexeme(self, line):
        match = self.lexeme_regex.search(line)
        if match:
            return int(match.group(1)), match.group(2)
        else:
            return False

    def process_details(self, line):
        results = {}
        results['random_number'] = line[1]
        results['lat'] = line[3:10].strip()
        results['lon'] = line[11:18].strip()
        results['nsp'] = line[18:30].strip()
        results['wals'] = line[33:36].strip()
        results['iso'] = line[39:42].strip()
        return results

    def __iter__(self):
        result_dict = None
        last_line_top = False
        go = False
        for line in self.file:
            if not go and self.first_data_line_regex.match(line):
                go = True
            if not go:
                continue
            if '{' in line:
                if result_dict is not None:
                    yield result_dict
                (name,family,breakdown) = self.process_language_name(line)
                result_dict = {'name': name.replace('(', '-').replace(')','-'), 'family': family, 'breakdown': breakdown, 'words': {}, 'name_line': line.strip().replace('(', '-').replace(')','-'), 'lines': [], 'random_number': '', 'lat': '', 'lon': '', 'nsp': '', 'iso': '', 'wals': '', 'details_line': ''}
                last_line_top = True
            else:
                if last_line_top:
                    result_dict['details_line'] = line
                    result_dict.update(self.process_details(line))
                    last_line_top = False
                elif line.strip() != "":
                    lexeme_result = self.process_lexeme(line.strip())
                    result_dict['lines'].append(line.strip())
                    result_dict['words'][lexeme_result[0]] = lexeme_result[1]
        yield result_dict


class ProcessASJPTextFiles(object):
    
    def __init__(self, input=None, output_template=None, keys=None, filter=None, output_file_prefix='output', aline=None, asjp=None, newick=None, find_ethnologue_only = False, verbose_output=False):
        if input is None:
            self.input = sys.stdin
        else:
            self.input = input

            
        if output_template is None:
            self.output_template = "%(name)s\t%(wals)s\t%(iso)s\t%(family)s\t%(breakdown)s\t%(lat)s\t%(lon)s\t%(nsp)s\t"
        else:
            self.output_template = output_template
        self.filter = filter
        self.keys = keys
        self.aline = aline
        self.asjp = asjp
        self.newick = newick
        if self.aline:
            self.aline_output = open("%s_aline.txt" % (output_file_prefix, ), "w")
        if self.asjp:
            self.asjp_output = open("%s_asjp.txt" % (output_file_prefix, ), "w")
            # find preamble in file
            for line in self.input:
                if not re.match("GWI", line):
                    print >>self.asjp_output, line.rstrip("\n")
                else:
                    break
            self.input.seek(0)
            #print >>self.asjp_output, _asjp_preamble, #print the preamble, no extra return
        if self.newick:
            self.newick_output = open("%s_newick.txt" % (output_file_prefix, ), "w")
        self.find_ethnologue_only = find_ethnologue_only
        self.verbose_output = verbose_output
    
    def meaning_value_pairs(self, word_dict):
        if self.keys is not None:
            keys = self.keys
        else:
            keys = range(1, 100)
        values = []
        for key in keys:
            if word_dict.has_key(key) and word_dict[key] != 'XXX':
                values.append(word_dict[key].strip().replace(',','|').replace(' ',''))
            else:
                values.append('')
            
        return '\t'.join(values)
            
    
    def label_finder(self, name, label):
        current = result = {}
        z = ['top']
        y = label.split('|')
        if len(y) > 1:
            z.extend(y)
        for node in z:
            current[node] = {}
            current = current[node]
        current[name] = 1
        return result
    
    def process(self):
        i = 1
        ethnologue_trees_array = []
        newick_labels_array = []
        e = ethnologue_tree.Ethnologue()
        for record in ASJPTextIterator(self.input):
            if self.filter != None and self.filter(record) == False:
                continue
            if self.verbose_output:
                print "Name: %s" % (record['name'], )
            if self.find_ethnologue_only:
                if record['iso'] == '':
                    if self.verbose_output:
                        print "No iso for %s" % (record['name'], )
                    continue
                new_ethnologue_tree = e.find_label(record['name'], record['iso'])
                if new_ethnologue_tree is None:
                    if self.verbose_output:
                        print "Couldn't parse ethnologue entry for name: %s iso: %s" % (record['name'], record['iso'])
                    continue
                if self.newick:
                    ethnologue_trees_array.append(new_ethnologue_tree)
            else:
                if self.newick:
                    newick_labels_array.append((record['name'], record['breakdown']))
            if self.aline:
                output_string = self.output_template % record
                output_string += self.meaning_value_pairs(record['words'])
                print >>self.aline_output, '%s\t%s' % (i, output_string)
            if self.asjp:
                print >>self.asjp_output, record['name_line'] 
                print >>self.asjp_output, record['details_line']
                for line in record['lines']:
                    print >>self.asjp_output, line.strip()
            i+=1
        if self.asjp:
            #Give the ol' asjp an extra 5 newlines at the end for ol' times sake
            for i in xrange(5):
                print >>self.asjp_output 
        if self.newick:
            if self.find_ethnologue_only:
                newick_tree = {}
                for tree in ethnologue_trees_array:
                    newick_tree = e.merge(newick_tree, tree)
                newick_tree = e.prune_tree(newick_tree)
                newick_tree = e.newick_out(newick_tree)
            else:
                newick_tree = e.find_labels(newick_labels_array, label_finder = self.label_finder)
            print >>self.newick_output, "%s" % (newick_tree, )

    
if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename", help="ASJP database file")
    parser.add_option("-r", "--regex_filter", dest="regex_filter", help="Specify a regular expression to match against language families to choose which families to output")
    parser.add_option("-l", "--language", action="append", dest="languages", help="Specify specific language names to output one per switch")
    parser.add_option("-s", "--small", action="store_true", dest="small", help="Only output the small set of ASJP words for each language")
    parser.add_option("-a", "--asjp", action="store_true", dest="asjp", help="Output an ASJP formatted file for the languages specified")
    parser.add_option("-i", "--aline", action="store_true", dest="aline", help="Output a PyAline formatted file for the languages specified")
    parser.add_option("-n", "--newick", action="store_true", dest="newick", help="Output a newick tree file format for the languages specified, the tree coming from ethnologue or from the ASJP database depending on whether or not -e is specified")
    parser.add_option("-p", "--prefix", dest="output_file_prefix", help="Add a prefix to each output file (useful for putting them in a subdirectory)")
    parser.add_option("-e", "--ethnologue_only", action="store_true", dest="find_ethnologue_only", help="Only use languages that are found in ethnologue, and use the newick tree from ethnologue, not ASJP's 'expert' trees")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose_output", help="Verbose output")

    (options, args) = parser.parse_args()

    filter = words = input = None

    if options.filename:
        input = open(options.filename)
    else:
        input = sys.stdin

    if options.regex_filter:
        regex = re.compile(options.regex_filter)
        def filter(r):
            if regex.match(r['family']):
                return True
            else: 
                return False
    elif options.languages:
        def filter(r):
            if r['name'] in options.languages:
                return True
            return False
    if options.small:
        words = (1,2,3,11,12,18,19,21,22,23,25,28,30,31,34,39,40,41,43,44,47,48,51,53,54,57,58,61,66,72,74,75,77,82,85,86,92,95,96,100)

    if options.output_file_prefix:
        prefix = options.output_file_prefix
    else:
        prefix = 'output'
    p = ProcessASJPTextFiles(input=input, keys=words, filter=filter, output_file_prefix=prefix, aline=options.aline, asjp=options.asjp, newick=options.newick, find_ethnologue_only=options.find_ethnologue_only, verbose_output=options.verbose_output)
    p.process()
    
