"""
Compare test output results from Xule tests to expected output.

The output files are XML. There may be multiple test output and expected output files. This process collates the test
output files into a single set of messages to compare to the expected result. Likewise, there may be multiple expected
result files. These are collated into a single set of messages for the comparison.

Test output and expected results may not be in the same order. Some messages may contain runtime information (timestamps).

The return of this script is 0 for all messages match and 1 if messages do not match.
"""

import argparse
import collections
import copy
import csv
import html
import os
import re
import sys
import tabulate
import xml.etree.ElementTree as ET

def options():
    """
    Set up arguments.
    :return: None
    """
    parser = argparse.ArgumentParser(description='Xule test compare utility.')
    parser.add_argument('--test-files', dest='test_files', required=True,
                        help="List of test result XML files. File names are separated by a comma.")
    parser.add_argument('--expected-results', dest='expected_results', required=True,
                        help="List of expected result files. File names are separated by a comma.")
    parser.add_argument('--compare-file', dest='compare_file',
                        help='File name of text version of compare results.')
    parser.add_argument('--html-file', dest='html_file',
                        help='File name of html version of compare results')

    args = parser.parse_args()

    return args

def combine_results(file_names):
    """
    Combine result files into a single list of messages. This will also filter messages and sort them into a
    canonical list.

    :param file_names: List of file names separated by a comma.
    :return: List of messages
    """
    messages = collections.defaultdict(list)
    xml_docs = open_files(file_names)
    for xml_doc in xml_docs:
        for entry in xml_doc[0].findall('entry'):
            if entry.get('code','').startswith('DQC'):
                messages[message_key(entry)].append((entry, xml_doc[1]))
    return messages

def message_key(entry):
    """Create the key that will be used for the comparison"""

    message = re.sub('Rule version:.*$','',getattr(entry.find('message'), 'text',''), flags=re.I|re.S) # Remove Rule Version
    message = re.sub('\s','',message) # Remove all spaces
    # Sort the characters of the message. This will resolve issues when parts of the message come out in different orders
    message = "".join(sorted(message))

    return (entry.get('code'), entry.get('level'), message) #, tuplize(entry.find('ref')))

def tuplize(node):
    """Convert an XML element to a tuple structure

    The tuple structure has 2 items.
        1: tuple of attributes (name/value pairs in a tuple
        2: tuple of children
    :param node: Element
    :return: tuple
    """
    if node is None:
        return None
    else:
        return (
                 tuple((aname, node.get(aname)) for aname in sorted(node.keys())),
                 tuple(tuplize(child) for child in node)
                )

def open_files(file_names):
    """
    Open list of files and create a list of XML documents.
    :param file_names: List of file names separated by a comma.
    :return: List of XML documents
    """
    xml_docs = []
    for file_name in file_names.split(','):
        print("Opening file:", file_name.strip())
        with open(file_name.strip(), 'r') as f:
            xml_doc = ET.fromstring(f.read())
            xml_docs.append((xml_doc, file_name.strip()))

    return xml_docs

def compare(test_messages, expected_messages):
    """Compare generated test messages to expected results.

    :param test_messages: Dictionary of messages
    :param expected_messages: Dictionary of messages
    :return:
    """
    report = []
    headers = ['code', 'severity', 'message', 'test file', 'test count', 'expected file', 'expected count', 'key message']
    all_keys = test_messages.keys() | expected_messages.keys()
    for key in sorted(all_keys):
        test_count = len(test_messages.get(key,tuple()))
        expected_count = len(expected_messages.get(key, tuple()))
        if test_count != expected_count:
            # This is a difference
            base_message = (test_messages[key] if key in test_messages else expected_messages[key])[0]
            report.append([key[0],
                           base_message[0].get('level'),
                           base_message[0].find('message').text,
                           os.path.split(test_messages[key][0][1] if key in test_messages else '')[1], # file name
                           test_count,
                           os.path.split(expected_messages[key][0][1] if key in expected_messages else '')[1], # file name
                           expected_count,
                           key[2]
                          ])
    if len(report) > 0:
        return [headers, *report]
    else:
        return None

def split_string(s, size):
    """Split a string into lines based on a fixed size."""
    def _split_string(s, size):
        for pos in range(0, len(s), size):
            yield s[pos:pos+size]

    # Split the string on new lines and then split on size
    splits = ['\n'.join(_split_string(x, size)) for x in s.split('\n')]

    return '\n'.join(splits)

def write_table_report(report, args):
    """Write report as a tabulate text file"""
    if report is not None:
        # Fix long strings in the table. Tabulate does not wrap text in a cell. So the long text is pre split with newlines
        # using split_string()
        tab_report = []
        for row in report:
            tab_row = copy.copy(row)
            tab_row[2] = split_string(tab_row[2], 30)
            tab_row[7] = split_string(tab_row[7], 30)
            tab_report.append(tab_row)

        report_table = tabulate.tabulate(tab_report, headers='firstrow', tablefmt='grid')
        if args.compare_file is None:
            print(report_table)
        else:
            with open(args.compare_file, 'w') as o:
                o.write(report_table)    

def write_html_report(report, args):
    """Write report as an html file"""
    # Only write the report if the html_file argument was used
    if report is not None:
        if args.html_file is not None:
            html_start = """<html><head><style>
    table {
        border-collapse: collapse;
    }

    table, th, td {
        border: 1px solid black;
    }
            </style></head><body><table>"""
            html_end = '</table></body></html>'

            table = ''
            # First row has headers
            table += '<tr>' + ''.join(['<th>' + html.escape(x) + '</th>' for x in report[0]]) + '</tr>'
            for row in report[1:]:
                table += '<tr>'
                for i in range(len(row)):
                    if i == 7:
                        val = html.escape(split_string(row[i], 30))
                    else:
                        val = html.escape(str(row[i]))
                    table += "<td valign='top'>" +  val + "</td>" 
                table += '</tr>'


            with open(args.html_file.strip(), 'w') as h:
                h.write(html_start + table + html_end)

if __name__ == '__main__':
    args = options()
    test_messages = combine_results(args.test_files)
    expected_messages = combine_results(args.expected_results)
    report = compare(test_messages, expected_messages)
    if report is None:
        print('No differences')
    write_table_report(report, args)
    write_html_report(report, args)
    if report is None:
        sys.exit(0)
    else:
        sys.exit(1)

