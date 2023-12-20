import {AbstractParseTreeVisitor, ParseTree, TerminalNode} from "antlr4ts/tree";
import {XULEParserVisitor} from "./parser/XULEParserVisitor";
import {Diagnostic, DiagnosticSeverity} from "vscode-languageserver";
import {
    bindingInfo,
    FunctionInfo,
    IdentifierType,
    OutputAttributeInfo,
    PropertyInfo,
    SymbolTable,
    VariableInfo,
    wellKnownVariables
} from "./symbols";
import {
    AssertionContext,
    AtIdentifierContext,
    ConstantDeclarationContext,
    ExpressionContext,
    FactsetBodyContext,
    FilterContext,
    FunctionDeclarationContext,
    NavigationWhereClauseContext,
    OutputAttributeContext, OutputContext,
    ParametersListContext,
    PropertyAccessContext, RoleContext,
    VariableReadContext,
    XuleFileContext
} from "./parser/XULEParser";
import {TextDocument} from "vscode-languageserver-textdocument";
import {ParserRuleContext} from "antlr4ts";
import {getRange} from "./utils";

export class SemanticCheckVisitor extends AbstractParseTreeVisitor<any> implements XULEParserVisitor<any> {

    localVariables = {};
    checkFunctions = true;
    checkProperties = true;
    checkVariables = true;
    checkQNames = true;

    constructor(public diagnostics: Diagnostic[], protected symbolTable: SymbolTable, protected document: TextDocument) {
        super();
    }

    protected defaultResult(): any {
        return undefined;
    }

