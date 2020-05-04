import {AbstractParseTreeVisitor} from "antlr4ts/tree";
import {XULEParserVisitor} from "./parser/XULEParserVisitor";
import {Diagnostic, DiagnosticSeverity} from "vscode-languageserver";
import {Binding, IdentifierType, FunctionInfo, SymbolTable, IdentifierInfo} from "./symbols";
import {
    ExpressionContext,
    FilterContext, FunctionDeclarationContext,
    NavigationWhereClauseContext,
    OutputAttributeContext, ParametersListContext, VariableReadContext
} from "./parser/XULEParser";
import {Range, TextDocument} from "vscode-languageserver-textdocument";
import {ParserRuleContext} from "antlr4ts";
import {number} from "vscode-languageserver/lib/utils/is";

function bindingInfo(binding: Binding, type: IdentifierType) {
    if(binding.meaning instanceof Array) {
        return binding.meaning.find(x => x instanceof IdentifierInfo && x.type == type);
    } else {
        if(binding.meaning instanceof IdentifierInfo && binding.meaning.type == type) {
            return binding.meaning;
        }
    }
}

export class SemanticCheckVisitor  extends AbstractParseTreeVisitor<any> implements XULEParserVisitor<any> {

    localVariables = {};
    checkVariables = true;
    checkFunctions = true;

    constructor(public diagnostics: Diagnostic[], protected symbolTable: SymbolTable, protected document: TextDocument) {
        super();
    }

    protected defaultResult(): any {
        return undefined;
    }

    visitExpression = (ctx: ExpressionContext) => {
        if(ctx.parametersList()) {
            this.checkFunctionCall(ctx);
        } else {
            let identifier = ctx.variableRead();
            if(identifier) {
                let variableName = identifier.text.toLowerCase();
                if(variableName.startsWith("$")) {
                    this.checkVariableAccess(variableName, ctx, identifier);
                }
            } else {
                this.visitChildren(ctx);
            }
        }
    };

    protected checkVariableAccess(variableName: string, ctx: ExpressionContext, identifier: VariableReadContext) {
        if(!this.checkVariables) {
            return;
        }
        let binding = this.lookupIgnoreCase(variableName, ctx);
        const range = this.getRange(identifier);
        if (!binding && !wellKnownVariables[variableName] && !this.localVariables[variableName]) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Warning,
                range: range,
                message: "Unknown variable or constant: " + identifier.text,
                source: 'XULE semantic checker'
            });
        } else if (binding && !bindingInfo(binding, IdentifierType.CONSTANT) && !bindingInfo(binding, IdentifierType.VARIABLE)) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Warning,
                range: range,
                message: "Not a variable or constant: " + identifier.text,
                source: 'XULE semantic checker'
            });
        }
    }

    private getRange(parseTree: ParserRuleContext): Range {
        if(this.document) {
            return {
                start: this.document.positionAt(parseTree.start.startIndex),
                end: this.document.positionAt(parseTree.stop.stopIndex + 1)
            };
        } else {
            return { start: null, end: null };
        }
    }

    visitOutputAttribute = (ctx: OutputAttributeContext) => {
        this.withLocalVariables({ 'error': {} }, () => this.visitChildren(ctx));
    };

    private withLocalVariables(localVariables: Object, thunk: () => void) {
        const prev = this.localVariables;
        this.localVariables = {...this.localVariables, ...localVariables};
        try {
            thunk.call(this);
        } finally {
            this.localVariables = prev;
        }
    }

    visitFilter = (ctx: FilterContext) => {
        this.withLocalVariables({ '$item': {} }, () => this.visitChildren(ctx));
    };

    /**
     * "A special variable $relationship is available in the ‘where’ expression to refer to the relationship being filtered."
     * Page 31.
     * */
    visitNavigationWhereClause = (ctx: NavigationWhereClauseContext) => {
        this.withLocalVariables({ '$relationship': {} }, () => this.visitChildren(ctx));
    };

    visitFunctionDeclaration = (ctx: FunctionDeclarationContext) => {
        let functionName = ctx.identifier().text;
        if(functionName.startsWith("$")) {
            const range = this.getRange(ctx.identifier());
            this.diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: range,
                message: "Invalid function name: " + ctx.identifier().text,
                source: 'XULE semantic checker'
            });
        }
        return this.visitChildren(ctx);
    };

    protected lookupIgnoreCase(name: string, ctx: ExpressionContext) {
        function lookup(binding) {
            return binding.name.toString().toLowerCase() == name;
        }
        return this.symbolTable.lookup(lookup, ctx);
    }

    protected checkFunctionCall(ctx: ExpressionContext) {
        const expression = ctx.expression(0);
        const identifier = expression.variableRead();
        let parametersList = ctx.parametersList();
        if (identifier) {
            let functionName = identifier.text.toLowerCase();
            const range = this.getRange(identifier);
            if(functionName.startsWith("$")) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: range,
                    message: "Invalid function name: " + identifier.text,
                    source: 'XULE semantic checker'
                });
                return;
            }
            if(!this.checkFunctions) {
                return;
            }
            let binding = this.lookupIgnoreCase(functionName, ctx);
            if (!binding && !wellKnownFunctions[functionName]) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Warning,
                    range: range,
                    message: "Unknown function: " + identifier.text,
                    source: 'XULE semantic checker'
                });
            } else if (binding && !bindingInfo(binding, IdentifierType.FUNCTION)) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Warning,
                    range: range,
                    message: "Not a function: " + identifier.text,
                    source: 'XULE semantic checker'
                });
            } else {
                let functionInfo: FunctionInfo = wellKnownFunctions[functionName] || bindingInfo(binding, IdentifierType.FUNCTION);
                this.checkArity(functionInfo, parametersList);
            }
        } else {
            this.visitExpression(expression);
        }
        this.visit(parametersList);
    }

    private checkArity(functionInfo: FunctionInfo, parametersList: ParametersListContext) {
        const range = this.getRange(parametersList);
        if (typeof (functionInfo.arity) === 'number') {
            if (functionInfo.arity != parametersList.expression().length) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: range,
                    message: `Expected ${functionInfo.arity} parameters`,
                    source: 'XULE semantic checker'
                });
            }
        } else if (functionInfo.arity) {
            let arity = functionInfo.arity as any;
            if (typeof (arity.min) === 'number' && parametersList.expression().length < arity.min) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: range,
                    message: `Expected at least ${arity.min} parameters`,
                    source: 'XULE semantic checker'
                });
            }
            if (typeof (arity.max) === 'number' && parametersList.expression().length > arity.max) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: range,
                    message: `Expected at most ${arity.max} parameters`,
                    source: 'XULE semantic checker'
                });
            }
        }
    }
}

