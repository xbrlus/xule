"""
The test file contains a variable for each group of unit tests. The variable name
is used as part of the test case class name. The content of the variable is a tuple of dictionaries. Each dictionary requires:
    name: test case name
    expr: test string
    result: expected result of parsing as a dictionary. If None, then a parse error is expected.
Optional keys are:
    expr_stop: possible values are 'all', 'expr', 'whereExpr', 'aspectExpr'
                This will convert these expressions to the string 'expr'
"""    

Factset = (
 {'name': 'bad_aspect_simple',
  'expr': 'assert abc @@@',
  'result': None
 }
,{'name': 'empty_factset_curly',
  'expr': 'assert abc {}',
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open'}}}}]}
 }
,{'name': 'empty_factset_bar',
  'expr': 'assert abc ||',
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'closed'}}}}]}
 }
,{'name': 'empty_covered',
  'expr': 'assert abc {covered}',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'covered': True,
                          'factsetType': 'open'}}}}]}
 }
,{'name': 'simple_aspect_curly',
  'expr': 'assert abc {@}',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'coverType': 'covered'}}],
                          'factsetType': 'open'}}}}]}
 }
,{'name': 'simple_aspect_no_curly',
  'expr': 'assert abc @',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body':{'factset': {'aspectFilters': [{'aspectFilter': {'coverType': 'covered'}}],
                                     'factsetType': 'open'}}}}]}
 }
,{'name': 'simple_uncovered_aspect_curly',
  'expr': 'assert abc{@@}',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'coverType': 'uncovered'}}],
                                     'factsetType': 'open'}}}}]}
 }
,{'name': 'simple_uncovered_aspect_no_curly',
  'expr': 'assert abc @@',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'coverType': 'uncovered'}}],
                                     'factsetType': 'open'}}}}]}
 }
,{'name': 'empty_covered_bar',
  'expr': 'assert abc |covered|',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'covered': True,
                                     'factsetType': 'closed'}}}}]}
 }
,{'name': 'simple_aspect_bar',
  'expr': 'assert abc |@|',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'coverType': 'covered'}}],
                                     'factsetType': 'closed'}}}}]}
 }
,{'name': 'simple_uncovered_aspect_bar',
  'expr': 'assert abc |@@|',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'coverType': 'uncovered'}}],
                                     'factsetType': 'closed'}}}}]}
 }
,{'name': 'named_common_aspect',
  'expr': 'assert abc @concept',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'aspectName': 'concept',
                                                                         'coverType': 'covered'}}],
                                     'factsetType': 'open'}}}}]}
 }
,{'name': 'named_common_aspect_upper_and_lower',
  'expr': 'assert abc @coNCepT',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'aspectName': 'concept',
                                                                         'coverType': 'covered'}}],
                                     'factsetType': 'open'}}}}]}
 }           
,{'name': 'named_default_dim_aspect',
  'expr': 'assert abc @dimension',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'aspectDimensionName': {'localName':'dimension',
                                                                                      'prefix':'*'},
                                                                         'coverType': 'covered'}}],
                                     'factsetType': 'open'}}}}]}
 }          
,{'name': 'named_prefixed_dim_aspect',
  'expr': 'assert abc @dim:dimension',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body':{'factset': {'aspectFilters': [{'aspectFilter': {'aspectDimensionName': {'localName':'dimension',
                                                                                      'prefix':'dim'},
                                                                         'coverType': 'covered'}}],
                                     'factsetType': 'open'}}}}]}
 }                    
,{'name': 'named_prefixed_dim_aspect_equal',
  'expr': 'assert abc @dim:dimension = block',
  'expr_stop':'aspectExpr',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'aspectDimensionName': {'localName':'dimension',
                                                                                      'prefix':'dim'},
                                                              'coverType': 'covered',
                                                              'aspectOperator':'=',
                                                              'aspectExpr': 'expr_stop'}}],
                                     'factsetType': 'open'}}}}]}
 } 
,{'name': 'named_dim_aspect_starts_with_concept',
  'expr': 'assert abc @conceptabc',
  'result': 
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'aspectDimensionName': {'localName':'conceptabc',
                                                                                      'prefix':'*'},
                                                              'coverType': 'covered'}}],
                                     'factsetType': 'open'}}}}]}         
  }
       
,{'name': 'simple_where_curly',
  'expr': 'assert abc {where 1}',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'open',
                                     'whereExpr': {'integer': '1'}}}}}]}
 }
,{'name': 'simple_where_bar',
  'expr': 'assert abc |where 1|',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'factsetType': 'closed',
                                     'whereExpr': {'integer': '1'}}}}}]}
 }
,{'name': 'aspect_equal',
  'expr': 'assert abc @concept=block',
  'expr_stop': 'aspectExpr',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body':{'factset': {'aspectFilters': [{'aspectFilter': {'aspectExpr': 'expr_stop',
                                                              'aspectName': 'concept',
                                                              'aspectOperator': '=',
                                                              'coverType': 'covered'}}],
                          'factsetType': 'open'}}}}]}
 }
