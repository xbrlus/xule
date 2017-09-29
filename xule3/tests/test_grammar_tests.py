
import unittest
import sys
import pyparsing
sys.path.append('..')
from xule_grammar4 import get_grammar

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

class TestFactset(unittest.TestCase):

    maxDiff = None
    
    
    def setUp(self):
        self.grammar = get_grammar()
    
    def test_bad_aspect_simple(self):
        self.assertRaises(pyparsing.ParseException, self.grammar.parseString, """assert abc @@@""", parseAll=True)
    
    def test_empty_factset_curly(self):
        res = self.grammar.parseString(r"""assert abc {}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open'}}, 'ruleName': 'abc'}}]})
    
    def test_empty_factset_bar(self):
        res = self.grammar.parseString(r"""assert abc ||""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'closed'}}, 'ruleName': 'abc'}}]})
    
    def test_empty_covered(self):
        res = self.grammar.parseString(r"""assert abc {covered}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'covered': True, 'factsetType': 'open'}}, 'ruleName': 'abc'}}]})
    
    def test_simple_aspect_curly(self):
        res = self.grammar.parseString(r"""assert abc {@}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_simple_aspect_no_curly(self):
        res = self.grammar.parseString(r"""assert abc @""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_simple_uncovered_aspect_curly(self):
        res = self.grammar.parseString(r"""assert abc{@@}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'uncovered'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_simple_uncovered_aspect_no_curly(self):
        res = self.grammar.parseString(r"""assert abc @@""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'uncovered'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_empty_covered_bar(self):
        res = self.grammar.parseString(r"""assert abc |covered|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'covered': True, 'factsetType': 'closed'}}, 'ruleName': 'abc'}}]})
    
    def test_simple_aspect_bar(self):
        res = self.grammar.parseString(r"""assert abc |@|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'closed', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_simple_uncovered_aspect_bar(self):
        res = self.grammar.parseString(r"""assert abc |@@|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'closed', 'aspectFilters': [{'aspectFilter': {'coverType': 'uncovered'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_named_common_aspect(self):
        res = self.grammar.parseString(r"""assert abc @concept""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectName': 'concept'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_named_common_aspect_upper_and_lower(self):
        res = self.grammar.parseString(r"""assert abc @coNCepT""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectName': 'concept'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_named_default_dim_aspect(self):
        res = self.grammar.parseString(r"""assert abc @dimension""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectDimensionName': {'localName': 'dimension', 'prefix': '*'}}}]}}, 'ruleName': 'abc'}}]})
    
    def test_named_prefixed_dim_aspect(self):
        res = self.grammar.parseString(r"""assert abc @dim:dimension""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectDimensionName': {'localName': 'dimension', 'prefix': 'dim'}}}]}}, 'ruleName': 'abc'}}]})
    
    def test_named_prefixed_dim_aspect_equal(self):
        res = self.grammar.parseString(r"""assert abc @dim:dimension = block""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'aspectExpr': 'expr_stop', 'coverType': 'covered', 'aspectDimensionName': {'localName': 'dimension', 'prefix': 'dim'}, 'aspectOperator': '='}}]}}, 'ruleName': 'abc'}}]})
    
    def test_named_dim_aspect_starts_with_concept(self):
        res = self.grammar.parseString(r"""assert abc @conceptabc""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectDimensionName': {'localName': 'conceptabc', 'prefix': '*'}}}]}}, 'ruleName': 'abc'}}]})
    
    def test_simple_where_curly(self):
        res = self.grammar.parseString(r"""assert abc {where 1}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'whereExpr': {'integer': '1'}, 'factsetType': 'open'}}, 'ruleName': 'abc'}}]})
    
    def test_simple_where_bar(self):
        res = self.grammar.parseString(r"""assert abc |where 1|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'whereExpr': {'integer': '1'}, 'factsetType': 'closed'}}, 'ruleName': 'abc'}}]})
    
    def test_aspect_equal(self):
        res = self.grammar.parseString(r"""assert abc @concept=block""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectOperator': '=', 'aspectExpr': 'expr_stop', 'aspectName': 'concept'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_aspect_equal_multi(self):
        res = self.grammar.parseString(r"""assert abc @concept=block @unit=block""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectOperator': '=', 'aspectExpr': 'expr_stop', 'aspectName': 'concept'}}, {'aspectFilter': {'coverType': 'covered', 'aspectOperator': '=', 'aspectExpr': 'expr_stop', 'aspectName': 'unit'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_aspect_equal_with_alias(self):
        res = self.grammar.parseString(r"""assert abc @concept=block as con""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectOperator': '=', 'aspectExpr': 'expr_stop', 'alias': 'con', 'aspectName': 'concept'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_aspect_with_alias(self):
        res = self.grammar.parseString(r"""assert abc @concept as con""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'alias': 'con', 'coverType': 'covered', 'aspectName': 'concept'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_aspect_equal_with_alias_curly(self):
        res = self.grammar.parseString(r"""assert abc {@concept=block as con}""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectOperator': '=', 'aspectExpr': 'expr_stop', 'alias': 'con', 'aspectName': 'concept'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_aspect_with_alias_curly(self):
        res = self.grammar.parseString(r"""assert abc {@concept as con}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'alias': 'con', 'coverType': 'covered', 'aspectName': 'concept'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_aspect_equal_with_alias_bar(self):
        res = self.grammar.parseString(r"""assert abc |@concept=block as con|""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'closed', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectOperator': '=', 'aspectExpr': 'expr_stop', 'alias': 'con', 'aspectName': 'concept'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_aspect_with_alias_bar(self):
        res = self.grammar.parseString(r"""assert abc |@concept as con|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'closed', 'aspectFilters': [{'aspectFilter': {'alias': 'con', 'coverType': 'covered', 'aspectName': 'concept'}}]}}, 'ruleName': 'abc'}}]})
    
    def test_factset_expr(self):
        res = self.grammar.parseString(r"""assert abc {4}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'innerExpr': {'integer': '4'}, 'factsetType': 'open'}}, 'ruleName': 'abc'}}]})
    
    def test_factset_expr_where(self):
        res = self.grammar.parseString(r"""assert abc {4 where  5}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'innerExpr': {'integer': '4'}, 'whereExpr': {'integer': '5'}, 'factsetType': 'open'}}, 'ruleName': 'abc'}}]})
    
    def test_factset_expr_aspect_where(self):
        res = self.grammar.parseString(r"""assert abc {@Assets 4 where  5}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'factset': {'innerExpr': {'integer': '4'}, 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectDimensionName': {'localName': 'Assets', 'prefix': '*'}}}], 'whereExpr': {'integer': '5'}, 'factsetType': 'open'}}, 'ruleName': 'abc'}}]})
    
    def test_no_aspect_name_with_alias(self):
        self.assertRaises(pyparsing.ParseException, self.grammar.parseString, """assert abc @ as asp""", parseAll=True)
    
    def test_no_aspect_name_with_alias_curly(self):
        self.assertRaises(pyparsing.ParseException, self.grammar.parseString, """assert abc {@ as asp}""", parseAll=True)
    
    def test_no_aspect_name_with_alias_bar(self):
        self.assertRaises(pyparsing.ParseException, self.grammar.parseString, """assert abc |@ as asp|""", parseAll=True)
    
class TestFunctions(unittest.TestCase):

    maxDiff = None
    
    
    def setUp(self):
        self.grammar = get_grammar()
    
    def test_function_reference_no_args(self):
        res = self.grammar.parseString(r"""assert abc xyz()""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'functionReference': {'functionName': 'xyz', 'functionArgs': []}}, 'ruleName': 'abc'}}]})
    
    def test_function_reference_one_args(self):
        res = self.grammar.parseString(r"""assert abc xyz(1)""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'functionReference': {'functionName': 'xyz', 'functionArgs': [{'integer': '1'}]}}, 'ruleName': 'abc'}}]})
    
    def test_function_reference_two_args(self):
        res = self.grammar.parseString(r'''assert abc xyz(1,"arg1")''', parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'functionReference': {'functionName': 'xyz', 'functionArgs': [{'integer': '1'}, {'string': '"arg1"'}]}}, 'ruleName': 'abc'}}]})
    
    def test_function_reference_nested(self):
        res = self.grammar.parseString(r"""assert abc xyz(1,zzz(5))""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'functionReference': {'functionName': 'xyz', 'functionArgs': [{'integer': '1'}, {'functionReference': {'functionName': 'zzz', 'functionArgs': [{'integer': '5'}]}}]}}, 'ruleName': 'abc'}}]})
    