export const wellKnownFunctions: { [name: string]: FunctionInfo } = {
    "abs": new FunctionInfo(1),
    "all": new FunctionInfo(1),
    "any": new FunctionInfo(1),
    "avg": new FunctionInfo(1),
    "contains": new FunctionInfo(2),
    "count": new FunctionInfo(1),
    "csv-data": new FunctionInfo({ min: 2, max: 4 }),
    "date": new FunctionInfo(1),
    "day": new FunctionInfo(1),
    "dict": new FunctionInfo(1),
    "duration": new FunctionInfo(2),
    "entry-point-namespace": new FunctionInfo(1),
    "exists": new FunctionInfo(1),
    "first": new FunctionInfo(1),
    "first-value": new FunctionInfo(),
    "forever": new FunctionInfo(0),
    "is_base": new FunctionInfo(),
    "index-of": new FunctionInfo(2),
    "json-data": new FunctionInfo(1),
    "last": new FunctionInfo(1),
    "last-index-of": new FunctionInfo(2),
    "length": new FunctionInfo(1),
    "list": new FunctionInfo(),
    "log10": new FunctionInfo(1),
    "lower-case": new FunctionInfo(1),
    "max": new FunctionInfo(1),
    "min": new FunctionInfo(1),
    "missing": new FunctionInfo(1),
    "mod": new FunctionInfo(2),
    "month": new FunctionInfo(1),
    "number": new FunctionInfo(1),
    "power": new FunctionInfo(2),
    "prod": new FunctionInfo(1),
    "qname": new FunctionInfo(2),
    "range": new FunctionInfo({ min: 1, max: 3 }),
    "round": new FunctionInfo(2),
    "rule-name": new FunctionInfo(0),
    "set": new FunctionInfo(),
    "signum": new FunctionInfo(1),
    "sort": new FunctionInfo(1),
    "split": new FunctionInfo(2),
    "string": new FunctionInfo(1),
    "substring": new FunctionInfo({ min: 2, max: 3 }),
    "sum": new FunctionInfo(1),
    "stdev": new FunctionInfo(1),
    "taxonomy": new FunctionInfo({ min: 0, max: 1 }),
    "time-span": new FunctionInfo(1),
    "to-qname": new FunctionInfo(1),
    "trunc": new FunctionInfo({ min: 1, max: 2 }),
    "unit": new FunctionInfo({ min: 1, max: 2 }),
    "upper-case": new FunctionInfo(1),
    "year": new FunctionInfo(1)
};

export const wellKnownVariables = {
    "$fact": {},
    "$ruleversion": {},
    "$rule-value": {},
    //The following are actually constants or keywords, but for know we don't need to distinguish them
    "duration": {},
    "inf": {},
    "none": {},
    "skip": {},
    //The following are specific to taxonomies
    "all": {},
    "dimension-default": {},
    "dimension-domain": {},
    "domain-member": {},
    "essence-alias": {},
    "general-special": {},
    "hypercube-dimension": {},
    "parent-child": {},
    "summation-item": {},
};