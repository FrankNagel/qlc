#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================================================================
#  Version: 1.5 (Oct 17, 2009)
#  Author: Antonio Fuschetto (fuschett@di.unipi.it), University of Pisa
# =============================================================================

# =============================================================================
#  This file is part of Tanl.
#
#  Tanl is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License, version 3,
#  as published by the Free Software Foundation.
#
#  Tanl is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
# =============================================================================

"""Wikipedia Extractor:
Extracts and cleans text from Wikipedia database dump and stores output in a
number of files of similar size in a given directory. Each file contains
several documents in Tanl document format.

Usage:
  WikiExtractor.py [options]

Options:
  -c, --compress        : compress output files using bzip2 algorithm
  -b ..., --bytes=...   : put specified bytes per output file (500K by default)
  -o ..., --output=...  : place output files in specified directory (current
                          directory by default)
  --help                : display this help and exit
  --usage               : display script usage
"""

import sys
import getopt
import pickle
import urllib.parse
import re
import bz2
import os.path
import fileinput

### PARAMS ####################################################################

prefix = 'http://it.wikipedia.org/wiki/'

### SUPPORT CLASSES ###########################################################

class WikiDocument:
    def __init__(self):
        self.id = None
        self.url = None
        self.text = None

    def __str__(self):
        return '<doc id="%d" url="%s">\n%s\n</doc>\n' % (self.id, self.url, self.text)

def get_wiki_document_url(wiki_document_title, prefix):
    quoted_title = urllib.parse.quote(wiki_document_title.replace(' ', '_').encode('utf-8'))
    quoted_title = quoted_title.replace('%28', '(').replace('%29', ')')
    return prefix + quoted_title[0].upper() + quoted_title[1:]

#------------------------------------------------------------------------------