class TestLiterals(unittest.TestCase):

    maxDiff = None
    
    
    def setUp(self):
        self.grammar = get_grammar()
    
    def test_integer(self):
        res = self.grammar.parseString(r"""assert abc 1""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'integer': '1'}, 'ruleName': 'abc'}}]})
    
    def test_integer_negative(self):
        res = self.grammar.parseString(r"""assert abc -1""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'integer': '-1'}, 'ruleName': 'abc'}}]})
    
    def test_integer_postive(self):
        res = self.grammar.parseString(r"""assert abc +3""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'integer': '+3'}, 'ruleName': 'abc'}}]})
    
    def test_float(self):
        res = self.grammar.parseString(r"""assert abc 2.3""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'float': '2.3'}, 'ruleName': 'abc'}}]})
    
    def test_float_scientific_notation(self):
        res = self.grammar.parseString(r"""assert abc 3.4e2""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'float': '3.4e2'}, 'ruleName': 'abc'}}]})
    
    def test_float_scientific_notation_negative_e(self):
        res = self.grammar.parseString(r"""assert abc 3.4e-12""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'float': '3.4e-12'}, 'ruleName': 'abc'}}]})
    
    def test_float_negative_scientific_notation(self):
        res = self.grammar.parseString(r"""assert abc -3.4e2""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'float': '-3.4e2'}, 'ruleName': 'abc'}}]})
    
    def test_float_postive_scientific_notation(self):
        res = self.grammar.parseString(r"""assert abc +3.4e2""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'float': '+3.4e2'}, 'ruleName': 'abc'}}]})
    
    def test_float_postive_scientific_notation_negative_e(self):
        res = self.grammar.parseString(r"""assert abc +3.4e-22""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'float': '+3.4e-22'}, 'ruleName': 'abc'}}]})
    
    def test_float_postive_scientific_notation_positive_e(self):
        res = self.grammar.parseString(r"""assert abc +3.4e+9""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'float': '+3.4e+9'}, 'ruleName': 'abc'}}]})
    
    def test_float_infinite(self):
        res = self.grammar.parseString(r"""assert abc inf""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'float': 'INF'}, 'ruleName': 'abc'}}]})
    
    def test_float_postitive_infinite(self):
        res = self.grammar.parseString(r"""assert abc +inf""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'float': '+INF'}, 'ruleName': 'abc'}}]})
    
    def test_float_negative_infinite(self):
        res = self.grammar.parseString(r"""assert abc -inf""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'float': '-INF'}, 'ruleName': 'abc'}}]})
    
    def test_float_infinite_mixed_case(self):
        res = self.grammar.parseString(r"""assert abc iNF""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'float': 'INF'}, 'ruleName': 'abc'}}]})
    
    def test_string_single_quote(self):
        res = self.grammar.parseString(r"""assert abc 'abc'""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'string': "'abc'"}, 'ruleName': 'abc'}}]})
    
    def test_string_double_quote(self):
        res = self.grammar.parseString(r'''assert abc "abc"''', parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'string': '"abc"'}, 'ruleName': 'abc'}}]})
    
    def test_string_single_quote_escaped(self):
        res = self.grammar.parseString(r"""assert abc 'a\'bc'""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'string': "'a\\'bc'"}, 'ruleName': 'abc'}}]})
    
    def test_string_double_quote_escaped(self):
        res = self.grammar.parseString(r'''assert abc "ab\"c"''', parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'string': '"ab\\"c"'}, 'ruleName': 'abc'}}]})
    
    def test_qname_no_prefix(self):
        res = self.grammar.parseString(r"""assert abc hello""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'qname': {'localName': 'hello', 'prefix': '*'}}, 'ruleName': 'abc'}}]})
    
    def test_qname_with_prefix(self):
        res = self.grammar.parseString(r"""assert abc pre:hello""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'qname': {'localName': 'hello', 'prefix': 'pre'}}, 'ruleName': 'abc'}}]})
    
    def test_severity_literal_error(self):
        res = self.grammar.parseString(r"""assert abc error""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'severity': 'error'}, 'ruleName': 'abc'}}]})
    
    def test_severity_literal_warning(self):
        res = self.grammar.parseString(r"""assert abc warning""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'severity': 'warning'}, 'ruleName': 'abc'}}]})
    
    def test_severity_literal_info(self):
        res = self.grammar.parseString(r"""assert abc info""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'severity': 'info'}, 'ruleName': 'abc'}}]})
    
    def test_severity_literal_pass(self):
        res = self.grammar.parseString(r"""assert abc pass""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'satisfactionType': 'satisfied', 'body': {'severity': 'pass'}, 'ruleName': 'abc'}}]})
    
class TestNotes(unittest.TestCase):

    maxDiff = None
    
    
    def setUp(self):
        self.grammar = get_grammar()
    
    def test_notes(self):
        self.fail("""
Need test for navigate and all its permutations.
Need tests for assertion results.
Need tests for qnames.
Need tests for severity literals.
Need tests for function reference.
Need tests for variable reference.
Need tests for if and else if expressions.
Need tests for for (with and without parens).
Need tests for list literals.
Need tests for namespaces declarations.
Neet tests for constants.
Neet tests for output rules.
Need tests for function declarations (include tags with and without tag names).
  """)
    
class TestVariables(unittest.TestCase):

    maxDiff = None
    
    
    def setUp(self):
        self.grammar = get_grammar()
    