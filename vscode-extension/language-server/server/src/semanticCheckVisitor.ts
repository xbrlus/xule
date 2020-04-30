import {AbstractParseTreeVisitor} from "antlr4ts/tree";
import {XULEParserVisitor} from "./parser/XULEParserVisitor";
import {Diagnostic, DiagnosticSeverity} from "vscode-languageserver";
import {Binding, DeclarationType, SymbolTable} from "./symbols";
import {
    ExpressionContext,
    FilterContext,
    NavigationWhereClauseContext,
    OutputAttributeContext, VariableReadContext
} from "./parser/XULEParser";
import {TextDocument} from "vscode-languageserver-textdocument";

function isBindingType(binding: Binding, type: DeclarationType) {
    if(binding.meaning instanceof Array) {
        return binding.meaning.find(x => x == type) !== false;
    } else {
        return binding.meaning == type;
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
        const range = {
            start: this.document.positionAt(identifier.start.startIndex),
            end: this.document.positionAt(identifier.stop.stopIndex + 1)
        };
        if (!binding && !wellKnownVariables[variableName] && !this.localVariables[variableName]) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Warning,
                range: range,
                message: "Unknown variable or constant: " + identifier.text,
                source: 'XULE semantic checker'
            });
        } else if (binding && !isBindingType(binding, DeclarationType.CONSTANT) && !isBindingType(binding, DeclarationType.VARIABLE)) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Warning,
                range: range,
                message: "Not a variable or constant: " + identifier.text,
                source: 'XULE semantic checker'
            });
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

    protected lookupIgnoreCase(name: string, ctx: ExpressionContext) {
        function lookup(binding) {
            return binding.name.toString().toLowerCase() == name;
        }
        return this.symbolTable.lookup(lookup, ctx);
    }

    private checkFunctionCall(ctx: ExpressionContext) {
        if(!this.checkFunctions) {
            return;
        }
        const expression = ctx.expression(0);
        const identifier = expression.variableRead();
        if (identifier) {
            let functionName = identifier.text.toLowerCase();
            let binding = this.lookupIgnoreCase(functionName, ctx);
            const range = {
                start: this.document.positionAt(identifier.start.startIndex),
                end: this.document.positionAt(identifier.stop.stopIndex + 1)
            };
            if (!binding && !wellKnownFunctions[functionName]) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Warning,
                    range: range,
                    message: "Unknown function: " + identifier.text,
                    source: 'XULE semantic checker'
                });
            } else if (binding && !isBindingType(binding, DeclarationType.FUNCTION)) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Warning,
                    range: range,
                    message: "Not a function: " + identifier.text,
                    source: 'XULE semantic checker'
                });
            }
        } else {
            this.visitExpression(expression);
        }
        this.visit(ctx.parametersList());
    }
}

export const wellKnownFunctions = {
    "abs": {},
    "all": {},
    "any": {},
    "avg": {},
    "count": {},
    "csv-data": {},
    "date": {},
    "day": {},
    "dict": {},
    "duration": {},
    "entry-point-namespace": {},
    "exists": {},
    "first": {},
    "first-value": {},
    "forever": {},
    "is_base": {},
    "json-data": {},
    "last": {},
    "length": {},
    "list": {},
    "log10": {},
    "min": {},
    "missing": {},
    "mod": {},
    "month": {},
    "power": {},
    "prod": {},
    "qname": {},
    "range": {},
    "round": {},
    "rule-name": {},
    "set": {},
    "signum": {},
    "sum": {},
    "stdev": {},
    "taxonomy": {},
    "time-span": {},
    "trunc": {},
    "unit": {},
    "year": {}
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