class WikiExtractor:
    __garbage_tags = ('ref', 'gallery', 'timeline', 'noinclude', 'pre', 'table', 'tr', 'td',
                      'ul', 'li', 'ol', 'dl', 'dt', 'dd', 'menu', 'dir', 'onlyinclude')
    __wrapper_tags = ('nowiki', 'cite', 'source', 'hiero', 'div', 'font', 'span', 'strong',
                      'strike', 'blockquote', 'tt', 'var', 'sup', 'sub', 'big', 'small',
                      'center', 'h1', 'h2', 'h3', 'em', 'b', 'i', 'u', 'a', 's', 'p')
    __single_tags = ('references', 'ref', 'img', 'br', 'hr', 'li', 'dt', 'dd')
    __placeholder_tags = {'math':'formula', 'code':'codice'}

    __project_namespaces = ('wikipedia', 'mediawiki', 'wikiquote', 'wikibooks', 'wikisource',
                            'wiktionary', 'wikispecies', 'wikinews', 'wikiversita', 'commons')
    __garbage_namespaces = ('immagine', 'image', 'categoria', 'category', 'file')

    __char_entities =  {'&nbsp;'   :'\u00A0', '&iexcl;' :'\u00A1', '&cent;'    :'\u00A2',
                        '&pound;'  :'\u00A3', '&curren;':'\u00A4', '&yen;'     :'\u00A5',
                        '&brvbar;' :'\u00A6', '&sect;'  :'\u00A7', '&uml;'     :'\u00A8',
                        '&copy;'   :'\u00A9', '&ordf;'  :'\u00AA', '&laquo;'   :'\u00AB',
                        '&not;'    :'\u00AC', '&shy;'   :'\u00AD', '&reg;'     :'\u00AE',
                        '&macr;'   :'\u00AF', '&deg;'   :'\u00B0', '&plusmn;'  :'\u00B1',
                        '&sup2;'   :'\u00B2', '&sup3;'  :'\u00B3', '&acute;'   :'\u00B4',
                        '&micro;'  :'\u00B5', '&para;'  :'\u00B6', '&middot;'  :'\u00B7',
                        '&cedil;'  :'\u00B8', '&sup1;'  :'\u00B9', '&ordm;'    :'\u00BA',
                        '&raquo;'  :'\u00BB', '&frac14;':'\u00BC', '&frac12;'  :'\u00BD',
                        '&frac34;' :'\u00BE', '&iquest;':'\u00BF', '&Agrave;'  :'\u00C0',
                        '&Aacute;' :'\u00C1', '&Acirc;' :'\u00C2', '&Atilde;'  :'\u00C3',
                        '&Auml;'   :'\u00C4', '&Aring;' :'\u00C5', '&AElig;'   :'\u00C6',
                        '&Ccedil;' :'\u00C7', '&Egrave;':'\u00C8', '&Eacute;'  :'\u00C9',
                        '&Ecirc;'  :'\u00CA', '&Euml;'  :'\u00CB', '&Igrave;'  :'\u00CC',
                        '&Iacute;' :'\u00CD', '&Icirc;' :'\u00CE', '&Iuml;'    :'\u00CF',
                        '&ETH;'    :'\u00D0', '&Ntilde;':'\u00D1', '&Ograve;'  :'\u00D2',
                        '&Oacute;' :'\u00D3', '&Ocirc;' :'\u00D4', '&Otilde;'  :'\u00D5',
                        '&Ouml;'   :'\u00D6', '&times;' :'\u00D7', '&Oslash;'  :'\u00D8',
                        '&Ugrave;' :'\u00D9', '&Uacute;':'\u00DA', '&Ucirc;'   :'\u00DB',
                        '&Uuml;'   :'\u00DC', '&Yacute;':'\u00DD', '&THORN;'   :'\u00DE',
                        '&szlig;'  :'\u00DF', '&agrave;':'\u00E0', '&aacute;'  :'\u00E1',
                        '&acirc;'  :'\u00E2', '&atilde;':'\u00E3', '&auml;'    :'\u00E4',
                        '&aring;'  :'\u00E5', '&aelig;' :'\u00E6', '&ccedil;'  :'\u00E7',
                        '&egrave;' :'\u00E8', '&eacute;':'\u00E9', '&ecirc;'   :'\u00EA',
                        '&euml;'   :'\u00EB', '&igrave;':'\u00EC', '&iacute;'  :'\u00ED',
                        '&icirc;'  :'\u00EE', '&iuml;'  :'\u00EF', '&eth;'     :'\u00F0',
                        '&ntilde;' :'\u00F1', '&ograve;':'\u00F2', '&oacute;'  :'\u00F3',
                        '&ocirc;'  :'\u00F4', '&otilde;':'\u00F5', '&ouml;'    :'\u00F6',
                        '&divide;' :'\u00F7', '&oslash;':'\u00F8', '&ugrave;'  :'\u00F9',
                        '&uacute;' :'\u00FA', '&ucirc;' :'\u00FB', '&uuml;'    :'\u00FC',
                        '&yacute;' :'\u00FD', '&thorn;' :'\u00FE', '&yuml;'    :'\u00FF',
                        '&fnof;'   :'\u0192', '&Alpha;' :'\u0391', '&Beta;'    :'\u0392',
                        '&Gamma;'  :'\u0393', '&Delta;' :'\u0394', '&Epsilon;' :'\u0395',
                        '&Zeta;'   :'\u0396', '&Eta;'   :'\u0397', '&Theta;'   :'\u0398',
                        '&Iota;'   :'\u0399', '&Kappa;' :'\u039A', '&Lambda;'  :'\u039B',
                        '&Mu;'     :'\u039C', '&Nu;'    :'\u039D', '&Xi;'      :'\u039E',
                        '&Omicron;':'\u039F', '&Pi;'    :'\u03A0', '&Rho;'     :'\u03A1',
                        '&Sigma;'  :'\u03A3', '&Tau;'   :'\u03A4', '&Upsilon;' :'\u03A5',
                        '&Phi;'    :'\u03A6', '&Chi;'   :'\u03A7', '&Psi;'     :'\u03A8',
                        '&Omega;'  :'\u03A9', '&alpha;' :'\u03B1', '&beta;'    :'\u03B2',
                        '&gamma;'  :'\u03B3', '&delta;' :'\u03B4', '&epsilon;' :'\u03B5',
                        '&zeta;'   :'\u03B6', '&eta;'   :'\u03B7', '&theta;'   :'\u03B8',
                        '&iota;'   :'\u03B9', '&kappa;' :'\u03BA', '&lambda;'  :'\u03BB',
                        '&mu;'     :'\u03BC', '&nu;'    :'\u03BD', '&xi;'      :'\u03BE',
                        '&omicron;':'\u03BF', '&pi;'    :'\u03C0', '&rho;'     :'\u03C1',
                        '&sigmaf;' :'\u03C2', '&sigma;' :'\u03C3', '&tau;'     :'\u03C4',
                        '&upsilon;':'\u03C5', '&phi;'   :'\u03C6', '&chi;'     :'\u03C7',
                        '&psi;'    :'\u03C8', '&omega;' :'\u03C9', '&thetasym;':'\u03D1',
                        '&upsih;'  :'\u03D2', '&piv;'   :'\u03D6', '&bull;'    :'\u2022',
                        '&hellip;' :'\u2026', '&prime;' :'\u2032', '&Prime;'   :'\u2033',
                        '&oline;'  :'\u203E', '&frasl;' :'\u2044', '&weierp;'  :'\u2118',
                        '&image;'  :'\u2111', '&real;'  :'\u211C', '&trade;'   :'\u2122',
                        '&alefsym;':'\u2135', '&larr;'  :'\u2190', '&uarr;'    :'\u2191',
                        '&rarr;'   :'\u2192', '&darr;'  :'\u2193', '&harr;'    :'\u2194',
                        '&crarr;'  :'\u21B5', '&lArr;'  :'\u21D0', '&uArr;'    :'\u21D1',
                        '&rArr;'   :'\u21D2', '&dArr;'  :'\u21D3', '&hArr;'    :'\u21D4',
                        '&forall;' :'\u2200', '&part;'  :'\u2202', '&exist;'   :'\u2203',
                        '&empty;'  :'\u2205', '&nabla;' :'\u2207', '&isin;'    :'\u2208',
                        '&notin;'  :'\u2209', '&ni;'    :'\u220B', '&prod;'    :'\u220F',
                        '&sum;'    :'\u2211', '&minus;' :'\u2212', '&lowast;'  :'\u2217',
                        '&radic;'  :'\u221A', '&prop;'  :'\u221D', '&infin;'   :'\u221E',
                        '&ang;'    :'\u2220', '&and;'   :'\u2227', '&or;'      :'\u2228',
                        '&cap;'    :'\u2229', '&cup;'   :'\u222A', '&int;'     :'\u222B',
                        '&there4;' :'\u2234', '&sim;'   :'\u223C', '&cong;'    :'\u2245',
                        '&asymp;'  :'\u2248', '&ne;'    :'\u2260', '&equiv;'   :'\u2261',
                        '&le;'     :'\u2264', '&ge;'    :'\u2265', '&sub;'     :'\u2282',
                        '&sup;'    :'\u2283', '&nsub;'  :'\u2284', '&sube;'    :'\u2286',
                        '&supe;'   :'\u2287', '&oplus;' :'\u2295', '&otimes;'  :'\u2297',
                        '&perp;'   :'\u22A5', '&sdot;'  :'\u22C5', '&lceil;'   :'\u2308',
                        '&rceil;'  :'\u2309', '&lfloor;':'\u230A', '&rfloor;'  :'\u230B',
                        '&lang;'   :'\u2329', '&rang;'  :'\u232A', '&loz;'     :'\u25CA',
                        '&spades;' :'\u2660', '&clubs;' :'\u2663', '&hearts;'  :'\u2665',
                        '&diams;'  :'\u2666', '&quot;'  :'\u0022', '&lt;'      :'\u003C',
                        '&gt;'     :'\u003E', '&OElig;' :'\u0152', '&oelig;'   :'\u0153',
                        '&Scaron;' :'\u0160', '&scaron;':'\u0161', '&Yuml;'    :'\u0178',
                        '&circ;'   :'\u02C6', '&tilde;' :'\u02DC', '&ensp;'    :'\u2002',
                        '&emsp;'   :'\u2003', '&thinsp;':'\u2009', '&zwnj;'    :'\u200C',
                        '&zwj;'    :'\u200D', '&lrm;'   :'\u200E', '&rlm;'     :'\u200F',
                        '&ndash;'  :'\u2013', '&mdash;' :'\u2014', '&lsquo;'   :'\u2018',
                        '&rsquo;'  :'\u2019', '&sbquo;' :'\u201A', '&ldquo;'   :'\u201C',
                        '&rdquo;'  :'\u201D', '&bdquo;' :'\u201E', '&dagger;'  :'\u2020',
                        '&Dagger;' :'\u2021', '&permil;':'\u2030', '&lsaquo;'  :'\u2039',
                        '&rsaquo;' :'\u203A', '&euro;'  :'\u20AC'}

    def __init__(self):
        # Riconosce i commenti HTML
        self.__comment_pattern = re.compile(r'<!--.*?-->', re.DOTALL)

        # Riconosce i tag HTML spazzatura
        self.__garbage_tag_patterns = list()
        for tag in self.__class__.__garbage_tags:
            pattern = re.compile(r'<\s*%s(\s*| [^/]+?)>.*?<\s*/\s*%s\s*>' % (tag, tag), re.DOTALL | re.IGNORECASE)
            self.__garbage_tag_patterns.append(pattern)

        # Riconosce i tag HTML contenitori
        self.__wrapper_tag_patterns = list()
        for tag in self.__class__.__wrapper_tags:
            left_pattern = re.compile(r'<\s*%s(\s*| [^/]+?)>' % tag, re.DOTALL | re.IGNORECASE)
            right_pattern = re.compile(r'<\s*/\s*%s\s*>' % tag, re.DOTALL | re.IGNORECASE)
            self.__wrapper_tag_patterns.append((left_pattern, right_pattern))

        # Riconosce i tag HTML singoli
        self.__single_tag_patterns = list()
        for tag in self.__class__.__single_tags:
            good_pattern = re.compile(r'<\s*%s(\s*| .+?)/\s*>' % tag, re.DOTALL | re.IGNORECASE)
            bad_pattern = re.compile(r'<\s*(/|\\)?\s*%s(\s*| [^/]+?)\\?\s*>' % tag, re.DOTALL | re.IGNORECASE)
            self.__single_tag_patterns.append((good_pattern, bad_pattern))

        # Riconosce i tag HTML segnaposto
        self.__placeholder_tag_patterns = list()
        for tag in self.__class__.__placeholder_tags.keys():
            pattern = re.compile(r'<\s*%s(\s*| [^/]+?)>.*?<\s*/\s*%s\s*>' % (tag, tag), re.DOTALL | re.IGNORECASE)
            self.__placeholder_tag_patterns.append((pattern, self.__class__.__placeholder_tags[tag]))

        # Riconosce le tabelle e i template
        self.__table_pattern = re.compile(r'\{[^{]*?\}', re.DOTALL)

        # Riconosce i wikilink
        good_wikilink_pattern = re.compile(r'\[\[[^[]*?\]\]', re.DOTALL)
        bad_left_wikilink_pattern = re.compile(r'\[[^[]*?\]\]', re.DOTALL)
        bad_right_wikilink_pattern = re.compile(r'\[\[[^[]*?\]', re.DOTALL)
        self.__wikilink_pattern = (good_wikilink_pattern, bad_left_wikilink_pattern, bad_right_wikilink_pattern)

        # Riconosce i link HTTP
        self.__http_link_pattern = re.compile(r'\[http.*?\]', re.DOTALL | re.IGNORECASE)

        # Riconosce gli apostrofi che precedono grassetto e corsivo
        apostrophe_bold_pattern = re.compile(r"\w'('''[^\s'][^']*?[^\s']''')[^']", re.DOTALL)
        apostrophe_italic_pattern = re.compile(r"\w'(''[^\s'][^']*?[^\s']'')[^']", re.DOTALL)
        self.__apostrophe_pattern = (apostrophe_bold_pattern, apostrophe_italic_pattern)

        # Riconosce le entita' numeriche
        self.__numeric_entity_pattern = re.compile(r'&#\d+?;')

        # Riconosce gli spazi multipli
        self.__multi_space_pattern = re.compile(r' {2,}')

        # Riconosce i punti multipli
        self.__multi_dot_pattern = re.compile(r'\.{4,}')

    def extract(self, wiki_document):
        wiki_document = self.__clean(wiki_document)
        if not wiki_document: return None

        wiki_document = self.__compact(wiki_document)
        return wiki_document

    def __clean(self, wiki_document):
        # Rende maggiormente riconoscibili i tag
        wiki_document.text = wiki_document.text.replace('&lt;', '<').replace('&gt;', '>')
        wiki_document.text = wiki_document.text.replace('<<', '«').replace('>>', '»')

        # Elimina i commenti HTML
        wiki_document.text = self.__comment_pattern.sub('', wiki_document.text)

        # Elimina i tag HTML spazzatura
        for pattern in self.__garbage_tag_patterns:
            wiki_document.text = pattern.sub('', wiki_document.text)

        # Elimina i tag HTML contenitori
        for left_pattern, right_pattern in self.__wrapper_tag_patterns:
            wiki_document.text = left_pattern.sub('', wiki_document.text)
            wiki_document.text = right_pattern.sub('', wiki_document.text)

        # Elimina i tag HTML singoli
        for good_pattern, bad_pattern in self.__single_tag_patterns:
            wiki_document.text = good_pattern.sub('', wiki_document.text)
            wiki_document.text = bad_pattern.sub('', wiki_document.text)

        # Elimina i tag HTML segnaposto
        for pattern, placeholder in self.__placeholder_tag_patterns:
            index = 1
            for match in pattern.finditer(wiki_document.text):
                wiki_document.text = wiki_document.text.replace(match.group(), '%s_%d' % (placeholder, index))
                index += 1

        # Elimina le tabelle e i template
        wiki_document.text = wiki_document.text.replace('{{end box}}', '}')
        wiki_document.text = wiki_document.text.replace('{{', '{').replace('}}', '}')
        wiki_document.text = wiki_document.text.replace('{|', '{').replace('|}', '}')
        wiki_document.text = self.__table_pattern.sub('', wiki_document.text)
        wiki_document.text = self.__table_pattern.sub('', wiki_document.text)
        wiki_document.text = self.__table_pattern.sub('', wiki_document.text)

        # Gestisce i wikilink (ben formattati; due livelli di annidamento)
        good_wikilink_pattern = self.__wikilink_pattern[0]
        #for match in good_wikilink_pattern.finditer(wiki_document.text):
        #    wikilink = match.group()
        #    document_title, link_text = self.__handle_wikilink(wikilink[2:-2])
        #    wiki_document.text = wiki_document.text.replace(wikilink, self.__get_anchor_tag(document_title, link_text))
        for match in good_wikilink_pattern.finditer(wiki_document.text):
            wikilink = match.group()
            wiki_document.text = wiki_document.text.replace(wikilink, self.__handle_wikilink(wikilink[2:-2])[1])

        # Gestisce i wikilink (mal formattati)
        bad_left_wikilink_pattern = self.__wikilink_pattern[1]
        for match in bad_left_wikilink_pattern.finditer(wiki_document.text):
            wikilink = match.group()
            document_title, link_text = self.__handle_wikilink(wikilink[1:-2])
            wiki_document.text = wiki_document.text.replace(wikilink, self.__get_anchor_tag(document_title, link_text))
        bad_right_wikilink_pattern = self.__wikilink_pattern[2]
        for match in bad_right_wikilink_pattern.finditer(wiki_document.text):
            wikilink = match.group()
            document_title, link_text = self.__handle_wikilink(wikilink[2:-1])
            wiki_document.text = wiki_document.text.replace(wikilink, self.__get_anchor_tag(document_title, link_text))
        wiki_document.text = wiki_document.text.replace('[[', '').replace(']]', '')

        # Elimina i link HTTP
        wiki_document.text = self.__http_link_pattern.sub('', wiki_document.text).replace('[]', '')

        # Gestisce i grassetti e i corsivi
        apostrophe_bold_pattern = self.__apostrophe_pattern[0]
        for match in apostrophe_bold_pattern.finditer(wiki_document.text):
            bold_text = match.group(1)
            wiki_document.text = wiki_document.text.replace(bold_text, bold_text[3:-3])
        apostrophe_italic_pattern = self.__apostrophe_pattern[1]
        for match in apostrophe_italic_pattern.finditer(wiki_document.text):
            italic_text = match.group(1)
            wiki_document.text = wiki_document.text.replace(italic_text, '&quot;%s&quot;' % italic_text[2:-2])
        wiki_document.text = wiki_document.text.replace("'''", '').replace("''", '&quot;')

        # Gestisce i caratteri speciali
        wiki_document.text = wiki_document.text.replace('&amp;', '&').replace('&quot;&quot;', '&quot;')
        for entity in self.__class__.__char_entities.keys():
            wiki_document.text = wiki_document.text.replace(entity, self.__class__.__char_entities[entity])

        # Gestisce i caratteri speciali
        for match in self.__numeric_entity_pattern.finditer(wiki_document.text):
            entity = match.group()
            wiki_document.text = wiki_document.text.replace(entity, self.__handle_unicode(entity))

        # Gestisce alcune imperfezioni del testo
        wiki_document.text = wiki_document.text.replace('\t', ' ')
        wiki_document.text = self.__multi_space_pattern.sub(' ', wiki_document.text)
        wiki_document.text = self.__multi_dot_pattern.sub('...', wiki_document.text)
        wiki_document.text = wiki_document.text.replace(' ,', ',').replace(' .', '.')
        wiki_document.text = wiki_document.text.replace(' :', ':').replace(' ;', ';')
        wiki_document.text = wiki_document.text.replace(',,', ',').replace(',.', '.')
        wiki_document.text = wiki_document.text.replace('( ', '(').replace(' )', ')')
        wiki_document.text = wiki_document.text.replace('[ ', '[').replace(' ]', ']')
        wiki_document.text = wiki_document.text.replace('« ', '«').replace(' »', '»')

        return wiki_document

    def __compact(self, wiki_document):
        page = list()
        paragraph = list()

        for line in wiki_document.text.split('\n'):
            line = line.strip()
            if not line: continue

            # Gestisce il titolo della pagina
            if line.startswith('++'):
                title = line[2:-2]
                if title and title[-1] not in '!?':
                    title = '%s.' % title
                page = [title]
            # Gestisce i titoli dei paragrafi
            elif line.startswith('=='):
                if len(paragraph) > 1:
                    page.extend(paragraph)
                title = line[2:-2]
                if title and title[-1] not in '!?':
                    title = '%s.' % title
                paragraph = [title]
            # Elimina gli elenchi puntati e numerati
            elif line[-1] == ':' or line[0] in '*#:;':
                continue
            # Elimina i resti delle tabelle
            elif line[0] in '{|' or line[-1] in '}':
                continue
            # Elimina le righe non significative
            elif (line[0] == '(' and line[-1] == ')') or line.strip('.-') == '':
                continue
            # Elimina le righe con un basso numero di token
            elif not '_' in line and len(line.split()) < 6:
                continue
            # Gestisce il testo della pagina
            elif len(paragraph) == 0:
                page.append(line)
            # Gestisce il testo dei paragrafi
            else:
                paragraph.append(line)

        if len(paragraph) > 1:
            page.extend(paragraph)
        elif len(page) == 1: return None

        wiki_document.text = '\n'.join(page)
        return wiki_document

    def __handle_wikilink(self, wikilink):
        tokens = wikilink.split(':')
        while not tokens[0]:
            if len(tokens) < 2: return '', ''
            tokens = tokens[1:]

        if len(tokens) == 1 or tokens[0].strip().lower() in self.__class__.__project_namespaces:
            tokens = tokens[-1].split('|')
            while not tokens[-1]:
                if len(tokens) < 2: return '', ''
                tokens = tokens[:-1]
            link_text = tokens[-1].split('#')[-1].split('/')[-1].strip()
            if len(tokens) > 1:
                article_title = tokens[-2].strip()
            else:
                 article_title = link_text
            return article_title, link_text

        if tokens[0].strip().lower() in self.__class__.__garbage_namespaces: return '', ''

        tokens = tokens[-1].split('|')
        while not tokens[-1]:
            if len(tokens) < 2: return '', ''
            tokens = tokens[:-1]
        if len(tokens) == 1: return '', ''
        link_text = tokens[-1].split('#')[-1].split('/')[-1].strip()
        if len(tokens) > 1:
            article_title = tokens[-2].strip()
        else:
            article_title = link_text
        return article_title, link_text

    def __get_anchor_tag(self, document_title, link_text):
        if not link_text: return ''
        if not document_title: return link_text
        return '<a href="%s">%s</a>' % (get_wiki_document_url(document_title, ''), link_text)

    def __handle_unicode(self, entity):
        numeric_code = int(entity[2:-1])
        if numeric_code >= 0x10000: return ''
        return unichr(numeric_code)

