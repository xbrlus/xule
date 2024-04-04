'''
xendrCommon

This file contains general until code that is common to the whole xender process.

Reivision number: $Change: $
'''

from arelle import FileSource


# xule namespace used in the template
XULE_NAMESPACE_MAP = {'xule': 'http://xbrl.us/xendr/2.0/template', 
                       'xhtml': 'http://www.w3.org/1999/xhtml',
                       'ix': 'http://www.xbrl.org/2013/inlineXBRL'}

XENDR_FOOTNOTE_FACT_ID_CONSTANT_NAME = 'xendr-footnote-fact-ids'
XENDR_FOOTNOTE_FACT_XULE_FUNCTION_NAME = 'xendr-footnote-facts'
XENDR_OBJECT_ID_XULE_FUNCTION_NAME = 'xendr-model-id'
XENDR_FORMAT_FOOTNOTE = 'xendr-format-footnote'

class XendrException(Exception):
    pass

def clean_entities(text):
    '''Clean up HTML entities 
    
    lxml does not recognize HTML entities like &mdash;. As a work around this is converting these entities to 
    their HTML hex equivalent.
    '''

    if text is None:
        return text
    else:
        text = text.replace('&ldquo;', '&#x201c;')
        text = text.replace('&rdquo;', '&#x201d;')
        text = text.replace('&lsquo;', '&#x2018;')
        text = text.replace('&rsquo;', '&#x2019;')
        text = text.replace('&mdash;', '&#x2014;')
        text = text.replace('&ndash;', '&#x2013;')
        return text
    
def get_file_or_url(file_name, cntlr):
    try:
        file_source = FileSource.openFileSource(file_name, cntlr)
        file_object = file_source.file(file_name, binary=True)[0]    
        return file_object
    except:
        raise XendrException("Cannot open file: {}".format(file_name))