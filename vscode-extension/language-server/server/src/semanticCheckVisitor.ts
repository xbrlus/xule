import {AbstractParseTreeVisitor, ParseTree, TerminalNode} from "antlr4ts/tree";
import {XULEParserVisitor} from "./parser/XULEParserVisitor";
import {Diagnostic, DiagnosticSeverity} from "vscode-languageserver";
import {Binding, FunctionInfo, IdentifierInfo, IdentifierType, PropertyInfo, SymbolTable} from "./symbols";
import {
    AssertionContext,
    ExpressionContext,
    FilterContext,
    FunctionDeclarationContext,
    NavigationWhereClauseContext,
    OutputAttributeContext,
    ParametersListContext,
    PropertyAccessContext,
    VariableReadContext
} from "./parser/XULEParser";
import {Range, TextDocument} from "vscode-languageserver-textdocument";
import {ParserRuleContext} from "antlr4ts";

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
    checkFunctions = true;
    checkProperties = true;
    checkVariables = true;

    constructor(public diagnostics: Diagnostic[], protected symbolTable: SymbolTable, protected document: TextDocument) {
        super();
    }

    protected defaultResult(): any {
        return undefined;
    }

    visitAssertion = (ctx: AssertionContext) => {
        if(ctx.expression().length == 0) {
            let range = this.getRange(ctx.ASSERT());
            this.diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: range,
                message: `Assertions must contain at least one expression`,
                source: 'XULE semantic checker'
            });
        }
        return this.visitChildren(ctx);
    };

    visitExpression = (ctx: ExpressionContext) => {
        if(ctx.propertyAccess().length > 0) {
            this.visitExpression(ctx.expression(0));
            this.checkPropertyAccess(ctx.propertyAccess());
        } else if(ctx.parametersList()) {
            const expression = ctx.expression(0);
            const identifier = expression.variableRead();
            const parametersList = ctx.parametersList();
            if(identifier) {
                this.checkFunctionCall(identifier, expression, parametersList);
            } else {
                this.visitExpression(expression);
            }
            this.visit(parametersList);
        } else {
            let identifier = ctx.variableRead();
            if(identifier) {
                let variableName = identifier.text.toLowerCase();
                if(variableName.startsWith("$")) {
                    this.checkVariableAccess(variableName, ctx, identifier);
                } else {
                    this.checkAttribute(variableName, ctx, identifier);
                }
            } else {
                this.visitChildren(ctx);
            }
        }
    };

    protected checkVariableAccess(variableName: string, ctx: ParseTree, identifier: ParseTree) {
        if(!this.checkVariables) {
            return;
        }
        let binding = this.lookupIgnoreCase(variableName, ctx);
        const range = this.getRange(identifier);
        if (!binding && !this.localVariables[variableName]) {
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

    protected checkAttribute(variableName: string, ctx: ParseTree, identifier: ParseTree) {
        //TODO
    }

    private getRange(parseTree: ParseTree): Range {
        if(this.document) {
            if(parseTree instanceof ParserRuleContext) {
                return {
                    start: this.document.positionAt(parseTree.start.startIndex),
                    end: this.document.positionAt(parseTree.stop.stopIndex + 1)
                };
            } else if(parseTree instanceof TerminalNode) {
                return {
                    start: this.document.positionAt(parseTree.symbol.startIndex),
                    end: this.document.positionAt(parseTree.symbol.stopIndex + 1)
                };
            }
        }
        return { start: null, end: null };
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

    protected lookupIgnoreCase(name: string, ctx: ParseTree) {
        function lookup(binding) {
            return binding.name.toString().toLowerCase() == name;
        }
        return this.symbolTable.lookup(lookup, ctx);
    }

    protected checkFunctionCall(identifier: VariableReadContext, ctx: ExpressionContext, parametersList: ParametersListContext) {
        if(!this.checkFunctions) {
            return;
        }
        let functionName = identifier.text.toLowerCase();
        const range = this.getRange(identifier);
        if (functionName.startsWith("$")) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: range,
                message: "Invalid function name: " + identifier.text,
                source: 'XULE semantic checker'
            });
        } else {
            let binding = this.lookupIgnoreCase(functionName, ctx);
            let wnf = wellKnownFunctions[functionName];
            if (!binding && !wnf) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Warning,
                    range: range,
                    message: "Unknown function: " + identifier.text,
                    source: 'XULE semantic checker'
                });
            } else if (binding && !wnf && !bindingInfo(binding, IdentifierType.FUNCTION)) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Warning,
                    range: range,
                    message: "Not a function: " + identifier.text,
                    source: 'XULE semantic checker'
                });
            } else {
                let functionInfo: FunctionInfo = wnf || bindingInfo(binding, IdentifierType.FUNCTION);
                this.checkArity(functionInfo, parametersList);
            }
        }
    }

    protected checkPropertyAccess(propertyPath: PropertyAccessContext[]) {
        propertyPath.forEach(p => {
            if(this.checkProperties && this.checkPropertyExists(p)) {
                this.checkPropertyArity(p);
            }
            if(p.parametersList()) {
                this.visit(p.parametersList());
            }
        });
    }

    private checkPropertyArity(p: PropertyAccessContext) {
        let identifier = p.propertyRef();
        let rawPropertyName = identifier.text;
        let propertyName = rawPropertyName.toLowerCase();
        let property = wellKnownProperties[propertyName];
        if(!property) {
            return;
        }
        let parameters = p.parametersList() ? p.parametersList().expression() : [];
        let arity = property.arity as any;
        let range = this.getRange(p.parametersList() || identifier);
        if (typeof (arity) === "number" && arity != parameters.length) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: range,
                message: `${rawPropertyName} requires exactly ${arity} parameters`,
                source: 'XULE semantic checker'
            });
        } else if (arity) {
            if (typeof (arity.min) === 'number' && parameters.length < arity.min) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: range,
                    message: `${rawPropertyName} requires at least ${arity.min} parameters`,
                    source: 'XULE semantic checker'
                });
            }
            if (typeof (arity.max) === 'number' && parameters.length > arity.max) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: range,
                    message: `${rawPropertyName} requires at most ${arity.max} parameters`,
                    source: 'XULE semantic checker'
                });
            }
        }
    }

    private checkPropertyExists(p: PropertyAccessContext) {
        let identifier = p.propertyRef();
        let rawPropertyName = identifier.text;
        let propertyName = rawPropertyName.toLowerCase();
        let property = wellKnownProperties[propertyName];
        if (!property) {
            let range = this.getRange(identifier);
            this.diagnostics.push({
                severity: DiagnosticSeverity.Warning,
                range: range,
                message: "Unknown property: " + rawPropertyName,
                source: 'XULE semantic checker'
            });
            return false;
        }
        return true;
    }

    protected checkArity(functionInfo: FunctionInfo, parametersList: ParametersListContext) {
        const range = this.getRange(parametersList);
        if (typeof (functionInfo.arity) === 'number') {
            if (functionInfo.arity != parametersList.expression().length) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: range,
                    message: `Expected exactly ${functionInfo.arity} parameters`,
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
    "dict": new FunctionInfo(),
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

export const wellKnownProperties: { [name: string]: PropertyInfo } = {
    "abs": new PropertyInfo(0),
    "all": new PropertyInfo(0),
    "any": new PropertyInfo(0),
    "arc-name": new PropertyInfo(0),
    "arcrole": new PropertyInfo(0),
    "arcrole-description": new PropertyInfo(0),
    "arcrole-uri": new PropertyInfo(0),
    "aspects": new PropertyInfo(0),
    "attribute": new PropertyInfo(1),
    "avg": new PropertyInfo(0),
    "balance": new PropertyInfo(0),
    "base-type": new PropertyInfo(0),
    "concept": new PropertyInfo({ min: 0, max: 1 }),
    "concept-names": new PropertyInfo(0),
    "concepts": new PropertyInfo(0),
    "contains": new PropertyInfo(1),
    "count": new PropertyInfo(0),
    "cube": new PropertyInfo(2),
    "cube-concept": new PropertyInfo(0),
    "cubes": new PropertyInfo(0),
    "data-type": new PropertyInfo(0),
    "day": new PropertyInfo(0),
    "days": new PropertyInfo(0),
    "decimals": new PropertyInfo(0),
    "default": new PropertyInfo(0),
    "denominator": new PropertyInfo(0),
    "description": new PropertyInfo(0),
    "difference": new PropertyInfo(1),
    "dimension": new PropertyInfo(1),
    "dimensions": new PropertyInfo(0),
    "dimensions-explicit": new PropertyInfo(0),
    "dimensions-typed": new PropertyInfo(0),
    "drs-role": new PropertyInfo(0),
    "dts-document": new PropertyInfo(0),
    "effective-weight": new PropertyInfo(2),
    "effective-weight-network": new PropertyInfo({ min: 2, max: 3 }),
    "end": new PropertyInfo(0),
    "entity": new PropertyInfo(0),
    "entry-point": new PropertyInfo(0),
    "entry-point-namespace": new PropertyInfo(0),
    "enumerations": new PropertyInfo(0),
    "facts": new PropertyInfo(0),
    "first": new PropertyInfo(0),
    "has-enumerations": new PropertyInfo(0),
    "has-key": new PropertyInfo(1),
    "id": new PropertyInfo(0),
    "index": new PropertyInfo(1),
    "index-of": new PropertyInfo(1),
    "inline-display-value": new PropertyInfo(0),
    "inline-format": new PropertyInfo(0),
    "inline-hidden": new PropertyInfo(0),
    "inline-negated": new PropertyInfo(0),
    "inline-scale": new PropertyInfo(0),
    "intersect": new PropertyInfo(1),
    "is-abstract": new PropertyInfo(0),
    "is-fact": new PropertyInfo(0),
    "is-monetary": new PropertyInfo(0),
    "is-nil": new PropertyInfo(0),
    "is-numeric": new PropertyInfo(0),
    "is-subset": new PropertyInfo(1),
    "is-superset": new PropertyInfo(1),
    "is-type": new PropertyInfo(1),
    "join": new PropertyInfo({ min: 1, max: 2 }),
    "keys": new PropertyInfo({ min: 0, max: 1 }),
    "label": new PropertyInfo({ min: 0, max: 2 }),
    "lang": new PropertyInfo(0),
    "last": new PropertyInfo(0),
    "last-index-of": new PropertyInfo(1),
    "length": new PropertyInfo(0),
    "link-name": new PropertyInfo(0),
    "local-name": new PropertyInfo(0),
    "log10": new PropertyInfo(0),
    "lower-case": new PropertyInfo(0),
    "max": new PropertyInfo(0),
    "min": new PropertyInfo(0),
    "mod": new PropertyInfo(1),
    "month": new PropertyInfo(0),
    "name": new PropertyInfo(0),
    "namespace-uri": new PropertyInfo(0),
    "network": new PropertyInfo(0),
    "networks": new PropertyInfo({ min: 0, max: 2 }),
    "number": new PropertyInfo(0),
    "numerator": new PropertyInfo(0),
    "order": new PropertyInfo(0),
    "part-by-name": new PropertyInfo(1),
    "part-value": new PropertyInfo(0),
    "parts": new PropertyInfo(0),
    "period": new PropertyInfo(0),
    "period-type": new PropertyInfo(0),
    "power": new PropertyInfo(1),
    "preferred-label": new PropertyInfo(0),
    "primary-concepts": new PropertyInfo(0),
    "prod": new PropertyInfo(0),
    "references": new PropertyInfo(1),
    "relationships": new PropertyInfo(0),
    "role": new PropertyInfo(0),
    "role-description": new PropertyInfo(0),
    "role-uri": new PropertyInfo(0),
    "roots": new PropertyInfo(0),
    "round": new PropertyInfo(1),
    "scheme": new PropertyInfo(0),
    "signum": new PropertyInfo(0),
    "sort": new PropertyInfo({ min: 0, max: 1 }),
    "source": new PropertyInfo(0),
    "source-concepts": new PropertyInfo(0),
    "source-name": new PropertyInfo(0),
    "split": new PropertyInfo(1),
    "start": new PropertyInfo(0),
    "stdev": new PropertyInfo(0),
    "string": new PropertyInfo(0),
    "substitution": new PropertyInfo(0),
    "substring": new PropertyInfo({ min: 1, max: 2 }),
    "sum": new PropertyInfo(0),
    "symmetric-difference": new PropertyInfo(1),
    "target": new PropertyInfo(0),
    "target-concepts": new PropertyInfo(0),
    "target-name": new PropertyInfo(0),
    "text": new PropertyInfo(0),
    "to-dict": new PropertyInfo(0),
    "to-json": new PropertyInfo(0),
    "to-list": new PropertyInfo(0),
    "to-qname": new PropertyInfo(0),
    "to-set": new PropertyInfo(0),
    "trim": new PropertyInfo(),
    "trunc": new PropertyInfo({ min: 0, max: 1 }),
    "union": new PropertyInfo(1),
    "unit": new PropertyInfo(0),
    "upper-case": new PropertyInfo(0),
    "uri": new PropertyInfo(0),
    "used-on": new PropertyInfo(0),
    "values": new PropertyInfo(0),
    "weight": new PropertyInfo(0),
    "year": new PropertyInfo(0),
};

export const wellKnownOutputAttributes = [
    "message", "rule-suffix", "rule-focus", "severity"
];