#------------------------------------------------------------------------------

class OutputSplitter:
    def __init__(self, compress, max_file_size, path_name):
        self.__dir_index = 0
        self.__file_index = -1
        self.__cur_file_size = 0
        self.__compress = compress
        self.__max_file_size = max_file_size
        self.__path_name = path_name
        self.__out_file = self.__open_next_file()

    def write(self, text):
        text_len = len(text)
        if self.__cur_file_size + text_len / 2 > self.__max_file_size:
            self.__close_cur_file()
            self.__out_file = self.__open_next_file()
            self.__cur_file_size = 0
        self.__out_file.write(text)
        self.__cur_file_size += text_len

    def close(self):
        self.__close_cur_file()

    def __open_next_file(self):
        self.__file_index += 1
        if self.__file_index == 100:
            self.__dir_index += 1
            self.__file_index = 0
        dir_name = self.__get_dir_name()
        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)
        file_name = os.path.join(dir_name, self.__get_file_name())
        if self.__compress:
            return bz2.BZ2File('%s.bz2' % file_name, 'w')
        else:
            return open(file_name, 'w')

    def __close_cur_file(self):
        self.__out_file.close()

    def __get_dir_name(self):
        char1 = self.__dir_index % 26
        char2 = self.__dir_index / 26 % 26
        return os.path.join(self.__path_name, '%c%c' % (ord('A') + char2, ord('A') + char1))

    def __get_file_name(self):
        return 'wiki%02d' % self.__file_index

