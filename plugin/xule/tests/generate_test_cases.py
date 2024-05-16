import sys
import uuid
sys.path.append('..')
from xule_grammar3 import get_grammar
import argparse
import importlib
import os.path

aparser = argparse.ArgumentParser()
aparser.add_argument("-f", required=True, help="File of tests.")
args = aparser.parse_args()

if __name__ == '__main__':
    """Dynamically build the unit tests.
    
    The unit test are build from a test file. The test file contains a variable for each group of unit tests. The variable name
    is used as part of the test case class name. The content of the variable is a tuple of tuples. Each inner tuple contains:
    1 - test case name
    2 - test string
    3 - expected result of parsing as a dictionary
    
    """
    
    test_suite = '''
import unittest
import sys
import pyparsing
sys.path.append('..')
from xule_grammar3 import get_grammar

def replace_expr(col, expr_type):
    """Replaces expression in the parse tree with 'expr'
    
    col: iterable collection
    expr_type: string possible values are 'all', 'expr', 'whereExpr', 'aspectExpr'
    """
    
    if isinstance(col, dict):
        for k in col:
            if k == expr_type or (expr_type == 'all' and k in ('expr', 'whereExpr', 'aspectExpr')):
                col[k] = 'expr_stop'
        children = col.values()
    elif isinstance(col, list) or isinstance(col, set):
        children = col
    else:
        return
    
    for child in children:
        replace_expr(child, expr_type)
'''
                     
    test_class_model = '''
class Test{class_name}(unittest.TestCase):

    maxDiff = None
    
    '''
    
    set_up_model = '''
    def setUp(self):
        self.grammar = get_grammar()
    '''
    
    test_model_equal = '''
    def test_{test_name}(self):
        res = self.grammar.parseString({test_string}, parseAll=True).asDict()
        {replace_expr}
        self.assertEqual(res, {expected})
    '''

    test_model_parse_exception = '''
    def test_{test_name}(self):
        self.assertRaises(pyparsing.ParseException, self.grammar.parseString, """{test_string}""", parseAll=True)
    '''
    
    test_model_dup_name = '''
    def test_{test_name}(self):
        self.fail('Duplicate test name')
    '''
    
    test_model_note = '''
    def test_{test_name}(self):
        self.fail("""{note}""")
    '''
    
    
    tests_name = os.path.splitext(os.path.basename(args.f))[0]
    if not os.path.isfile(tests_name + '.py'):
        raise FileNotFoundError("{}.py not found".format(tests_name))
    try:
        tests = importlib.import_module(tests_name)
        #import tests2 as tests #test are in file tests.py 
    except ImportError:
        print('{} file not found.'.format(args.f))
        raise
    
        
    for test_group in dir(tests):
        if not test_group.startswith('__'):
            processed_tests = set()
            
            test_class = test_class_model.format(class_name=test_group) + set_up_model
            
            #for test_name, test_string, expected_result in getattr(tests, test_group):
            for test in getattr(tests, test_group):
                test_name = test['name']
                if test_name in processed_tests:
                    print('Test {test_name} is a duplicate name'.format(test_name=test_name))
                    test_name += '_' + uuid.uuid4().hex
                    test_class += test_model_dup_name.format(test_name=test_name)
        
                if 'note' in test:
                    test_class += test_model_note.format(test_name=test_name, note=test['note'])
                else:
                    test_string = test['expr']
                    expected_result = test['result']

                    if expected_result is None:
                        test_class += test_model_parse_exception.format(test_name=test_name, test_string=test_string)
                    else:
                        if 'expr_stop' in test:
                            replace_expr = 'replace_expr(res,"' + test['expr_stop'] + '")'
                        else:
                            replace_expr = ''
                        if '"' in test_string:
                            quotes = "'''"
                        else:
                            quotes = '"""'
                        test_class += test_model_equal.format(test_name=test_name, test_string='r'+quotes+test_string+quotes, expected=expected_result, replace_expr=replace_expr)
                
                processed_tests.add(test_name)
            test_suite += test_class
    
    output_file_name = 'test_{}.py'.format(tests_name)
    with open(output_file_name, 'w') as o:
        print('writing:', output_file_name)
        o.write(test_suite)      
    
