
import unittest
import sys
import pyparsing
#sys.path.append('..')
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
        res = self.grammar.parseString("""assert abc {}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open'}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_empty_factset_bar(self):
        res = self.grammar.parseString("""assert abc ||""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'closed'}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_empty_covered(self):
        res = self.grammar.parseString("""assert abc {covered}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'covered': True}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_simple_aspect_curly(self):
        res = self.grammar.parseString("""assert abc {@}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_simple_aspect_no_curly(self):
        res = self.grammar.parseString("""assert abc @""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_simple_uncovered_aspect_curly(self):
        res = self.grammar.parseString("""assert abc{@@}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'uncovered'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_simple_uncovered_aspect_no_curly(self):
        res = self.grammar.parseString("""assert abc @@""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'uncovered'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_empty_covered_bar(self):
        res = self.grammar.parseString("""assert abc |covered|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'closed', 'covered': True}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_simple_aspect_bar(self):
        res = self.grammar.parseString("""assert abc |@|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'closed', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_simple_uncovered_aspect_bar(self):
        res = self.grammar.parseString("""assert abc |@@|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'closed', 'aspectFilters': [{'aspectFilter': {'coverType': 'uncovered'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_named_common_aspect(self):
        res = self.grammar.parseString("""assert abc @concept""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectName': 'concept'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_named_common_aspect_upper_and_lower(self):
        res = self.grammar.parseString("""assert abc @coNCepT""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectName': 'concept'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_named_default_dim_aspect(self):
        res = self.grammar.parseString("""assert abc @dimension""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'aspectDimensionName': {'prefix': '*', 'localName': 'dimension'}, 'coverType': 'covered'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_named_prefixed_dim_aspect(self):
        res = self.grammar.parseString("""assert abc @dim:dimension""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'aspectDimensionName': {'prefix': 'dim', 'localName': 'dimension'}, 'coverType': 'covered'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_named_prefixed_dim_aspect_equal(self):
        res = self.grammar.parseString("""assert abc @dim:dimension = block""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'aspectExpr': 'expr_stop', 'aspectDimensionName': {'prefix': 'dim', 'localName': 'dimension'}, 'aspectOperator': '=', 'coverType': 'covered'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_named_dim_aspect_starts_with_concept(self):
        res = self.grammar.parseString("""assert abc @conceptabc""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'aspectDimensionName': {'prefix': '*', 'localName': 'conceptabc'}, 'coverType': 'covered'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_simple_where_curly(self):
        res = self.grammar.parseString("""assert abc {where 1}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'whereExpr': {'integer': '1'}}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_simple_where_bar(self):
        res = self.grammar.parseString("""assert abc |where 1|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'closed', 'whereExpr': {'integer': '1'}}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_aspect_equal(self):
        res = self.grammar.parseString("""assert abc @concept=block""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectName': 'concept', 'aspectOperator': '=', 'aspectExpr': 'expr_stop'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_aspect_equal_multi(self):
        res = self.grammar.parseString("""assert abc @concept=block @unit=block""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectName': 'concept', 'aspectOperator': '=', 'aspectExpr': 'expr_stop'}}, {'aspectFilter': {'coverType': 'covered', 'aspectName': 'unit', 'aspectOperator': '=', 'aspectExpr': 'expr_stop'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_aspect_equal_with_alias(self):
        res = self.grammar.parseString("""assert abc @concept=block as con""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectName': 'concept', 'aspectOperator': '=', 'alias': 'con', 'aspectExpr': 'expr_stop'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_aspect_with_alias(self):
        res = self.grammar.parseString("""assert abc @concept as con""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'alias': 'con', 'aspectName': 'concept'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_aspect_equal_with_alias_curly(self):
        res = self.grammar.parseString("""assert abc {@concept=block as con}""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectName': 'concept', 'aspectOperator': '=', 'alias': 'con', 'aspectExpr': 'expr_stop'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_aspect_with_alias_curly(self):
        res = self.grammar.parseString("""assert abc {@concept as con}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'alias': 'con', 'aspectName': 'concept'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_aspect_equal_with_alias_bar(self):
        res = self.grammar.parseString("""assert abc |@concept=block as con|""", parseAll=True).asDict()
        replace_expr(res,"aspectExpr")
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'closed', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'aspectName': 'concept', 'aspectOperator': '=', 'alias': 'con', 'aspectExpr': 'expr_stop'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_aspect_with_alias_bar(self):
        res = self.grammar.parseString("""assert abc |@concept as con|""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'closed', 'aspectFilters': [{'aspectFilter': {'coverType': 'covered', 'alias': 'con', 'aspectName': 'concept'}}]}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_factset_expr(self):
        res = self.grammar.parseString("""assert abc {4}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'innerExpr': {'integer': '4'}}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_factset_expr_where(self):
        res = self.grammar.parseString("""assert abc {4 where  5}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'whereExpr': {'integer': '5'}, 'innerExpr': {'integer': '4'}}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_factset_expr_aspect_where(self):
        res = self.grammar.parseString("""assert abc {@Assets 4 where  5}""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'factset': {'factsetType': 'open', 'whereExpr': {'integer': '5'}, 'aspectFilters': [{'aspectFilter': {'aspectDimensionName': {'prefix': '*', 'localName': 'Assets'}, 'coverType': 'covered'}}], 'innerExpr': {'integer': '4'}}}, 'satisfactionType': 'satisfied'}}]})
    
    def test_no_aspect_name_with_alias(self):
        self.assertRaises(pyparsing.ParseException, self.grammar.parseString, """assert abc @ as asp""", parseAll=True)
    
    def test_no_aspect_name_with_alias_curly(self):
        self.assertRaises(pyparsing.ParseException, self.grammar.parseString, """assert abc {@ as asp}""", parseAll=True)
    
    def test_no_aspect_name_with_alias_bar(self):
        self.assertRaises(pyparsing.ParseException, self.grammar.parseString, """assert abc |@ as asp|""", parseAll=True)
    
class TestLiterals(unittest.TestCase):

    maxDiff = None
    
    
    def setUp(self):
        self.grammar = get_grammar()
    
    def test_integer(self):
        res = self.grammar.parseString("""assert abc 1""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'integer': '1'}, 'satisfactionType': 'satisfied'}}]})
    
    def test_integer_negative(self):
        res = self.grammar.parseString("""assert abc -1""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'integer': '-1'}, 'satisfactionType': 'satisfied'}}]})
    
    def test_integer_postive(self):
        res = self.grammar.parseString("""assert abc +3""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'integer': '+3'}, 'satisfactionType': 'satisfied'}}]})
    
    def test_float(self):
        res = self.grammar.parseString("""assert abc 2.3""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'float': '2.3'}, 'satisfactionType': 'satisfied'}}]})
    
    def test_float_scientific_notation(self):
        res = self.grammar.parseString("""assert abc 3.4e2""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'float': '3.4e2'}, 'satisfactionType': 'satisfied'}}]})
    
    def test_float_scientific_notation_negative_e(self):
        res = self.grammar.parseString("""assert abc 3.4e-12""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'float': '3.4e-12'}, 'satisfactionType': 'satisfied'}}]})
    
    def test_float_negative_scientific_notation(self):
        res = self.grammar.parseString("""assert abc -3.4e2""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'float': '-3.4e2'}, 'satisfactionType': 'satisfied'}}]})
    
    def test_float_postive_scientific_notation(self):
        res = self.grammar.parseString("""assert abc +3.4e2""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'float': '+3.4e2'}, 'satisfactionType': 'satisfied'}}]})
    
    def test_float_postive_scientific_notation_negative_e(self):
        res = self.grammar.parseString("""assert abc +3.4e-22""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'float': '+3.4e-22'}, 'satisfactionType': 'satisfied'}}]})
    
    def test_float_postive_scientific_notation_positive_e(self):
        res = self.grammar.parseString("""assert abc +3.4e+9""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'float': '+3.4e+9'}, 'satisfactionType': 'satisfied'}}]})
    
    def test_float_infinite(self):
        res = self.grammar.parseString("""assert abc inf""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'float': 'INF'}, 'satisfactionType': 'satisfied'}}]})
    
    def test_float_postitive_infinite(self):
        res = self.grammar.parseString("""assert abc +inf""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'float': '+INF'}, 'satisfactionType': 'satisfied'}}]})
    
    def test_float_negative_infinite(self):
        res = self.grammar.parseString("""assert abc -inf""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'float': '-INF'}, 'satisfactionType': 'satisfied'}}]})
    
    def test_float_infinite_mixed_case(self):
        res = self.grammar.parseString("""assert abc iNF""", parseAll=True).asDict()
        
        self.assertEqual(res, {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'expr': {'float': 'INF'}, 'satisfactionType': 'satisfied'}}]})
    
class TestNotes(unittest.TestCase):

    maxDiff = None
    
    
    def setUp(self):
        self.grammar = get_grammar()
    
    def test_notes(self):
        self.fail("""
Need test for navigate and all its permutations.
Need tests for assertion results.
Need tests for string literals - include escaping.
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
    