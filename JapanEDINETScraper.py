from bs4 import BeautifulSoup
import urllib
from http import cookiejar
from io import BytesIO
import copy
import optparse
import os
import pprint
import re
import ssl
import zipfile

_base_url = 'https://disclosure.edinet-fsa.go.jp'
_a_url = 'http://disclosure.edinet-fsa.go.jp/EKW0EZ1001.html'
_debug = False
_first_time = True

def call(cntlr, url, url_opener, name):

    cntlr.addToLog("URL Requeset: {}".format(url), "info")
    try:
        resp = url_opener.open(url)
    except:
        return None, None, None

    if _debug:
        print("Response", name, "\n" + pprint.pformat(resp.info().items()))

        with open('{}_info.txt'.format(name), 'w') as info_out:
            pprint.pprint(resp.info().items(), info_out)

    cntlr.addToLog("URL Response Received", "info")

    if resp.info().get('Content-Type','') in ('application/zip', 'application/octet-stream'):
        type = 'zip'
        soup = resp.read()
        if _debug:
            with open('{}.zip'.format(name), 'wb') as zip_out:
                zip_out.write(soup)

    elif 'text/html' in resp.info().get('Content-Type',''):
        type = 'html'
        html = resp.read()
        soup = BeautifulSoup(html, 'html.parser')

        resp_cookie = resp.info().get('Set-Cookie')
        if resp_cookie is not None:
            cookie = resp_cookie

        if _debug:
            with open ('{}_info.txt'.format(name),'w') as info_out:
                pprint.pprint(resp.info().items(), info_out)

            with open('{}_out.html'.format(name),'wb') as body_out:
                body_out.write(html)
    else:
        type = None
        soup = None

    return resp, soup, type

def extract_from_href(href):
    re_res = re.match(r'''[^\(]+\(\'([^\']*)\'\s*,\s*\'([^\']*)\'\s*,\s*\'([^\']*)\'\s*,\s*\'([^\']*)\'\s*,\s*\'([^\']*)\'\s*\)\s*''', href)
    return re_res.groups()

def extract_from_function_call(args):

    args_string = re.sub(r'''\s|\'|\"''', "", args)
    try:
        verb, bean, pid, tid, *other = args_string.split(',')
    except ValueError:
        print("Cannot parse doAction on search screen")
        exit()

    return verb, bean, pid, tid, other

def extract_inputs(soup, url_query):
    input_dict = dict()
    inputs = soup.find_all('input', type='hidden')
    for input in inputs:
        field_value = input.get('value', '')
        if field_value != '':
            field_name = input.get('name')
            if field_name not in url_query:
                input_dict[field_name] = field_value

    return input_dict