,{'name': 'aspect_equal_multi',
  'expr': 'assert abc @concept=block @unit=block',
  'expr_stop': 'aspectExpr',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'aspectExpr': 'expr_stop',
                                                              'aspectName': 'concept',
                                                              'aspectOperator': '=',
                                                              'coverType': 'covered'}},
                                            {'aspectFilter': {'aspectExpr': 'expr_stop',
                                                              'aspectName': 'unit',
                                                              'aspectOperator': '=',
                                                              'coverType': 'covered'}}
                                            ],
                          'factsetType': 'open'}}}}]}
 }  
,{'name': 'aspect_equal_with_alias',
  'expr': 'assert abc @concept=block as con',
  'expr_stop': 'aspectExpr',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'aspectExpr': 'expr_stop',
                                                              'aspectName': 'concept',
                                                              'aspectOperator': '=',
                                                              'coverType': 'covered',
                                                              'alias': 'con'}
                                             }],
                          'factsetType': 'open'}}}}]}
 }
,{'name': 'aspect_with_alias',
  'expr': 'assert abc @concept as con',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'aspectName': 'concept',
                                                              'coverType': 'covered',
                                                              'alias': 'con'}
                                             }],
                          'factsetType': 'open'}}}}]}
 }
           
,{'name': 'aspect_equal_with_alias_curly',
  'expr': 'assert abc {@concept=block as con}',
  'expr_stop': 'aspectExpr',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body':{'factset': {'aspectFilters': [{'aspectFilter': {'aspectExpr': 'expr_stop',
                                                              'aspectName': 'concept',
                                                              'aspectOperator': '=',
                                                              'coverType': 'covered',
                                                              'alias': 'con'}
                                             }],
                          'factsetType': 'open'}}}}]}
 }
,{'name': 'aspect_with_alias_curly',
  'expr': 'assert abc {@concept as con}',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'aspectName': 'concept',
                                                              'coverType': 'covered',
                                                              'alias': 'con'}
                                             }],
                          'factsetType': 'open'}}}}]}
 }

,{'name': 'aspect_equal_with_alias_bar',
  'expr': 'assert abc |@concept=block as con|',
  'expr_stop': 'aspectExpr',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factset': {'aspectFilters': [{'aspectFilter': {'aspectExpr': 'expr_stop',
                                                              'aspectName': 'concept',
                                                              'aspectOperator': '=',
                                                              'coverType': 'covered',
                                                              'alias': 'con'}
                                             }],
                          'factsetType': 'closed'}}}}]}
 }
,{'name': 'aspect_with_alias_bar',
  'expr': 'assert abc |@concept as con|',
  'result':
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': 
                                {'factset': {'aspectFilters': [{'aspectFilter': {'aspectName': 'concept',
                                                              'coverType': 'covered',
                                                              'alias': 'con'}
                                             }],
                          'factsetType': 'closed'}}}}]}
 }
,{'name': 'factset_expr',
  'expr': 'assert abc {4}',
  'result': 
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 
                                'body': {'factset': {
                                                     'factsetType': 'open',
                                                     'innerExpr':
                                                     {'integer': '4'}}}}}]}  
}
,{'name': 'factset_expr_where',
  'expr': 'assert abc {4 where  5}',
  'result': 
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 
                                'body': {'factset': {
                                                     'factsetType': 'open',
                                                     'whereExpr': {'integer': '5'},
                                                     'innerExpr': {'integer': '4'}}}}}]}  
}
,{'name': 'factset_expr_aspect_where',
  'expr': 'assert abc {@Assets 4 where  5}',
  'result': 
    {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 
                                'body': {'factset': {
                                                     'factsetType': 'open',
                                                     'whereExpr': {'integer': '5'},
                                                     'innerExpr': {'integer': '4'},
                                                     
                                                     'aspectFilters': [{'aspectFilter': {'aspectDimensionName': {'localName': 'Assets',
                                                                                                                 'prefix': '*'},
                                                                                          'coverType': 'covered'}}]
                                                     }}}}]}  
}           
           
,{'name': 'no_aspect_name_with_alias',
  'expr': 'assert abc @ as asp',
  'result': None}                               

,{'name': 'no_aspect_name_with_alias_curly',
  'expr': 'assert abc {@ as asp}',
  'result': None}  
,{'name': 'no_aspect_name_with_alias_bar',
  'expr': 'assert abc |@ as asp|',
  'result': None}                                           
)

