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
  'result': {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]}
 }
,{'name': 'empty_factset_bracket',
  'expr': 'assert abc []',
  'result': {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'factsetType': 'closed', 'exprName': 'factset'}, 'exprName': 'assertion'}]}
 }
,{'name': 'empty_covered',
  'expr': 'assert abc {covered}',
  'result':
   {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'covered': True, 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]}
 }
,{'name': 'simple_aspect_curly',
  'expr': 'assert abc {@}',
  'result':
    {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'covered', 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]}
 }
,{'name': 'simple_aspect_no_curly',
  'expr': 'assert abc @',
  'result':
    {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'covered', 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]}

 }
,{'name': 'simple_uncovered_aspect_curly',
  'expr': 'assert abc{@@}',
  'result':
    {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'uncovered', 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]}
 }
,{'name': 'simple_uncovered_aspect_no_curly',
  'expr': 'assert abc @@',
  'result':
    {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'uncovered', 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]}
 }
,{'name': 'empty_covered_bracket',
  'expr': 'assert abc [covered]',
  'result':
    {'xuleDoc': [{'body': {'covered': True,
                       'exprName': 'factset',
                       'factsetType': 'closed'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
 }
,{'name': 'simple_aspect_bracket',
  'expr': 'assert abc [@]',
  'result':
    {'xuleDoc': [{'body': {'aspectFilters': [{'coverType': 'covered',
                                          'exprName': 'aspectFilter'}],
                       'exprName': 'factset',
                       'factsetType': 'closed'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
 }
,{'name': 'simple_uncovered_aspect_bracket',
  'expr': 'assert abc [@@]',
  'result':
    {'xuleDoc': [{'body': {'aspectFilters': [{'coverType': 'uncovered',
                                          'exprName': 'aspectFilter'}],
                       'exprName': 'factset',
                       'factsetType': 'closed'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
 }
,{'name': 'named_common_aspect',
  'expr': 'assert abc @concept',
  'result':
    {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'covered', 'aspectName': 'concept', 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]}
 }
,{'name': 'named_common_aspect_upper_and_lower',
  'expr': 'assert abc @coNCepT',
  'result':
    {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'covered', 'aspectName': 'concept', 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]}

 }           
,{'name': 'named_default_dim_aspect',
  'expr': 'assert abc @dimension',
  'result':
    {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'covered', 'aspectDimensionName': {'prefix': '*', 'localName': 'dimension', 'exprName': 'qname'}, 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]}

 }          
,{'name': 'named_prefixed_dim_aspect',
  'expr': 'assert abc @dim:dimension',
  'result':
    {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'aspectFilters': [{'coverType': 'covered', 'aspectDimensionName': {'prefix': 'dim', 'localName': 'dimension', 'exprName': 'qname'}, 'exprName': 'aspectFilter'}], 'factsetType': 'open', 'exprName': 'factset'}, 'exprName': 'assertion'}]}
 }                    
,{'name': 'named_prefixed_dim_aspect_equal',
  'expr': 'assert abc @dim:dimension = block',
  'expr_stop':'aspectExpr',
  'result':
    {'xuleDoc': [{'body': {'aspectFilters': [{'aspectDimensionName': {'exprName': 'qname',
                                                                  'localName': 'dimension',
                                                                  'prefix': 'dim'},
                                                              'aspectExpr': 'expr_stop',
                                                              'aspectOperator': '=',
                                          'coverType': 'covered',
                                          'exprName': 'aspectFilter'}],
                       'exprName': 'factset',
                       'factsetType': 'open'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
 } 
,{'name': 'named_dim_aspect_starts_with_concept',
  'expr': 'assert abc @conceptabc',
  'result': 
    {'xuleDoc': [{'body': {'aspectFilters': [{'aspectDimensionName': {'exprName': 'qname',
                                                                  'localName': 'conceptabc',
                                                                  'prefix': '*'},
                                          'coverType': 'covered',
                                          'exprName': 'aspectFilter'}],
                       'exprName': 'factset',
                       'factsetType': 'open'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}         
  }
       
,{'name': 'simple_where_curly',
  'expr': 'assert abc {where 1}',
  'result':
    {'xuleDoc': [{'body': {'exprName': 'factset',
                       'factsetType': 'open',
                       'whereExpr': {'exprName': 'integer', 'value': '1'}},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
 }
,{'name': 'simple_where_bracket',
  'expr': 'assert abc [where 1]',
  'result':
    {'xuleDoc': [{'body': {'exprName': 'factset',
                       'factsetType': 'closed',
                       'whereExpr': {'exprName': 'integer', 'value': '1'}},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
 }
,{'name': 'aspect_equal',
  'expr': 'assert abc @concept=block',
  'expr_stop': 'aspectExpr',
  'result':
    {'xuleDoc': [{'body': {'aspectFilters': [{'aspectExpr': 'expr_stop',
                                          'aspectName': 'concept',
                                          'aspectOperator': '=',
                                          'coverType': 'covered',
                                          'exprName': 'aspectFilter'}],
                       'exprName': 'factset',
                       'factsetType': 'open'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
 }
,{'name': 'aspect_equal_multi',
  'expr': 'assert abc @concept=block @unit=block',
  'expr_stop': 'aspectExpr',
  'result':
    {'xuleDoc': [{'body': {'aspectFilters': [{'aspectExpr': 'expr_stop',
                                          'aspectName': 'concept',
                                          'aspectOperator': '=',
                                          'coverType': 'covered',
                                          'exprName': 'aspectFilter'},
                                         {'aspectExpr': 'expr_stop',
                                          'aspectName': 'unit',
                                          'aspectOperator': '=',
                                          'coverType': 'covered',
                                          'exprName': 'aspectFilter'}],
                       'exprName': 'factset',
                       'factsetType': 'open'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
 }  
,{'name': 'aspect_equal_with_alias',
  'expr': 'assert abc @concept=block as con',
  'expr_stop': 'aspectExpr',
  'result':
    {'xuleDoc': [{'body': {'aspectFilters': [{'alias': 'con',
                                          'aspectExpr': 'expr_stop',
                                          'aspectName': 'concept',
                                          'aspectOperator': '=',
                                          'coverType': 'covered',
                                          'exprName': 'aspectFilter'}],
                       'exprName': 'factset',
                       'factsetType': 'open'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
 }
,{'name': 'aspect_with_alias',
  'expr': 'assert abc @concept as con',
  'result':
    {'xuleDoc': [{'body': {'aspectFilters': [{'alias': 'con',
                                          'aspectName': 'concept',
                                          'coverType': 'covered',
                                          'exprName': 'aspectFilter'}],
                       'exprName': 'factset',
                       'factsetType': 'open'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
 }
           
,{'name': 'aspect_equal_with_alias_curly',
  'expr': 'assert abc {@concept=block as con}',
  'expr_stop': 'aspectExpr',
  'result':
    {'xuleDoc': [{'body': {'aspectFilters': [{'alias': 'con',
                                          'aspectExpr': 'expr_stop',
                                          'aspectName': 'concept',
                                          'aspectOperator': '=',
                                          'coverType': 'covered',
                                          'exprName': 'aspectFilter'}],
                       'exprName': 'factset',
                       'factsetType': 'open'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
 }
,{'name': 'aspect_with_alias_curly',
  'expr': 'assert abc {@concept as con}',
  'result':
    {'xuleDoc': [{'body': {'aspectFilters': [{'alias': 'con',
                                          'aspectName': 'concept',
                                          'coverType': 'covered',
                                          'exprName': 'aspectFilter'}],
                       'exprName': 'factset',
                       'factsetType': 'open'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
 }

,{'name': 'aspect_equal_with_alias_bracket',
  'expr': 'assert abc [@concept=block as con]',
  'result':
   {'xuleDoc': [{'body': {'aspectFilters': [{'alias': 'con',
                                          'aspectExpr': {'exprName': 'qname',
                                                         'localName': 'block',
                                                         'prefix': '*'},
                                          'aspectName': 'concept',
                                          'aspectOperator': '=',
                                          'coverType': 'covered',
                                          'exprName': 'aspectFilter'}],
                       'exprName': 'factset',
                       'factsetType': 'closed'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
 }
,{'name': 'aspect_with_alias_bracket',
  'expr': 'assert abc [@concept as con]',
  'result':
    {'xuleDoc': [{'body': {'aspectFilters': [{'alias': 'con',
                                          'aspectName': 'concept',
                                          'coverType': 'covered',
                                          'exprName': 'aspectFilter'}],
                       'exprName': 'factset',
                       'factsetType': 'closed'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
 }
,{'name': 'factset_expr',
  'expr': 'assert abc {4}',
  'result': 
    {'xuleDoc': [{'body': {'exprName': 'factset',
                       'factsetType': 'open',
                       'innerExpr': {'exprName': 'integer', 'value': '4'}},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
}
,{'name': 'factset_expr_where',
  'expr': 'assert abc {4 where  5}',
  'result': 
    {'xuleDoc': [{'body': {'exprName': 'factset',
                       'factsetType': 'open',
                       'innerExpr': {'exprName': 'integer', 'value': '4'},
                       'whereExpr': {'exprName': 'integer', 'value': '5'}},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]} 
}
,{'name': 'factset_expr_aspect_where',
  'expr': 'assert abc {@Assets 4 where  5}',
  'result': 
    {'xuleDoc': [{'body': {'aspectFilters': [{'aspectDimensionName': {'exprName': 'qname',
                                                                  'localName': 'Assets',
                                                                  'prefix': '*'},
                                          'coverType': 'covered',
                                          'exprName': 'aspectFilter'}],
                       'exprName': 'factset',
                       'factsetType': 'open',
                       'innerExpr': {'exprName': 'integer', 'value': '4'},
                       'whereExpr': {'exprName': 'integer', 'value': '5'}},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]} 
}           
           
,{'name': 'no_aspect_name_with_alias',
  'expr': 'assert abc @ as asp',
  'result': None}                               

,{'name': 'no_aspect_name_with_alias_curly',
  'expr': 'assert abc {@ as asp}',
  'result': None}  
,{'name': 'no_aspect_name_with_alias_bracket',
  'expr': 'assert abc [@ as asp]',
  'result': None}                                           
)

Literals = (
 {'name': 'integer',
  'expr': 'assert abc 1',
  'result':{'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': '1', 'exprName': 'integer'}, 'exprName': 'assertion'}]}
 }
,{'name': 'integer_negative',
  'expr': 'assert abc -1',
  'result':{'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'op': '-', 'expr': {'value': '1', 'exprName': 'integer'}, 'exprName': 'unaryExpr'}, 'exprName': 'assertion'}]}
 }
,{'name': 'integer_postive',
  'expr': 'assert abc +3',
  'result':{'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'op': '+', 'expr': {'value': '3', 'exprName': 'integer'}, 'exprName': 'unaryExpr'}, 'exprName': 'assertion'}]}
 }  
,{'name': 'float',
  'expr': 'assert abc 2.3',
  'result':{'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': '2.3', 'exprName': 'float'}, 'exprName': 'assertion'}]}
 }                      
,{'name': 'float_scientific_notation',
  'expr': 'assert abc 3.4e2',
  'result':{'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': '3.4e2', 'exprName': 'float'}, 'exprName': 'assertion'}]}
}
,{'name': 'float_scientific_notation_negative_e',
  'expr': 'assert abc 3.4e-12',
  'result':{'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': '3.4e-12', 'exprName': 'float'}, 'exprName': 'assertion'}]}
}
,{'name': 'float_negative_scientific_notation',
  'expr': 'assert abc -3.4e2',
  'result':{'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'op': '-', 'expr': {'value': '3.4e2', 'exprName': 'float'}, 'exprName': 'unaryExpr'}, 'exprName': 'assertion'}]}
}
,{'name': 'float_postive_scientific_notation',
  'expr': 'assert abc +3.4e2',
  'result':{'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'op': '+', 'expr': {'value': '3.4e2', 'exprName': 'float'}, 'exprName': 'unaryExpr'}, 'exprName': 'assertion'}]}
}            
,{'name': 'float_postive_scientific_notation_negative_e',
  'expr': 'assert abc +3.4e-22',
  'result':{'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'op': '+', 'expr': {'value': '3.4e-22', 'exprName': 'float'}, 'exprName': 'unaryExpr'}, 'exprName': 'assertion'}]}
}
,{'name': 'float_postive_scientific_notation_positive_e',
  'expr': 'assert abc +3.4e+9',
  'result':{'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'op': '+', 'expr': {'value': '3.4e+9', 'exprName': 'float'}, 'exprName': 'unaryExpr'}, 'exprName': 'assertion'}]}
}
,{'name': 'float_infinite',
  'expr': 'assert abc inf',
  'result':{'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': 'INF', 'exprName': 'float'}, 'exprName': 'assertion'}]}
}                                 
,{'name': 'float_postitive_infinite',
  'expr': 'assert abc +inf',
  'result':{'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'op': '+', 'expr': {'value': 'INF', 'exprName': 'float'}, 'exprName': 'unaryExpr'}, 'exprName': 'assertion'}]}
}
,{'name': 'float_negative_infinite',
  'expr': 'assert abc -inf',
  'result':{'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'op': '-', 'expr': {'value': 'INF', 'exprName': 'float'}, 'exprName': 'unaryExpr'}, 'exprName': 'assertion'}]}
}
,{'name': 'float_infinite_mixed_case',
  'expr': 'assert abc iNF',
  'result':{'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': 'INF', 'exprName': 'float'}, 'exprName': 'assertion'}]}
} 
,{'name': 'string_single_quote',
  'expr': "assert abc 'abc'",
  'result': {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': "'abc'", 'exprName': 'string'}, 'exprName': 'assertion'}]}
}
,{'name': 'string_double_quote',
  'expr': 'assert abc "abc"',
  'result': {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': '"abc"', 'exprName': 'string'}, 'exprName': 'assertion'}]}
}  
,{'name': 'string_single_quote_escaped',
  'expr': r"""assert abc 'a\'bc'""",
  'result': {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': "'a\\'bc'", 'exprName': 'string'}, 'exprName': 'assertion'}]}
  }                       
,{'name': 'string_double_quote_escaped',
  'expr': r'''assert abc "ab\"c"''',
  'result': {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': '"ab\\"c"', 'exprName': 'string'}, 'exprName': 'assertion'}]}
  }  
,{'name': 'qname_no_prefix',
  'expr': 'assert abc hello',
  'result': {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'prefix': '*', 'localName': 'hello', 'exprName': 'qname'}, 'exprName': 'assertion'}]}
  }
,{'name': 'qname_with_prefix',
  'expr': 'assert abc pre:hello',
  'result': {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'prefix': 'pre', 'localName': 'hello', 'exprName': 'qname'}, 'exprName': 'assertion'}]}
  }
,{'name': 'severity_literal_error',
  'expr': 'assert abc error',
  'result': {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': 'error', 'exprName': 'severity'}, 'exprName': 'assertion'}]}
  }
,{'name': 'severity_literal_warning',
  'expr': 'assert abc warning',
  'result': {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': 'warning', 'exprName': 'severity'}, 'exprName': 'assertion'}]}
  }
,{'name': 'severity_literal_info',
  'expr': 'assert abc info',
  'result': {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'prefix': '*', 'localName': 'info', 'exprName': 'qname'}, 'exprName': 'assertion'}]}
  }
,{'name': 'severity_literal_pass',
  'expr': 'assert abc pass',
  'result': {'xuleDoc': [{'ruleName': 'abc', 'satisfactionType': 'satisfied', 'body': {'value': 'pass', 'exprName': 'severity'}, 'exprName': 'assertion'}]}
  }
) 

Functions = (
 {'name': 'function_reference_no_args',
  'expr': 'assert abc xyz()',
  'result': {'xuleDoc': [{'body': {'exprName': 'functionReference',
                       'functionArgs': [],
                       'functionName': 'xyz'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
  }
,{'name': 'function_reference_one_args',
  'expr': 'assert abc xyz(1)',
  'result': {'xuleDoc': [{'body': {'exprName': 'functionReference',
                       'functionArgs': [{'exprName': 'integer', 'value': '1'}],
                       'functionName': 'xyz'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
  }
,{'name': 'function_reference_two_args',
  'expr': 'assert abc xyz(1,"arg1")',
  'result': {'xuleDoc': [{'body': {'exprName': 'functionReference',
                       'functionArgs': [{'exprName': 'integer', 'value': '1'},
                                        {'exprName': 'string',
                                         'value': '"arg1"'}],
                       'functionName': 'xyz'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
  }
,{'name': 'function_reference_nested',
  'expr': 'assert abc xyz(1,zzz(5))',
  'result': {'xuleDoc': [{'body': {'exprName': 'functionReference',
                       'functionArgs': [{'exprName': 'integer', 'value': '1'},
                                        {'exprName': 'functionReference',
                                         'functionArgs': [{'exprName': 'integer',
                                                           'value': '5'}],
                                         'functionName': 'zzz'}],
                       'functionName': 'xyz'},
              'exprName': 'assertion',
              'ruleName': 'abc',
              'satisfactionType': 'satisfied'}]}
  }
             
)

Variables = (


)


Constants = (
{'name': 'constant_as_function',
  'expr': 'constant abc = xyz()',
  'result': {'xuleDoc': [{'body': {'exprName': 'functionReference',
                       'functionArgs': [],
                       'functionName': 'xyz'},
              'constantName': 'abc',
              'exprName': 'constantDeclaration'}]}
  }
,{'name': 'constant_as_value',
  'expr': 'constant abc = 4',
  'result': {'xuleDoc': [{'constantName': 'abc', 'body': {'value': '4', 'exprName': 'integer'}, 'exprName': 'constantDeclaration'}]}
  }
,{'name': 'constant_as_list',
  'expr': 'constant abc = list(4,5,6)',
  'result': {'xuleDoc': [{'body': {'exprName': 'functionReference',
                       'functionArgs': [{'exprName': 'integer', 'value': '4'},
                                        {'exprName': 'integer', 'value': '5'},
                                        {'exprName': 'integer', 'value': '6'}],
                       'functionName': 'list'},
              'constantName': 'abc',
              'exprName': 'constantDeclaration'}]}
  }
,{'name': 'constant_as_list_in_list',
  'expr': 'constant abc = list(list(a,b) , list(y,z))',
  'result': {'xuleDoc': [{'body': {'exprName': 'functionReference',
                       'functionArgs': [{'exprName': 'functionReference',
                                         'functionArgs': [{'exprName': 'qname',
                                                           'localName': 'a',
                                                           'prefix': '*'},
                                                          {'exprName': 'qname',
                                                           'localName': 'b',
                                                           'prefix': '*'}],
                                         'functionName': 'list'},
                                        {'exprName': 'functionReference',
                                         'functionArgs': [{'exprName': 'qname',
                                                           'localName': 'y',
                                                           'prefix': '*'},
                                                          {'exprName': 'qname',
                                                           'localName': 'z',
                                                           'prefix': '*'}],
                                         'functionName': 'list'}],
                       'functionName': 'list'},
              'constantName': 'abc',
              'exprName': 'constantDeclaration'}]}
 
    }
,{'name': 'constant_as_add_list',
  'expr': 'constant abc = list(a,b) + list(x,y)',
  'result': {'xuleDoc': [{'body': {'exprName': 'addExpr',
                       'leftExpr': {'exprName': 'functionReference',
                                    'functionArgs': [{'exprName': 'qname',
                                                      'localName': 'a',
                                                      'prefix': '*'},
                                                     {'exprName': 'qname',
                                                      'localName': 'b',
                                                      'prefix': '*'}],
                                    'functionName': 'list'},
                       'rights': [{'exprName': 'rightOperation',
                                   'op': '+',
                                   'rightExpr': {'exprName': 'functionReference',
                                                 'functionArgs': [{'exprName': 'qname',
                                                                   'localName': 'x',
                                                                   'prefix': '*'},
                                                                  {'exprName': 'qname',
                                                                   'localName': 'y',
                                                                   'prefix': '*'}],
                                                 'functionName': 'list'}}]},
              'constantName': 'abc',
              'exprName': 'constantDeclaration'}]}
 
    }
,{'name': 'constant_as_add_multi_list',
  'expr': 'constant abc = list(a) + list(z) + list(g)',
  'result': {'xuleDoc': [{'body': {'exprName': 'addExpr',
                       'leftExpr': {'exprName': 'functionReference',
                                    'functionArgs': [{'exprName': 'qname',
                                                      'localName': 'a',
                                                      'prefix': '*'}],
                                    'functionName': 'list'},
                       'rights': [{'exprName': 'rightOperation',
                                   'op': '+',
                                   'rightExpr': {'exprName': 'functionReference',
                                                 'functionArgs': [{'exprName': 'qname',
                                                                   'localName': 'z',
                                                                   'prefix': '*'}],
                                                 'functionName': 'list'}},
                                  {'exprName': 'rightOperation',
                                   'op': '+',
                                   'rightExpr': {'exprName': 'functionReference',
                                                 'functionArgs': [{'exprName': 'qname',
                                                                   'localName': 'g',
                                                                   'prefix': '*'}],
                                                 'functionName': 'list'}}]},
              'constantName': 'abc',
              'exprName': 'constantDeclaration'}]}
    }      
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