### CORE ######################################################################

def process_data(input_file, wiki_extractor, output_splitter):
    page = []
    for line in input_file:
        line = line.strip()
        if line == '<page>':
            page = []
        elif line == '</page>':
            process_page(page, wiki_extractor, output_splitter)
        else:
            if isinstance(line, bytes):
                page.append(line.decode("utf-8"))
            else:
                page.append(line)

#------------------------------------------------------------------------------

def process_page(page, wiki_extractor, output_splitter):
    wiki_document = extract_document(page)
    if not wiki_document: return

    wiki_document = wiki_extractor.extract(wiki_document)
    if not wiki_document: return

    output_splitter.write(wiki_document.__str__().encode('utf-8'))

#------------------------------------------------------------------------------

def extract_document(page):
    wiki_document = WikiDocument()
    for line in page:
        if not line: continue

        # Identificatore della pagina (nodo XML)
        if not wiki_document.id and line.startswith('<id>') and line.endswith('</id>'):
            wiki_document.id = int(line[4:-5])
            continue
        # Titolo della pagina (nodo XML)
        elif not wiki_document.url and line.startswith('<title>') and line.endswith('</title>'):
            title = line[7:-8].replace('&amp;', '&')
            if ':' in title: return None
            wiki_document.url = get_wiki_document_url(title, prefix)
            wiki_document.text = '++%s++' % title
            continue
        # Inizio del testo della pagina (nodo XML)
        elif line.startswith('<text'):
            if line.endswith('</text>'): return None
            line = line[27:]
            if not line: continue
        # Fine del testo della pagina (nodo XML)
        elif line.endswith('</text>'):
            line = line[:-7]
            if not line: continue
        # Informazione superflua (nodo XML)
        elif line[0] == '<':
            continue
        # Titolo di paragafo (testo della pagina)
        elif line[0] == '=':
            line = '==%s==' % line.strip('= ')

        wiki_document.text += '\n%s' % line

    return wiki_document