Literals = (
 {'name': 'integer',
  'expr': 'assert abc 1',
  'result':{'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'integer': '1'}}}]}
 }
,{'name': 'integer_negative',
  'expr': 'assert abc -1',
  'result':{'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'integer': '-1'}}}]}
 }
,{'name': 'integer_postive',
  'expr': 'assert abc +3',
  'result':{'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'integer': '+3'}}}]}
 }  
,{'name': 'float',
  'expr': 'assert abc 2.3',
  'result':{'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'float': '2.3'}}}]}
 }                      
,{'name': 'float_scientific_notation',
  'expr': 'assert abc 3.4e2',
  'result':{'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'float': '3.4e2'}}}]}
}
,{'name': 'float_scientific_notation_negative_e',
  'expr': 'assert abc 3.4e-12',
  'result':{'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'float': '3.4e-12'}}}]}
}
,{'name': 'float_negative_scientific_notation',
  'expr': 'assert abc -3.4e2',
  'result':{'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'float': '-3.4e2'}}}]}
}
,{'name': 'float_postive_scientific_notation',
  'expr': 'assert abc +3.4e2',
  'result':{'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'float': '+3.4e2'}}}]}
}            
,{'name': 'float_postive_scientific_notation_negative_e',
  'expr': 'assert abc +3.4e-22',
  'result':{'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'float': '+3.4e-22'}}}]}
}
,{'name': 'float_postive_scientific_notation_positive_e',
  'expr': 'assert abc +3.4e+9',
  'result':{'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'float': '+3.4e+9'}}}]}
}
,{'name': 'float_infinite',
  'expr': 'assert abc inf',
  'result':{'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'float': 'INF'}}}]}
}                                 
,{'name': 'float_postitive_infinite',
  'expr': 'assert abc +inf',
  'result':{'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'float': '+INF'}}}]}
}
,{'name': 'float_negative_infinite',
  'expr': 'assert abc -inf',
  'result':{'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'float': '-INF'}}}]}
}
,{'name': 'float_infinite_mixed_case',
  'expr': 'assert abc iNF',
  'result':{'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'float': 'INF'}}}]}
} 
,{'name': 'string_single_quote',
  'expr': "assert abc 'abc'",
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 
                                        'body': {'string': "'abc'"}}}]}}
,{'name': 'string_double_quote',
  'expr': 'assert abc "abc"',
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 
                                        'body': {'string': '"abc"'}}}]}}  
,{'name': 'string_single_quote_escaped',
  'expr': r"""assert abc 'a\'bc'""",
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 
                                        'body': {'string': r"'a\'bc'"}}}]}}                       
,{'name': 'string_double_quote_escaped',
  'expr': r'''assert abc "ab\"c"''',
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied', 
                                        'body': {'string': r'"ab\"c"'}}}]}}  
,{'name': 'qname_no_prefix',
  'expr': 'assert abc hello',
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied',
                                        'body': {'qname': {'localName': 'hello', 'prefix': '*'}}}}]}}
,{'name': 'qname_with_prefix',
  'expr': 'assert abc pre:hello',
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied',
                                        'body': {'qname': {'localName': 'hello', 'prefix': 'pre'}}}}]}}
,{'name': 'severity_literal_error',
  'expr': 'assert abc error',
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied',
                                        'body': {'severity': 'error'}}}]}}
,{'name': 'severity_literal_warning',
  'expr': 'assert abc warning',
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied',
                                        'body': {'severity': 'warning'}}}]}}
,{'name': 'severity_literal_info',
  'expr': 'assert abc info',
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied',
                                        'body': {'severity': 'info'}}}]}}
,{'name': 'severity_literal_pass',
  'expr': 'assert abc pass',
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied',
                                        'body': {'severity': 'pass'}}}]}}
) 

Functions = (
 {'name': 'function_reference_no_args',
  'expr': 'assert abc xyz()',
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied',
                                        'body': {'functionReference': {
                                                                       'functionName': 'xyz',
                                                                       'functionArgs': []
                                                                       }}}}]}}
,{'name': 'function_reference_one_args',
  'expr': 'assert abc xyz(1)',
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied',
                                        'body': {'functionReference': {
                                                                       'functionName': 'xyz',
                                                                       'functionArgs': [
                                                                                        {'integer': '1'}
                                                                                        ]
                                                                       }}}}]}}
,{'name': 'function_reference_two_args',
  'expr': 'assert abc xyz(1,"arg1")',
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied',
                                        'body': {'functionReference': {
                                                                       'functionName': 'xyz',
                                                                       'functionArgs': [
                                                                                        {'integer': '1'},
                                                                                        {'string': '"arg1"'}
                                                                                        ]
                                                                       }}}}]}}
,{'name': 'function_reference_nested',
  'expr': 'assert abc xyz(1,zzz(5))',
  'result': {'xuleDoc': [{'assertion': {'ruleName': 'abc', 'satisfactionType': 'satisfied',
                                        'body': {'functionReference': {
                                                                       'functionName': 'xyz',
                                                                       'functionArgs': [
                                                                                        {'integer': '1'},
                                                                                        {'functionReference': {
                                                                                                               'functionName': 'zzz',
                                                                                                               'functionArgs': [
                                                                                                                                {'integer': '5'}
                                                                                                                                ]
                                                                                                               }
                                                                                         
                                                                                         }
                                                                                        ]
                                                                       }}}}]}}
             
)

Variables = (


)

Notes = (
 {'name':'notes',
  'note':
  '''
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
  '''}
,         
)
