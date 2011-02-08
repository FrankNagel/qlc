"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from routes import Mapper

def make_map(config):
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    map.minimization = False

    map.connect('/', controller='pages', action='index')
    #map.connect('/index.html', controller='pages', action='index')
    map.connect('/search/index.html', controller='search', action='index')
    map.connect('/search/result.html', controller='search', action='result')

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    # CUSTOM ROUTES HERE
    #map.connect('/source/{bibtexkey}/{srclanguage}/{tgtlanguage}/page/{pagenr}', controller='book', action='page')
    map.connect('/source/{bibtexkey}/{pagenr}/index.html', controller='book', action='page', requirements={'pagenr': '\d{1,4}'})
    map.connect('/source/{bibtexkey}/{pagenr}/layout.html', controller='book', action='page_with_layout', requirements={'pagenr': '\d{1,4}'})
    map.connect('/source/{bibtexkey}/{pagenr}/{pos_on_page}/formatting_annotations.xml', controller='book', action='formatting_annotations_for_entryid', format='xml', requirements={'pagenr': '\d{1,4}', 'pos_on_page': '\d{1,4}'})
    map.connect('/source/{bibtexkey}/{pagenr}/{pos_on_page}/dictinterpretation_annotations.xml', controller='book', action='dictinterpretation_annotations_for_entryid', format='xml', requirements={'pagenr': '\d{1,4}', 'pos_on_page': '\d{1,4}'})
    map.connect('/source/{bibtexkey}/{pagenr}/{pos_on_page}/text.xml', controller='book', action='entryid', format='xml', requirements={'pagenr': '\d{1,4}', 'pos_on_page': '\d{1,4}'})
    map.connect('/source/{bibtexkey}/{pagenr}/{pos_on_page}/index.html', controller='book', action='entryid', format='html', requirements={'pagenr': '\d{1,4}', 'pos_on_page': '\d{1,4}'})
    map.connect('/source/{bibtexkey}/{pagenr}/{pos_on_page}/edit.html', controller='book', action='edit_entryid', format='html', requirements={'pagenr': '\d{1,4}', 'pos_on_page': '\d{1,4}'})
    map.connect('/source/{bibtexkey}/{pagenr}/{pos_on_page}/save.html', controller='book', action='save_entryid', format='html', requirements={'pagenr': '\d{1,4}', 'pos_on_page': '\d{1,4}'})
    map.connect('/source/{bibtexkey}_{pagenr}_{pos_on_page}.py.txt', controller='book', action='entryid', format='py.txt', requirements={'pagenr': '\d{1,4}', 'pos_on_page': '\d{1,4}'})
    map.connect('/source/{bibtexkey}/dictionary-{startpage}-{endpage}/{startletter}/index.html', controller='book', action='letter')
    map.connect('/source/{bibtexkey}/dictionary-{startpage}-{endpage}.html', controller='book', action='dictdata', format='html', requirements={'startpage': '\d{1,4}', 'endpage': '\d{1,4}'})
    map.connect('/source/{bibtexkey}/{title}-{startpage}-{endpage}.html', controller='book', action='nondictdata', requirements={'startpage': '\d{1,4}', 'endpage': '\d{1,4}'})
    map.connect('/source/{bibtexkey}/index.html', controller='book', action='view', format='html')
    map.connect('/source/index.html', controller='book', action='index')
    
    # xml routes
    map.connect('/source/{bibtexkey}/dictionary-{startpage}-{endpage}-{annotationtype}-annotations.xml', controller='book', action='annotations_for_dictdata', format='xml', requirements={'startpage': '\d{1,4}', 'endpage': '\d{1,4}'})
    map.connect('/source/{bibtexkey}/create_xml_annotations_for_dictdata/dictionary-{startpage}-{endpage}-{annotationtype}-annotations.xml', controller='book', action='create_xml_annotations_for_dictdata', format='xml', requirements={'startpage': '\d{1,4}', 'endpage': '\d{1,4}'})
    map.connect('/source/{bibtexkey}/dictionary-{startpage}-{endpage}.xml', controller='book', action='dictdata', format='xml', requirements={'startpage': '\d{1,4}', 'endpage': '\d{1,4}'})
    map.connect('/source/{bibtexkey}/create_xml_dictdata/dictionary-{startpage}-{endpage}.xml', controller='book', action='create_xml_dictdata', format='xml', requirements={'startpage': '\d{1,4}', 'endpage': '\d{1,4}'})

    # wordlist routes
    map.connect('/source/{bibtexkey}/all-languages/{concept}/index.html', controller='book', action='concept_wordlist', format='html')
    map.connect('/source/{bibtexkey}/{language_bookname}/{concept}/index.html', controller='book', action='entryid_wordlist', format='html')
    map.connect('/source/{bibtexkey}/{language_bookname}/{concept}/edit.html', controller='book', action='edit_entryid_wordlist', format='html')
    map.connect('/source/{bibtexkey}/{language_bookname}/{concept}/save.html', controller='book', action='save_entryid_wordlist', format='html')
    map.connect('/source/{bibtexkey}/{language_bookname}/index.html', controller='book', action='language_wordlist', format='html')
    map.connect('/source/wordlists.html', controller='book', action='wordlists', format='html')
    
    map.connect('/component/{name}/index.html', controller='component', action='view')
    map.connect('/component/index.html', controller='component', action='index')

    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')

    return map
