import {AbstractParseTreeVisitor} from "antlr4ts/tree";
import {XULEParserVisitor} from "./parser/XULEParserVisitor";
import {Diagnostic, DiagnosticSeverity} from "vscode-languageserver";
import {Binding, DeclarationType, SymbolTable} from "./symbols";
import {ExpressionContext, OutputAttributeContext, VariableReadContext} from "./parser/XULEParser";
import {TextDocument} from "vscode-languageserver-textdocument";

function isBindingType(binding: Binding, type: DeclarationType) {
    if(binding.meaning instanceof Array) {
        return binding.meaning.find(x => x == type);
    } else {
        return binding.meaning == type;
    }
}

export class SemanticCheckVisitor  extends AbstractParseTreeVisitor<any> implements XULEParserVisitor<any> {

    localVariables = {};

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
                let binding = this.lookupIgnoreCase(variableName, ctx);
                const range = {
                    start: this.document.positionAt(identifier.start.startIndex),
                    end: this.document.positionAt(identifier.stop.stopIndex + 1)
                };
                if (!binding && !wellKnownVariables[variableName] && !this.localVariables[variableName]) {
                    this.diagnostics.push({
                        severity: DiagnosticSeverity.Error,
                        range: range,
                        message: "Unknown variable or constant: " + identifier.text,
                        source: 'XULE semantic checker'
                    });
                } else if (binding && !isBindingType(binding, DeclarationType.CONSTANT) && !isBindingType(binding, DeclarationType.VARIABLE)) {
                    this.diagnostics.push({
                        severity: DiagnosticSeverity.Error,
                        range: range,
                        message: "Not a variable or constant: " + identifier.text,
                        source: 'XULE semantic checker'
                    });
                }
            } else {
                this.visitChildren(ctx);
            }
        }
    };

    visitOutputAttribute = (ctx: OutputAttributeContext) => {
        const prev = this.localVariables;
        this.localVariables = { ...this.localVariables, 'error': {} };
        try {
            this.visitChildren(ctx);
        } finally {
            this.localVariables = prev;
        }
    };

    protected lookupIgnoreCase(name: string, ctx: ExpressionContext) {
        function lookup(binding) {
            return binding.name.toString().toLowerCase() == name;
        }
        return this.symbolTable.lookup(lookup, ctx);
    }

    private checkFunctionCall(ctx: ExpressionContext) {
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
                    severity: DiagnosticSeverity.Error,
                    range: range,
                    message: "Unknown function: " + identifier.text,
                    source: 'XULE semantic checker'
                });
            } else if (binding && !isBindingType(binding, DeclarationType.FUNCTION)) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: range,
                    message: "Not a function: " + identifier.text,
                    source: 'XULE semantic checker'
                });
            }
        }
        ctx.parametersList().children.forEach(x => this.visit(x));
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
    "duration": {},
    "entry-point-namespace": {},
    "exists": {},
    "first": {},
    "first-value": {},
    "forever": {},
    "json-data": {},
    "last": {},
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
    "$ruleVersion": {},
    //The following are actually constants or keywords, but for know we don't need to distinguish them
    "inf": {},
    "none": {},
    "skip": {}
};