    visitXuleFile = (ctx: XuleFileContext) => {
        this.symbolTable.errors.forEach(e => {
            let file = e.scope;
            while(!(file instanceof XuleFileContext)) {
                if(file) {
                    file = file.parent;
                } else {
                    break;
                }
            }
            if(file == ctx) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: getRange(e.scope),
                    message: e.message,
                    source: 'XULE semantic checker'
                });
            }
        });
        return this.visitChildren(ctx);
    };

    visitAssertion = (ctx: AssertionContext) => {
        let assertionsWithTheSameName = ctx.parent.children.filter(c =>
            c instanceof AssertionContext && c.ASSERT_RULE_NAME().text == ctx.ASSERT_RULE_NAME().text);
        if(assertionsWithTheSameName.length > 1) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: getRange(ctx.ASSERT_RULE_NAME()),
                message: "Assertion defined more than once",
                source: 'XULE semantic checker'
            });
        }
        return this.visitChildren(ctx);
    };

    visitConstantDeclaration = (ctx: ConstantDeclarationContext) => {
        let bindings = this.symbolTable.lookupAll(ctx.identifier().text, ctx);
        if(bindings) {
            bindings = bindings.filter(b => bindingInfo(b, IdentifierType.CONSTANT));
        }
        if(bindings && bindings.length > 1) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: getRange(ctx.identifier()),
                message: "Constant defined more than once",
                source: 'XULE semantic checker'
            });
        }
        if(!ctx.identifier().text.startsWith("$")) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: getRange(ctx.identifier()),
                message: "Constant names must start with the dollar character ($)",
                source: 'XULE semantic checker'
            });
        }
        return this.visit(ctx.expression());
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
                let name = identifier.text;
                if(name.startsWith("$")) {
                    this.checkVariableAccess(name, ctx, identifier);
                } else {
                    this.checkQName(name, ctx, identifier);
                }
            } else {
                this.visitChildren(ctx);
            }
        }
    };

    visitFactsetBody = (ctx: FactsetBodyContext) => {
        ctx.expression().forEach(e => {
            let vr = e.variableRead();
            if(vr && !vr.text.startsWith("@")) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: getRange(ctx),
                    message: "Malformed factset",
                    source: 'XULE semantic checker'
                });
            }
        });
        this.visitChildren(ctx);
    };

    visitAtIdentifier = (ctx: AtIdentifierContext) => {
        let name = ctx.text;
        while(name.startsWith("@")) {
            name = name.substring(1);
        }
        let lower = name.toLowerCase();
        if(dimensions[lower]) {
            return;
        }
        this.checkQName(name, ctx, ctx);
    };

    protected checkVariableAccess(variableName: string, ctx: ParseTree, identifier: ParseTree) {
        if(!this.checkVariables) {
            return;
        }
        const binding = this.symbolTable.lookup(variableName, ctx);
        const range = getRange(identifier);
        if (!binding && !this.localVariables[variableName]) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Warning,
                range: range,
                message: `Unknown variable or constant: ${identifier.text}`,
                source: 'XULE semantic checker'
            });
        } else if (binding && !bindingInfo(binding, IdentifierType.CONSTANT) && !bindingInfo(binding, IdentifierType.VARIABLE)) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Warning,
                range: range,
                message: `Not a variable or constant: ${identifier.text}`,
                source: 'XULE semantic checker'
            });
        }
    }

    protected checkQName(name: string, ctx: ParseTree, identifier: ParserRuleContext) {
        if(!this.checkQNames) {
            return;
        }
        let namespace = "";
        if(name.indexOf(':') >= 0) {
            let parts = name.split(':');
            namespace = parts[0];
            name = parts.slice(1).join(":");
        }
        let ns = this.symbolTable.lookupNamespace(namespace);
        if(ns && ns.namespace.names) {
            if(!ns.namespace.names.find(n => n.localName == name)) {
                if(namespace ||
                    (!wellKnownVariables[name] && !this.localVariables[name] && wellKnownOutputAttributes.indexOf(name.toLowerCase()) < 0)) {
                    let bindings = this.lookupIgnoreCase(name, identifier);
                    if(!bindings || !bindings.find(
                        b => b.name == name ||
                            b.meaning.find(m => m instanceof OutputAttributeInfo) ||
                            b.meaning.find(m => m instanceof VariableInfo && m.ignoreCase))) {
                        let message = `Unknown local name: ${name} in namespace ${ns.namespace.uri}`;
                        if(ns.namespace.path) {
                            message += ` (loaded from ${ns.namespace.path})`;
                        } else {
                            message += " (built-in)";
                        }
                        this.diagnostics.push({
                            severity: DiagnosticSeverity.Warning,
                            range: getRange(identifier),
                            message: message,
                            source: 'XULE semantic checker'
                        });
                    }
                }
            }
        } else if(namespace) {
            let startIndex = identifier.start.startIndex + identifier.text.indexOf(namespace);
            let endIndex = startIndex + namespace.length;
            this.diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: {
                    start: this.document.positionAt(startIndex),
                    end: this.document.positionAt(endIndex)
                },
                message: "Unknown namespace: " + namespace,
                source: 'XULE semantic checker'
            });
        } else {
            if((!wellKnownVariables[name] && !this.localVariables[name] && wellKnownOutputAttributes.indexOf(name.toLowerCase()) < 0)) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Warning,
                    range: getRange(identifier),
                    message: "Unknown attribute: " + name + " and no default namespace set.",
                    source: 'XULE semantic checker'
                });
            }
        }
    }

    visitOutput = (ctx: OutputContext) => {
        let outputsWithTheSameName = ctx.parent.children.filter(c =>
            c instanceof OutputContext && c.OUTPUT_RULE_NAME().text == ctx.OUTPUT_RULE_NAME().text);
        if(outputsWithTheSameName.length > 1) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: getRange(ctx.OUTPUT_RULE_NAME()),
                message: "Output defined more than once",
                source: 'XULE semantic checker'
            });
        }
        return this.visitChildren(ctx);
    };

    visitOutputAttribute = (ctx: OutputAttributeContext) => {
        return this.withLocalVariables({ 'error': {}, 'ok': {}, 'warning': {} }, () => this.visitChildren(ctx));
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

    visitRole = (ctx: RoleContext) => {
        let variable = ctx.variableRead();
        if(variable) {
            //The grammar guarantees that the variable has a name that starts with $, otherwise it's a role name
            this.checkVariableAccess(variable.text, ctx, variable);
            this.checkPropertyAccess(ctx.propertyAccess());
        } else {
            this.visitChildren(ctx);
        }
    }

    visitFunctionDeclaration = (ctx: FunctionDeclarationContext) => {
        let functionName = ctx.identifier().text;
        if(functionName.startsWith("$")) {
            const range = getRange(ctx.identifier());
            this.diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: range,
                message: "Invalid function name: " + ctx.identifier().text,
                source: 'XULE semantic checker'
            });
        }
        let bindings = this.symbolTable.lookupAll(ctx.identifier().text, ctx);
        if(bindings) {
            bindings = bindings.filter(b => bindingInfo(b, IdentifierType.FUNCTION));
        }
        if(bindings && bindings.length > 1) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: getRange(ctx.identifier()),
                message: "Function defined more than once",
                source: 'XULE semantic checker'
            });
        }
        return this.visitChildren(ctx);
    };

    protected lookupIgnoreCase(name: string, ctx: ParseTree) {
        let lower = name.toLowerCase();
        function lookup(binding) {
            return binding.name.toString().toLowerCase() == lower;
        }
        return this.symbolTable.lookupAll(lookup, ctx);
    }
    protected checkFunctionCall(identifier: VariableReadContext, ctx: ExpressionContext, parametersList: ParametersListContext) {
        if(!this.checkFunctions) {
            return;
        }
        let functionName = identifier.text;
        const range = getRange(identifier);
        if (functionName.startsWith("$")) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: range,
                message: "Invalid function name: " + identifier.text,
                source: 'XULE semantic checker'
            });
        } else {
            let binding = this.symbolTable.lookup(functionName, ctx);
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
            if(this.checkProperties) {
                this.checkSinglePropertyAccess(p);
            } else if(p.parametersList()) {
                this.visit(p.parametersList());
            }
        });
    }

    private checkSinglePropertyAccess(p: PropertyAccessContext) {
        let identifier = p.propertyRef();
        let propertyName = identifier.text;
        let property = wellKnownProperties[propertyName];
        if(!property) {
            let range = getRange(identifier);
            this.diagnostics.push({
                severity: DiagnosticSeverity.Warning,
                range: range,
                message: "Unknown property: " + propertyName,
                source: 'XULE semantic checker'
            });
            return;
        }
        let parameters = p.parametersList() ? p.parametersList().block().length : 0;
        let arity = property.arity as any;
        let range = getRange(p.parametersList() || identifier);
        if (typeof (arity) === "number" && arity != parameters) {
            this.diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: range,
                message: `${propertyName} requires exactly ${arity} parameters`,
                source: 'XULE semantic checker'
            });
        } else if (arity) {
            if (typeof (arity.min) === 'number' && parameters < arity.min) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: range,
                    message: `${propertyName} requires at least ${arity.min} parameters`,
                    source: 'XULE semantic checker'
                });
            }
            if (typeof (arity.max) === 'number' && parameters > arity.max) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: range,
                    message: `${propertyName} requires at most ${arity.max} parameters`,
                    source: 'XULE semantic checker'
                });
            }
        }
        if(p.parametersList()) {
            let parameters = p.parametersList().block();
            parameters.forEach((b, i) => {
                if((propertyName == 'cube' && i == 1) ||
                    (propertyName == 'effective-weight-network' && i == 2)) {
                    if(b.assignment() || !b.expression().variableRead()) {
                        this.diagnostics.push({
                            severity: DiagnosticSeverity.Error,
                            range: getRange(b),
                            message: "Not a role: " + b.text,
                            source: 'XULE semantic checker'
                        });
                    }
                } else {
                    this.visit(b);
                }
            });
        }
    }

    protected checkArity(functionInfo: FunctionInfo, parametersList: ParametersListContext) {
        const range = getRange(parametersList);
        let arity = parametersList.block().length;
        if (typeof (functionInfo.arity) === 'number') {
            if (functionInfo.arity != arity) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: range,
                    message: `Expected exactly ${functionInfo.arity} parameters`,
                    source: 'XULE semantic checker'
                });
            }
        } else if (functionInfo.arity) {
            let arity = functionInfo.arity as any;
            if (typeof (arity.min) === 'number' && arity < arity.min) {
                this.diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    range: range,
                    message: `Expected at least ${arity.min} parameters`,
                    source: 'XULE semantic checker'
                });
            }
            if (typeof (arity.max) === 'number' && arity > arity.max) {
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
    "alignment": new FunctionInfo(0),
    "all": new FunctionInfo(1),
    "all-labels": new FunctionInfo({ min: 1, max: 3 }),
    "all-references": new FunctionInfo({ min: 1, max: 2 }),
    "any": new FunctionInfo(1),
    "arcrole": new FunctionInfo(1),
    "arcroles": new FunctionInfo(1),
    "arcrole-description": new FunctionInfo(1),
    "arcrole-uri": new FunctionInfo(1),
    "arc-name": new FunctionInfo(1),
    "aspects": new FunctionInfo(1),
    "attribute": new FunctionInfo(2),
    "avg": new FunctionInfo(1),
    "balance": new FunctionInfo(1),
    "base-type": new FunctionInfo(1),
    "clark": new FunctionInfo(1),
    "concept": new FunctionInfo(1),
    "concept-names": new FunctionInfo(1),
    "concepts": new FunctionInfo(1),
    "contains": new FunctionInfo(2),
    "content": new FunctionInfo(1),
    "count": new FunctionInfo(1),
    "cube": new FunctionInfo(3),
    "csv-data": new FunctionInfo({ min: 2, max: 4 }),
    "cube-concept": new FunctionInfo(1),
    "data-type": new FunctionInfo(1),
    "date": new FunctionInfo(1),
    "day": new FunctionInfo(1),
    "days": new FunctionInfo(1),
    "decimal": new FunctionInfo(1),
    "decimals": new FunctionInfo(1),
    "default": new FunctionInfo(1),
    "dict": new FunctionInfo(),
    "dimension": new FunctionInfo(2),
    "dimension-type": new FunctionInfo(1),
    "dimensions": new FunctionInfo(1),
    "dimensions-explicit": new FunctionInfo(1),
    "dimensions-typed": new FunctionInfo(1),
    "document-location": new FunctionInfo(1),
    "drs-role": new FunctionInfo(1),
    "dts-document-locations": new FunctionInfo(1),
    "duration": new FunctionInfo(2),
    "end": new FunctionInfo(1),
    "entity": new FunctionInfo(2),
    "entry-point-namespace": new FunctionInfo(1),
    "entry-point": new FunctionInfo(1),
    "enumerations": new FunctionInfo(1), 
    "excel-data": new FunctionInfo({ min: 1, max: 4 }),
    "exists": new FunctionInfo(1),
    "fact": new FunctionInfo(1),
    "facts": new FunctionInfo(1),
    "first": new FunctionInfo(1),
    "footnotes": new FunctionInfo(1),
    "first-value": new FunctionInfo(),
    "first-value-or-none": new FunctionInfo(),
    "forever": new FunctionInfo(0),
    "has-enumerations": new FunctionInfo(1),
    "has-key": new FunctionInfo(2),
    "id": new FunctionInfo(1),
    "index": new FunctionInfo(2),
    "instance": new FunctionInfo({ min: 0, max: 1 }),
    "inline-ancestors": new FunctionInfo(1),
    "inline-children": new FunctionInfo(1),
    "inline-descendants": new FunctionInfo(1),
    "inline-display-value": new FunctionInfo(1),
    "inline-format": new FunctionInfo(1),
    "inline-hidden": new FunctionInfo(1),
    "inline-negated": new FunctionInfo(1),
    "inline-parent": new FunctionInfo(1),
    "inline-scale": new FunctionInfo(1),
    "inline-transform": new FunctionInfo({ min: 2, max: 3 }),
    "int": new FunctionInfo(1),
    "intersect": new FunctionInfo(2),
    "is_abstract": new FunctionInfo(1),
    "is_base": new FunctionInfo(),
    "index-of": new FunctionInfo(2),
    "join": new FunctionInfo({ min: 2, max: 3 }),
    "json-data": new FunctionInfo(1),
    "keys": new FunctionInfo({ min: 1, max: 2 }),
    "label": new FunctionInfo({ min: 1, max: 3 }),
    "lang": new FunctionInfo(1),
    "last": new FunctionInfo(1),
    "last-index-of": new FunctionInfo(2),
    "length": new FunctionInfo(1),
    "link-name": new FunctionInfo(1),
    "local-name": new FunctionInfo(1),
    "list": new FunctionInfo(),
    "log10": new FunctionInfo(1),
    "lower-case": new FunctionInfo(1),
    "max": new FunctionInfo(1),
    "min": new FunctionInfo(1),
    "missing": new FunctionInfo(1),
    "mod": new FunctionInfo(2),
    "month": new FunctionInfo(1),
    "name": new FunctionInfo(1),
    "namespaces": new FunctionInfo(1),
    "namespace-map": new FunctionInfo(1),
    "network": new FunctionInfo(1),
    "networks": new FunctionInfo({ min: 1, max: 3 }),
    "number": new FunctionInfo(1),
    "numerator": new FunctionInfo(1),
    "order": new FunctionInfo(1),
    "part-by-name": new FunctionInfo(2),
    "part-elements": new FunctionInfo(1),
    "part-value": new FunctionInfo(1),
    "parts": new FunctionInfo(1),
    "plain-string": new FunctionInfo(1),
    "power": new FunctionInfo(2),
    "preferred-label": new FunctionInfo(1),
    "primary-concepts": new FunctionInfo(1),
    "prod": new FunctionInfo(1),
    "qname": new FunctionInfo(2),
    "references": new FunctionInfo(({ min: 1, max: 2 })),
    "regex-match": new FunctionInfo(2),
    "regex-match-all": new FunctionInfo(2),
    "regex-match-string": new FunctionInfo({ min: 2, max: 3 }),
    "regex-match-string-all": new FunctionInfo({ min: 2, max: 3 }),
    "random": new FunctionInfo({ min: 0, max: 1 }),
    "range": new FunctionInfo({ min: 1, max: 3 }),
    "relationships": new FunctionInfo(1),
    "role": new FunctionInfo(1),
    "roles": new FunctionInfo(1),
    "roots": new FunctionInfo(1),
    "round": new FunctionInfo(2),
    "rule-name": new FunctionInfo(0),
    "scheme": new FunctionInfo(1),
    "set": new FunctionInfo(),
    "signum": new FunctionInfo(1),
    "sort": new FunctionInfo(1),
    "source": new FunctionInfo(1),
    "source-concepts": new FunctionInfo(1),
    "source-name": new FunctionInfo(1),
    "split": new FunctionInfo(2),
    "start": new FunctionInfo(1),
    "string": new FunctionInfo(1),
    "substitution": new FunctionInfo(1),
    "substring": new FunctionInfo({ min: 2, max: 3 }),
    "sum": new FunctionInfo(1),
    "stdev": new FunctionInfo(1),
    "target": new FunctionInfo(1),
    "target-concepts": new FunctionInfo(1),
    "target-name": new FunctionInfo(1),
    "taxonomy": new FunctionInfo({ min: 0, max: 1 }),
    "text": new FunctionInfo(1),
    "time-span": new FunctionInfo(1),
    "to-csv": new FunctionInfo({ min: 1, max: 2 }),
    "to-dict": new FunctionInfo(1),
    "to-json": new FunctionInfo(1),
    "to-list": new FunctionInfo(1),
    "to-qname": new FunctionInfo(1),
    "to-set": new FunctionInfo(1),
    "trim": new FunctionInfo({ min: 1, max: 2 }),
    "trunc": new FunctionInfo({ min: 1, max: 2 }),
    "unit": new FunctionInfo({ min: 1, max: 2 }),
    "upper-case": new FunctionInfo(1),
    "uri": new FunctionInfo(1),
    "values": new FunctionInfo(1),
    "weight": new FunctionInfo(1),
    "xml-data-flat": new FunctionInfo({ min: 3, max: 5 }),
    "year": new FunctionInfo(1)
};