def scraper_main(cntlr, options, edinet_code):
    cntlr.addToLog("Scraping JapanEDINET website for EDINET code {}".format(edinet_code), "info")

    # This context ignores the ssl certificate
    context = ssl._create_unverified_context()
    cookie_jar = cookiejar.CookieJar()
    url_opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context),
                                             urllib.request.HTTPCookieProcessor(cookie_jar))
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
    url_opener.addheaders = header.items()

    url_request = []

    # Start the session
    url_request.append(_a_url)
    resp, soup, resp_type = call(cntlr, _a_url, url_opener, 'a - Top Page')
    if resp_type != 'html':
        cntlr.addToLog("Did not get html back from request for EDINET code {}.\n{}".format(edinet_code, _a_url))
        return
    # Get the TID
    search_a = soup.find_all(href=re.compile('BLogicE'))
    verb, bean, pid, tid, _x = extract_from_href(search_a[0].attrs['href'])

    # Go to the search page
    search_url = _base_url + '/E01EW/BLMainController.jsp?' \
                 'uji.bean={bean}&uji.verb={verb}&TID={tid}&PID={pid}&SESSIONKEY=&lgKbn=1&dflg=0&iflg=0' \
                 ''.format(bean=bean, verb=verb, pid=pid, tid=tid)

    url_request.append(search_url)
    resp, soup, resp_type = call(cntlr, search_url, url_opener, 'b - Simple Search Page')
    if resp_type != 'html':
        cntlr.addToLog("Did not get html back from request for EDINET code {}.\n{}".format(edinet_code, search_url))
        return
    # Scrape
    # Need to find the doAction() function call in the script
    script = soup.find(lambda t: t.name == 'script' and 'src' not in t.attrs and re.search(r'doAction\s*\([^)]+\s*\)', t.string))
    if script == None:
        cntlr.addToLog("Cannot process search screen")
        return
    do_action_args = re.search(r'doAction\s*\(([^)]+)\s*\)', script.string)
    if do_action_args is None:
        cntlr.addToLog("Cannot parse doAction on search screen")
        return
    args_string = do_action_args.group(1)
    verb, bean, pid, tid, other = extract_from_function_call(args_string)

    url_query = {'uji.bean': bean,
                 'uji.verb': verb,
                 'TID': tid,
                 'PID': pid,
                 'mul' : edinet_code,
                 'fls': 'on', # Annual Securities Report - Semiannual Securities Report - Quarterly Securities Report
                 'lpr': 'on', # Report of Possession of Large Volume
                 'oth': 'on', # Other types of documents
                 'mon': '',
                 'yer': '',
                 'pfs': 5 # all periods
                 }

    input_dict = extract_inputs(soup, url_query)
    url_query.update(input_dict)

    search_url = _base_url + '/E01EW/BLMainController.jsp?' + '&'.join("{}={}".format(k, v) for k, v in url_query.items())
    url_request.append(search_url)
    resp, soup, resp_type = call(cntlr, search_url, url_opener, 'c - Simple Search Result page')
    if resp_type != 'html':
        cntlr.addToLog("Did not get html back from request for EDINET code {}.\n{}".format(edinet_code, _a_url))
        return

    # Make the call to download the zip file

    # Need to find the downloadConfirmFile() function call in the script
    download_button = soup.find(lambda t: t.name == 'input' and re.search(r'downloadConfirmFile\s*\([^)]+\s*\)', t.attrs.get('onclick','')))

    if download_button == None:
        cntlr.addToLog("Cannot process search result screen")
        return
    do_action_args = re.search(r'downloadConfirmFile\s*\(([^)]+)\s*\)', download_button.attrs.get('onclick',''))
    if do_action_args is None:
        cntlr.addToLog("Cannot parse downloadConfirmFile on search result screen")
        return
    args_string = do_action_args.group(1)
    verb, bean, pid, tid, other = extract_from_function_call(args_string)

    url_query = {'uji.bean': bean,
                 'uji.verb': verb,
                 'TID': tid,
                 'PID': pid,
                 'mul' : edinet_code,
                 'fls': 'on', # Annual Securities Report - Semiannual Securities Report - Quarterly Securities Report
                 'lpr': 'on', # Report of Possession of Large Volume
                 'oth': 'on', # Other types of documents
                 'mon': '',
                 'yer': '',
                 'pfs': 5 # all periods
                 }

    input_dict = extract_inputs(soup, url_query)
    url_query.update(input_dict)

    search_url = _base_url + '/E01EW/download?' + '&'.join("{}={}".format(k, v) for k, v in url_query.items())
    url_request.append(search_url)
    resp, zip_stream, resp_type = call(cntlr, search_url, url_opener, 'd - Download Zipfile Request')
    if resp_type != 'zip':
        cntlr.addToLog("Did not get zip file from request for EDINET code {}.\n{}".format(edinet_code, _a_url))
        return

    if _debug:
        cntlr.addToLog("URL Requests\n",
                       '\n'.join(url_request))

    if getattr(options, 'JapanEDINETScraper_SAVE_DIR', None) is not None:
        zip_file_name = '{}.zip'.format(edinet_code)
        zip_full_file_name = os.path.join(options.JapanEDINETScraper_SAVE_DIR, zip_file_name)
        cntlr.addToLog("Saving Japan EDINET zip file {}".format(zip_full_file_name), "info")
        with open(zip_full_file_name, 'wb') as zip_out:
            zip_out.write(zip_stream)

    cntlr.addToLog("Scraping complete", "info")
    if resp_type == 'zip':
        # Add the zipfile to the controller. This is used by the database loader to extract the contents from the
        # input zip file.
        cntlr.xbrlusDB_entry_zipfile = zipfile.ZipFile(BytesIO(zip_stream))
        cntlr.run(options, BytesIO(zip_stream))


def command_line_options(parser):
    parser_group = optparse.OptionGroup(parser,
                                       "Japan EDINET Scraper",
                                       "The Japan EDINET Scraper plugin scrapes filings from the Japan EDINET "
                                       "website.")
    parser_group.add_option('--JapanEDINETScraper-code', dest='JapanEDINETScraper_EDINET_CODE',
                        help='EDINET code. A list of codes can be supplied separated by comma or pipe ("|").')

    parser_group.add_option('--JapanEDINETScraper-save-dir', dest='JapanEDINETScraper_SAVE_DIR',
                            help='Save zip files to specified directory. If this option is not used, zip files will not be saved')

    parser.add_option_group(parser_group)

def command_line_utility(cntlr, options, **kwargs):
    global _first_time
    if _first_time:
        parser = optparse.OptionParser()
        if getattr(options, 'JapanEDINETScraper_EDINET_CODE', None) is None:
            parser.error(_("--JapanEDINETScraper-code is required"))

        _first_time = False
        for edinet_code in re.split(r'\|,', options.JapanEDINETScraper_EDINET_CODE):
            scraper_main(cntlr, options, edinet_code.strip().upper())

__pluginInfo__ = {
    'name': 'Japan EDINET Scraper',
    'version': '0.9',
    'description': "This plug-in adds a feature to scrape the Japan EDINET site for filings..",
    'license': 'Apache-2',
    'author': 'XBRL US Inc.',
    'copyright': '(c) Copyright 2018 XBRL US Inc., All rights reserved.',
    'import': 'JapanEDINETLoader',
    # classes of mount points (required)
    'CntlrCmdLine.Options': command_line_options,
    'CntlrCmdLine.Utility.Run': command_line_utility,
}