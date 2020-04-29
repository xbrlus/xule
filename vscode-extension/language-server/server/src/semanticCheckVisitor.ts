import {AbstractParseTreeVisitor} from "antlr4ts/tree";
import {XULEParserVisitor} from "./parser/XULEParserVisitor";
import {Diagnostic, DiagnosticSeverity} from "vscode-languageserver";
import {SymbolTable} from "./symbols";
import {ExpressionContext} from "./parser/XULEParser";
import {TextDocument} from "vscode-languageserver-textdocument";

export class SemanticCheckVisitor  extends AbstractParseTreeVisitor<any> implements XULEParserVisitor<any> {

    constructor(public diagnostics: Diagnostic[], protected symbolTable: SymbolTable, protected document: TextDocument) {
        super();
    }

    protected defaultResult(): any {
        return undefined;
    }

    visitExpression = (ctx: ExpressionContext) => {
        if(ctx.parametersList()) {
            const expression = ctx.expression(0);
            const identifier = expression.variableRead();
            if(identifier) {
                let functionName = identifier.text.toLowerCase();
                let lookup = function (binding) {
                    return binding.name.toString().toLowerCase() == functionName;
                };
                let binding = this.symbolTable.lookup(lookup, ctx);
                if(!binding && !wellKnownFunctions[functionName]) {
                    const range = {
                        start: this.document.positionAt(identifier.start.startIndex),
                        end: this.document.positionAt(identifier.stop.stopIndex + 1)
                    };
                    this.diagnostics.push({
                        severity: DiagnosticSeverity.Error,
                        range: range,
                        message: "Unknown function: " + identifier.text,
                        source: 'XULE semantic checker'
                    });
                }
            }
        }
    };
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