export const wellKnownProperties: { [name: string]: PropertyInfo } = {
    "abs": new PropertyInfo(0),
    "all": new PropertyInfo(0),
    "all-labels": new PropertyInfo({ min: 0, max: 2 }),
    "all-references": new PropertyInfo({ min: 0, max: 1 }),
    "any": new PropertyInfo(0),
    "arc-name": new PropertyInfo(0),
    "arcrole": new PropertyInfo(0),
    "arcroles": new PropertyInfo(0),
    "arcrole-description": new PropertyInfo(0),
    "arcrole-uri": new PropertyInfo(0),
    "aspects": new PropertyInfo(0),
    "attribute": new PropertyInfo(1),
    "avg": new PropertyInfo(0),
    "balance": new PropertyInfo(0),
    "base-type": new PropertyInfo(0),
    "clark": new PropertyInfo(0),
    "concept": new PropertyInfo({ min: 0, max: 1 }),
    "concept-names": new PropertyInfo(0),
    "concepts": new PropertyInfo(0),
    "contains": new PropertyInfo(1),
    "content": new PropertyInfo(0),
    "count": new PropertyInfo(0),
    "cube": new PropertyInfo({ min: 1, max: 2 }),
    "cube-concept": new PropertyInfo(0),
    "cubes": new PropertyInfo(0),
    "data-type": new PropertyInfo(0),
    "date": new PropertyInfo(0),
    "day": new PropertyInfo(0),
    "days": new PropertyInfo(0),
    "decimal": new PropertyInfo(0),
    "decimals": new PropertyInfo(0),
    "default": new PropertyInfo(0),
    "denominator": new PropertyInfo(0),
    "description": new PropertyInfo(0),
    "difference": new PropertyInfo(1),
    "dimension": new PropertyInfo(1),
    "dimension-type": new PropertyInfo(0),
    "dimensions": new PropertyInfo(0),
    "dimensions-explicit": new PropertyInfo(0),
    "dimensions-typed": new PropertyInfo(0),
    "document-location": new PropertyInfo(0),
    "drs-role": new PropertyInfo(0),
    "dts-document-locations": new PropertyInfo(0),
    "effective-weight": new PropertyInfo(2),
    "effective-weight-network": new PropertyInfo({ min: 2, max: 3 }),
    "end": new PropertyInfo(0),
    "entity": new PropertyInfo(0),
    "entry-point": new PropertyInfo(0),
    "entry-point-namespace": new PropertyInfo(0),
    "enumerations": new PropertyInfo(0),
    "fact": new PropertyInfo(0),
    "facts": new PropertyInfo(0),
    "first": new PropertyInfo(0),
    "footnotes": new PropertyInfo(0),
    "has-enumerations": new PropertyInfo(0),
    "has-key": new PropertyInfo(1),
    "id": new PropertyInfo(0),
    "index": new PropertyInfo(1),
    "index-of": new PropertyInfo(1),
    "inline-ancestors": new PropertyInfo(0),
    "inline-children": new PropertyInfo(0),
    "inline-descendants": new PropertyInfo(0),
    "inline-display-value": new PropertyInfo(0),
    "inline-format": new PropertyInfo(0),
    "inline-hidden": new PropertyInfo(0),
    "inline-negated": new PropertyInfo(0),
    "inline-parent": new PropertyInfo(0),
    "inline-scale": new PropertyInfo(0),
    "inline-transform": new PropertyInfo({ min: 1, max: 2 }),
    "instance": new PropertyInfo(0),
    "int": new PropertyInfo(0),
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
    "namespaces": new PropertyInfo(0),
    "namespace-map": new PropertyInfo(0),
    "network": new PropertyInfo(0),
    "networks": new PropertyInfo({ min: 0, max: 2 }),
    "number": new PropertyInfo(0),
    "numerator": new PropertyInfo(0),
    "order": new PropertyInfo(0),
    "part-by-name": new PropertyInfo(1),
    "part-elements": new PropertyInfo(0),
    "part-value": new PropertyInfo(0),
    "parts": new PropertyInfo(0),
    "period": new PropertyInfo(0),
    "period-type": new PropertyInfo(0),
    "plain-string": new PropertyInfo(0),
    "power": new PropertyInfo(1),
    "preferred-label": new PropertyInfo(0),
    "primary-concepts": new PropertyInfo(0),
    "prod": new PropertyInfo(0),
    "references": new PropertyInfo({ min: 0, max: 1 }),
    "regex-match": new PropertyInfo(1),
    "regex-match-all": new PropertyInfo(1),
    "regex-match-string": new PropertyInfo({ min: 1, max: 2 }),
    "regex-match-string-all": new PropertyInfo({ min: 1, max: 2 }),
    "relationships": new PropertyInfo(0),
    "role": new PropertyInfo(0),
    "roles": new PropertyInfo(0),
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
    "taxonomy": new PropertyInfo(0),
    "text": new PropertyInfo(0),
    "time-span": new PropertyInfo(0),
    "to-csv": new PropertyInfo({ min: 0, max: 1 }),
    "to-dict": new PropertyInfo(0),
    "to-json": new PropertyInfo(0),
    "to-list": new PropertyInfo(0),
    "to-qname": new PropertyInfo(0),
    "to-set": new PropertyInfo(0),
    "to-xince": new PropertyInfo(0),
    "trim": new PropertyInfo({ min: 0, max: 1 }),
    "trunc": new PropertyInfo({ min: 0, max: 1 }),
    "union": new PropertyInfo(1),
    "unit": new PropertyInfo(0),
    "upper-case": new PropertyInfo(0),
    "uri": new PropertyInfo(0),
    "used-on": new PropertyInfo(0),
    "values": new PropertyInfo(0),
    "weight": new PropertyInfo(0),
    "year": new PropertyInfo(0),
    "_type": new PropertyInfo(0),
};

export const dimensions = {
    "concept": {},
    "cube": {},
    "entity": {},
    "instance": {},
    "period": {},
    "unit": {}
}

export const wellKnownOutputAttributes = [
    "message", "rule-suffix", "rule-focus", "severity", "file-location", "file-content", "file-append"
];