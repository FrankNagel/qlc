#!/usr/bin/env python
import urllib2, re, sys
import pprint

class Ethnologue(object):
    def __init__(self):
        self.href_regex = re.compile('^show_family\.asp\?subid=')
        self.p_regex = re.compile('^level')
        self.wrapped_regex = re.compile('^\(.*\)$')
        pass
    
    def find_label(self, name, label):
        from BeautifulSoup import BeautifulSoup
        bs = BeautifulSoup(urllib2.urlopen('http://www.ethnologue.com/show_lang_family.asp?code=%s' % (label, )))
        current = x = {}
        try:
            invalid_code = bs.findAll("h3", text=re.compile("^Invalid code"))
            subid_invalid = bs.findAll("p", text=re.compile("^The subid used in the URL is invalid."))
            if len(subid_invalid) > 0 or len(invalid_code) > 0:
                return None
            for i in bs.find('div', id='LingTree').findAll('p', {'class': self.p_regex}):
                a = i.find('a', href=self.href_regex)
                if a is not None:
                    current[a['href'][22:]] = {}
                    current = current[a['href'][22:]]
                else:
                    current[name] = 1
        except:
            print "Had a big problem. %s %s" % (name, label)
            sys.exit(1)
        return x
    
    def merge(self, tree, new_tree):
        for key in new_tree.keys():
            if new_tree[key] == 1:
                tree[key] = 1
            elif tree.has_key(key):
                tree[key] = self.merge(tree[key], new_tree[key])
            else:
                tree[key] = new_tree[key]
        return tree

    def prune_tree(self, tree):
        if tree == 1:
            return tree
        keys = tree.keys()
        if len(keys) == 1:
            (key, ) = keys
            if tree[key] == 1:
                return tree
        
        for key in keys:
            tree[key] = self.prune_tree(tree[key])
            if tree[key] != 1 and len(tree[key].keys()) == 1:
                child = tree[key]
                (key2,) = child.keys()
                del tree[key]
                tree[key2] = child[key2]

        return tree

    def find_labels(self, name_label_pairs, pruned = 1, label_finder=None):
        if label_finder is None:
            label_finder = self.find_label
        tree = {}
        for (name, label) in name_label_pairs:
            tree = self.merge(tree, label_finder(name, label))
        if pruned:
            tree = self.prune_tree(tree)
        return self.newick_out(tree)

    def newick_out(self, tree, depth=0):
        string = ''
        if depth > 0:
            string += '('
        part1 = ','.join([ self.newick_out(tree[key], depth + 1)
                           for key in tree.keys() if tree[key] != 1])
        part2 = ','.join([ key for key in tree.keys() if tree[key] == 1])
        string += ','.join([ x for x in [part1, part2] if x != ''])
        if depth > 0:
            string += ')'

        match = self.wrapped_regex.search(string)
        if not match:
            string = '(' + string + ')'
        if depth == 0:
            string += ';'
        return string
            
if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename")
    (options, args) = parser.parse_args()
    if options.filename is None:
        print "Need a file name. "
        sys.exit(1)
    
    f = open(options.filename)
    labels = []
    for line in f:
        (name, label) = line.strip().split(",")
        labels.append((name, label))
    e = Ethnologue()
    print "%s" % (e.find_labels(labels), )
        
