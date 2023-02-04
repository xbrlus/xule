'''
xendrCommon

This file contains general until code that is common to the whole xender process.

Reivision number: $Change: $
'''

from arelle import PluginManager, FileSource

# This will hold the xule plugin module
_xule_plugin_info = None

# xule namespace used in the template
XULE_NAMESPACE_MAP = {'xule': 'http://xbrl.us/xule/2.0/template', 
                       'xhtml': 'http://www.w3.org/1999/xhtml',
                       'ix': 'http://www.xbrl.org/2013/inlineXBRL'}

class XendrException(Exception):
    pass

def getXulePlugin(cntlr):
    """Find the Xule plugin
    
    This will locate the Xule plugin module.
    """
    global _xule_plugin_info
    if _xule_plugin_info is None:
        for _plugin_name, plugin_info in PluginManager.modulePluginInfos.items():
            if plugin_info.get('moduleURL') == 'xule':
                _xule_plugin_info = plugin_info
                break
        else:
            cntlr.addToLog(_("Xule plugin is not loaded. Xule plugin is required to run DQC rules. This plugin should be automatically loaded."))
    
    return _xule_plugin_info

def getXuleMethod(cntlr, method_name):
    """Get method from Xule
    
    Get a method/function from the Xule plugin. This is how this validator calls functions in the Xule plugin.
    """
    return getXulePlugin(cntlr).get(method_name)

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