### USER INTERFACE ############################################################

def show_help():
    print(__doc__, file=sys.stdout)

def show_usage(output_file, script_name):
    print('Usage: %s [options]' % script_name, file=output_file)

def show_suggestion(output_file, script_name):
    print('Try \'%s --help\' for more information.' % script_name, file=output_file)

def show_size_error(script_name, file_size):
    print('%s: %s: Insufficient or invalid number of bytes' % (script_name, file_size), file=sys.stderr)

def show_file_error(script_name, file_name):
    print('%s: %s: No such file or directory' % (script_name, file_name), file=sys.stderr)

def main():
    script_name = os.path.basename(sys.argv[0])

    try:
        long_opts = ['help', 'usage', 'compress', 'bytes=', 'output=']
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'cb:o:', long_opts)
    except getopt.GetoptError:
        show_usage(sys.stderr, script_name)
        show_suggestion(sys.stderr, script_name)
        sys.exit(1)

    compress = False
    file_size = 500 * 1024
    output_dir = '.'

    for opt, arg in opts:
        if opt == '--help':
            show_help()
            sys.exit()
        elif opt == '--usage':
            show_usage(sys.stdout, script_name)
            sys.exit()
        elif opt in ('-c', '--compress'):
            compress = True
        elif opt in ('-b', '--bytes'):
            try:
                if arg[-1] in 'kK':
                    file_size = int(arg[:-1]) * 1024
                elif arg[-1] in 'mM':
                    file_size = int(arg[:-1]) * 1024 * 1024
                else:
                    file_size = int(arg)
                if file_size < 200 * 1024: raise ValueError()
            except ValueError:
                show_size_error(script_name, arg)
                sys.exit(2)
        elif opt in ('-o', '--output'):
            if os.path.isdir(arg):
                output_dir = arg
            else:
                show_file_error(script_name, arg)
                sys.exit(3)

    #if len(args) > 0:
    #    show_usage(sys.stderr, script_name)
    #    show_suggestion(sys.stderr, script_name)
    #    sys.exit(4)

    wiki_extractor = WikiExtractor()
    output_splitter = OutputSplitter(compress, file_size, output_dir)
    process_data(fileinput.input(args), wiki_extractor, output_splitter)

    output_splitter.close()

if __name__ == '__main__':
    main()
