
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

class TestFactset(unittest.TestCase):

    maxDiff = None
    
    
    def setUp(self):
        self.grammar = get_grammar()
    
    def test_bad_aspect_simple(self):
        self.assertRaises(pyparsing.ParseException, self.grammar.parseString, """assert abc @@@""", parseAll=True)
    
    def test_empty_factset_curly(self):
        res = self.grammar.parseString(r"""assert abc {}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]})
    
    def test_empty_factset_bar(self):
        res = self.grammar.parseString(r"""assert abc ||""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'closed'}}}}]})
    
    def test_empty_covered(self):
        res = self.grammar.parseString(r"""assert abc {covered}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'covered': True, 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]})
    
    def test_simple_aspect_curly(self):
        res = self.grammar.parseString(r"""assert abc {@}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'covered', 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]})
    
    def test_simple_aspect_no_curly(self):
        res = self.grammar.parseString(r"""assert abc @""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'covered', 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]})
    
    def test_simple_uncovered_aspect_curly(self):
        res = self.grammar.parseString(r"""assert abc{@@}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'uncovered', 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]})
    
    def test_simple_uncovered_aspect_no_curly(self):
        res = self.grammar.parseString(r"""assert abc @@""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'uncovered', 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]})
    
    def test_empty_covered_bar(self):
        res = self.grammar.parseString(r"""assert abc |covered|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'covered': True, 'factsetType': 'closed'}}}}]})
    
    def test_simple_aspect_bar(self):
        res = self.grammar.parseString(r"""assert abc |@|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'coverType': 'covered'}}], 'factsetType': 'closed'}}}}]})
    
    def test_simple_uncovered_aspect_bar(self):
        res = self.grammar.parseString(r"""assert abc |@@|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'coverType': 'uncovered'}}], 'factsetType': 'closed'}}}}]})
    
    def test_named_common_aspect(self):
        res = self.grammar.parseString(r"""assert abc @concept""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'covered', 'aspectName': 'concept', 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]})
    
    def test_named_common_aspect_upper_and_lower(self):
        res = self.grammar.parseString(r"""assert abc @coNCepT""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'covered', 'aspectName': 'concept', 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]})
    
    def test_named_default_dim_aspect(self):
        res = self.grammar.parseString(r"""assert abc @dimension""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'covered', 'aspectDimensionName': {'prefix': '*', 'localName': 'dimension', 'exprName': 'qname'}, 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]})
    
    def test_named_prefixed_dim_aspect(self):
        res = self.grammar.parseString(r"""assert abc @dim:dimension""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'covered', 'aspectDimensionName': {'prefix': 'dim', 'localName': 'dimension', 'exprName': 'qname'}, 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]})
    
    def test_named_prefixed_dim_aspect_equal(self):
        res = self.grammar.parseString(r"""assert abc @dim:dimension = block""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'body': {'aspectFilters': [{'aspectDimensionName': {'exprName': 'qname', 'localName': 'dimension', 'prefix': 'dim'}, 'aspectExpr': 'expr_stop', 'aspectOperator': '=', 'coverType': 'covered', 'exprName': 'aspectFilter'}], 'exprName': 'factset', 'factsetType': 'open'}, 'exprName': 'assertion', 'ruleName': 'abc', 'satisfactionType': 'satisfied'}]})
    
    def test_named_dim_aspect_starts_with_concept(self):
        res = self.grammar.parseString(r"""assert abc @conceptabc""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'body': {'aspectFilters': [{'aspectDimensionName': {'exprName': 'qname', 'localName': 'conceptabc', 'prefix': '*'}, 'coverType': 'covered', 'exprName': 'aspectFilter'}], 'exprName': 'factset', 'factsetType': 'open'}, 'exprName': 'assertion', 'ruleName': 'abc', 'satisfactionType': 'satisfied'}]})
    
    def test_simple_where_curly(self):
        res = self.grammar.parseString(r"""assert abc {where 1}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'body': {'exprName': 'factset', 'factsetType': 'open', 'whereExpr': {'exprName': 'integer', 'value': '1'}}, 'exprName': 'assertion', 'ruleName': 'abc', 'satisfactionType': 'satisfied'}]})
    
    def test_simple_where_bar(self):
        res = self.grammar.parseString(r"""assert abc |where 1|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'closed', 'whereExpr': {'integer': '1'}}}}}]})
    
    def test_aspect_equal(self):
        res = self.grammar.parseString(r"""assert abc @concept=block""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'body': {'aspectFilters': [{'aspectExpr': 'expr_stop', 'aspectName': 'concept', 'aspectOperator': '=', 'coverType': 'covered', 'exprName': 'aspectFilter'}], 'exprName': 'factset', 'factsetType': 'open'}, 'exprName': 'assertion', 'ruleName': 'abc', 'satisfactionType': 'satisfied'}]})
    
    def test_aspect_equal_multi(self):
        res = self.grammar.parseString(r"""assert abc @concept=block @unit=block""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'body': {'aspectFilters': [{'aspectExpr': 'expr_stop', 'aspectName': 'concept', 'aspectOperator': '=', 'coverType': 'covered', 'exprName': 'aspectFilter'}, {'aspectExpr': 'expr_stop', 'aspectName': 'unit', 'aspectOperator': '=', 'coverType': 'covered', 'exprName': 'aspectFilter'}], 'exprName': 'factset', 'factsetType': 'open'}, 'exprName': 'assertion', 'ruleName': 'abc', 'satisfactionType': 'satisfied'}]})
    
    def test_aspect_equal_with_alias(self):
        res = self.grammar.parseString(r"""assert abc @concept=block as con""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'body': {'aspectFilters': [{'alias': 'con', 'aspectExpr': 'expr_stop', 'aspectName': 'concept', 'aspectOperator': '=', 'coverType': 'covered', 'exprName': 'aspectFilter'}], 'exprName': 'factset', 'factsetType': 'open'}, 'exprName': 'assertion', 'ruleName': 'abc', 'satisfactionType': 'satisfied'}]})
    
    def test_aspect_with_alias(self):
        res = self.grammar.parseString(r"""assert abc @concept as con""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'body': {'aspectFilters': [{'alias': 'con', 'aspectName': 'concept', 'coverType': 'covered', 'exprName': 'aspectFilter'}], 'exprName': 'factset', 'factsetType': 'open'}, 'exprName': 'assertion', 'ruleName': 'abc', 'satisfactionType': 'satisfied'}]})
    
    def test_aspect_equal_with_alias_curly(self):
        res = self.grammar.parseString(r"""assert abc {@concept=block as con}""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'body': {'aspectFilters': [{'alias': 'con', 'aspectExpr': 'expr_stop', 'aspectName': 'concept', 'aspectOperator': '=', 'coverType': 'covered', 'exprName': 'aspectFilter'}], 'exprName': 'factset', 'factsetType': 'open'}, 'exprName': 'assertion', 'ruleName': 'abc', 'satisfactionType': 'satisfied'}]})
    
    def test_aspect_with_alias_curly(self):
        res = self.grammar.parseString(r"""assert abc {@concept as con}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'body': {'aspectFilters': [{'alias': 'con', 'aspectName': 'concept', 'coverType': 'covered', 'exprName': 'aspectFilter'}], 'exprName': 'factset', 'factsetType': 'open'}, 'exprName': 'assertion', 'ruleName': 'abc', 'satisfactionType': 'satisfied'}]})
    
    def test_aspect_equal_with_alias_bar(self):
        res = self.grammar.parseString(r"""assert abc |@concept=block as con|""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'aspectExpr': 'expr_stop', 'aspectName': 'concept', 'aspectOperator': '=', 'coverType': 'covered', 'alias': 'con'}}], 'factsetType': 'closed'}}}}]})
    
    def test_aspect_with_alias_bar(self):
        res = self.grammar.parseString(r"""assert abc |@concept as con|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'aspectName': 'concept', 'coverType': 'covered', 'alias': 'con'}}], 'factsetType': 'closed'}}}}]})
    
    def test_factset_expr(self):
        res = self.grammar.parseString(r"""assert abc {4}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'body': {'exprName': 'factset', 'factsetType': 'open', 'innerExpr': {'exprName': 'integer', 'value': '4'}}, 'exprName': 'assertion', 'ruleName': 'abc', 'satisfactionType': 'satisfied'}]})
    
    def test_factset_expr_where(self):
        res = self.grammar.parseString(r"""assert abc {4 where  5}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'whereExpr': {'integer': '5'}, 'innerExpr': {'integer': '4'}}}}}]})
    
    def test_factset_expr_aspect_where(self):
        res = self.grammar.parseString(r"""assert abc {@Assets 4 where  5}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open', 'whereExpr': {'integer': '5'}, 'innerExpr': {'integer': '4'}, 'aspectFilters': [{'aspectFilter': {'aspectDimensionName': {'localName': 'Assets', 'prefix': '*'}, 'coverType': 'covered'}}]}}}}]})
    
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
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'functionReference': {'functionName': 'xyz', 'functionArgs': []}}}}]})
    
    def test_function_reference_one_args(self):
        res = self.grammar.parseString(r"""assert abc xyz(1)""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'functionReference': {'functionName': 'xyz', 'functionArgs': [{'integer': '1'}]}}}}]})
    
    def test_function_reference_two_args(self):
        res = self.grammar.parseString(r'''assert abc xyz(1,"arg1")''', parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'functionReference': {'functionName': 'xyz', 'functionArgs': [{'integer': '1'}, {'string': '"arg1"'}]}}}}]})
    
    def test_function_reference_nested(self):
        res = self.grammar.parseString(r"""assert abc xyz(1,zzz(5))""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'functionReference': {'functionName': 'xyz', 'functionArgs': [{'integer': '1'}, {'functionReference': {'functionName': 'zzz', 'functionArgs': [{'integer': '5'}]}}]}}}}]})
    
class TestLiterals(unittest.TestCase):

    maxDiff = None
    
    
    def setUp(self):
        self.grammar = get_grammar()
    
    def test_integer(self):
        res = self.grammar.parseString(r"""assert abc 1""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': '1', 'exprName': 'integer'}, 'exprName': 'assertion'}]})
    
    def test_integer_negative(self):
        res = self.grammar.parseString(r"""assert abc -1""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'op': '-', 'expr': {'value': '1', 'exprName': 'integer'}, 'exprName': 'unaryExpr'}, 'exprName': 'assertion'}]})
    
    def test_integer_postive(self):
        res = self.grammar.parseString(r"""assert abc +3""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': '+3', 'exprName': 'integer'}, 'exprName': 'assertion'}]})
    
    def test_float(self):
        res = self.grammar.parseString(r"""assert abc 2.3""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': '2.3', 'exprName': 'float'}, 'exprName': 'assertion'}]})
    
    def test_float_scientific_notation(self):
        res = self.grammar.parseString(r"""assert abc 3.4e2""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': '3.4e2', 'exprName': 'float'}, 'exprName': 'assertion'}]})
    
    def test_float_scientific_notation_negative_e(self):
        res = self.grammar.parseString(r"""assert abc 3.4e-12""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': '3.4e-12', 'exprName': 'float'}, 'exprName': 'assertion'}]})
    
    def test_float_negative_scientific_notation(self):
        res = self.grammar.parseString(r"""assert abc -3.4e2""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'op': '-', 'expr': {'value': '3.4e2', 'exprName': 'float'}, 'exprName': 'unaryExpr'}, 'exprName': 'assertion'}]})
    
    def test_float_postive_scientific_notation(self):
        res = self.grammar.parseString(r"""assert abc +3.4e2""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'op': '+', 'expr': {'value': '3.4e2', 'exprName': 'float'}, 'exprName': 'unaryExpr'}, 'exprName': 'assertion'}]})
    
    def test_float_postive_scientific_notation_negative_e(self):
        res = self.grammar.parseString(r"""assert abc +3.4e-22""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'op': '+', 'expr': {'value': '3.4e-22', 'exprName': 'float'}, 'exprName': 'unaryExpr'}, 'exprName': 'assertion'}]})
    
    def test_float_postive_scientific_notation_positive_e(self):
        res = self.grammar.parseString(r"""assert abc +3.4e+9""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'op': '+', 'expr': {'value': '3.4e+9', 'exprName': 'float'}, 'exprName': 'unaryExpr'}, 'exprName': 'assertion'}]})
    
    def test_float_infinite(self):
        res = self.grammar.parseString(r"""assert abc inf""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': 'INF', 'exprName': 'float'}, 'exprName': 'assertion'}]})
    
    def test_float_postitive_infinite(self):
        res = self.grammar.parseString(r"""assert abc +inf""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'float': '+INF'}}}]})
    
    def test_float_negative_infinite(self):
        res = self.grammar.parseString(r"""assert abc -inf""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'float': '-INF'}}}]})
    
    def test_float_infinite_mixed_case(self):
        res = self.grammar.parseString(r"""assert abc iNF""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'float': 'INF'}}}]})
    
    def test_string_single_quote(self):
        res = self.grammar.parseString(r"""assert abc 'abc'""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'string': "'abc'"}}}]})
    
    def test_string_double_quote(self):
        res = self.grammar.parseString(r'''assert abc "abc"''', parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'string': '"abc"'}}}]})
    
    def test_string_single_quote_escaped(self):
        res = self.grammar.parseString(r"""assert abc 'a\'bc'""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'string': "'a\\'bc'"}}}]})
    
    def test_string_double_quote_escaped(self):
        res = self.grammar.parseString(r'''assert abc "ab\"c"''', parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'string': '"ab\\"c"'}}}]})
    
    def test_qname_no_prefix(self):
        res = self.grammar.parseString(r"""assert abc hello""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'qname': {'localName': 'hello', 'prefix': '*'}}}}]})
    
    def test_qname_with_prefix(self):
        res = self.grammar.parseString(r"""assert abc pre:hello""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'qname': {'localName': 'hello', 'prefix': 'pre'}}}}]})
    
    def test_severity_literal_error(self):
        res = self.grammar.parseString(r"""assert abc error""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'severity': 'error'}}}]})
    
    def test_severity_literal_warning(self):
        res = self.grammar.parseString(r"""assert abc warning""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'severity': 'warning'}}}]})
    
    def test_severity_literal_info(self):
        res = self.grammar.parseString(r"""assert abc info""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'severity': 'info'}}}]})
    
    def test_severity_literal_pass(self):
        res = self.grammar.parseString(r"""assert abc pass""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'severity': 'pass'}}}]})
    
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
    