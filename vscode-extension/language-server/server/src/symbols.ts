import {AbstractParseTreeVisitor, ParseTree, ParseTreeVisitor, RuleNode, Tree} from 'antlr4ts/tree';
import {XULEParserVisitor} from './parser/XULEParserVisitor';
import {
    AspectFilterContext,
    AssignedVariableContext,
    ConstantDeclarationContext,
    ForExpressionContext,
    FunctionArgumentContext,
    FunctionDeclarationContext,
    NamespaceDeclarationContext,
    NavigationContext,
    OutputAttributeDeclarationContext,
    TagContext,
    XuleFileContext
} from './parser/XULEParser';
import {ParserRuleContext, RuleContext} from "antlr4ts";

export type Binding = { name: any, meaning: any };
export type Lookup = (obj: Binding) => boolean;

export class Environment {

	public bindings: Binding[] = [];
	constructor(public parent?: Environment) {}

	find(what: string | Lookup): Binding {
		const test = typeof what === "string" ? function (binding: Binding) {
			return binding.name == what
		} : what as Lookup;
		const binding = this.bindings.find(mapping => test(mapping));
		if(binding) {
			return binding;
		} else if(this.parent) {
			return this.parent.find(test);
		} else {
			return undefined;
		}
	}

	findAll(what: string | Lookup): Binding[] {
		const test = typeof what === "string" ? function (binding: Binding) {
			return binding.name == what
		} : what as Lookup;
		const bindings = this.bindings.filter(mapping => test(mapping));
		if(this.parent) {
			return bindings.concat(this.parent.findAll(what));
		} else {
			return bindings;
		}
	}

}

function ensureArray(obj): any[] {
	if(obj instanceof Array) {
		return obj;
	} else {
		return [obj];
	}
}

export type Name = { localName: string } | any;
export class Namespace {
	constructor(public readonly uri: string, public names: Name[] = []) {}
}

export class CompilationUnit extends ParserRuleContext {
	protected files: XuleFileContext[] = [];

	readonly payload: any;
	readonly text: string;

	accept<T>(visitor: XULEParserVisitor<T>): T {
		if(visitor["visitCompilationUnit"]) {
			return visitor["visitCompilationUnit"](this);
		} else {
			return visitor.visitChildren(this);
		}
	}

	get childCount() {
		return this.files.length;
	}

	getChild(i: number): ParseTree {
		return this.files[i];
	}

	setParent(parent: RuleContext): void {
		throw "Not supported";
	}

	add(file: XuleFileContext) {
		file.setParent(this);
		this.files.push(file);
	}
}

export class SymbolTable {
	public symbols: { scope: ParseTree, environment: Environment }[] = [];
	public namespaces: { [name: string]: Namespace } = {};

	constructor(protected globalEnvironment = new Environment()) {}

	lookup(what: string | Lookup, scope: ParseTree) {
		const env = this.lookupEnvironment(scope);
		if(env) {
			return env.find(what);
		}
	}

	lookupAll(what: string | Lookup, scope: ParseTree) {
		const env = this.lookupEnvironment(scope);
		if(env) {
			return env.findAll(what);
		} else {
			return [];
		}
	}

	record(name, meaning, scope: ParseTree, combinator: (binding: Binding, meaning: any) => any = (binding, meaning) => {
		return ensureArray(binding.meaning).concat(ensureArray(meaning));
	}) {
		const info = this.symbols.find(s => s.scope == scope);
		if(info) {
			info.environment.bindings.push({ name: name, meaning: meaning });
		} else {
			const env = new Environment();
			env.parent = this.lookupEnvironment(scope);
			const existing = env.bindings.find(b => b.name == name);
			if(existing) {
				existing.meaning = combinator(existing, meaning);
			} else {
				env.bindings.push({ name: name, meaning: meaning });
			}
			this.symbols.push({ scope: scope, environment: env });
		}
	}

	lookupEnvironment(scope: ParseTree): Environment {
		const info = this.symbols.find(s => s.scope == scope);
		if(info) {
			return info.environment;
		} else if(scope.parent) {
			return this.lookupEnvironment(scope.parent);
		} else {
			return this.globalEnvironment;
		}
	}

	lookupNamespace(namespace: string) {
		return this.namespaces[namespace];
	}
}

export enum IdentifierType { CONSTANT, FUNCTION, VARIABLE, OUTPUT_ATTRIBUTE}

export class IdentifierInfo {
	type: IdentifierType
}

export class FunctionInfo extends IdentifierInfo {
	constructor(public arity?: number | { min?: number, max?: number }) {
		super();
		this.type = IdentifierType.FUNCTION;
	}
}

export class PropertyInfo extends FunctionInfo {}

export class VariableInfo extends IdentifierInfo {
	constructor(public isConstant?: boolean) {
		super();
		this.type = isConstant ? IdentifierType.CONSTANT : IdentifierType.VARIABLE;
	}
}

export class OutputAttributeInfo extends IdentifierInfo {
	type = IdentifierType.OUTPUT_ATTRIBUTE;
}

export const initialEnvironment = new Environment();
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
for(let name in wellKnownVariables) {
	initialEnvironment.bindings.push({ name: name, meaning: [new VariableInfo()] });
}

export class SymbolTableVisitor extends AbstractParseTreeVisitor<SymbolTable> implements XULEParserVisitor<SymbolTable> {

    protected symbolTable = new SymbolTable(initialEnvironment);
    protected context: ParseTree = null;
    protected namespaces: Namespace[] = [];

    withSymbolTable(symbolTable: SymbolTable) {
        this.symbolTable = symbolTable;
        return this;
    }

    withInitialContext(context: ParseTree) {
        this.context = context;
        return this;
    }

    withNamespaces(...namespaces: Namespace[]) {
        this.namespaces.push(...namespaces);
        return this;
    }

	protected defaultResult(): SymbolTable {
		return this.symbolTable;
	}

	visitCompilationUnit = (cu: CompilationUnit) => {
		return this.withNewContext(cu, () => this.visitChildren(cu));
	};

	visitXuleFile = (ctx: XuleFileContext) => {
		if(this.context instanceof CompilationUnit) {
			return this.visitChildren(ctx);
		} else {
			return this.withNewContext(ctx, () => this.visitChildren(ctx));
		}
	};

	visitNamespaceDeclaration = (ctx: NamespaceDeclarationContext) => {
		if(ctx.exception) {
			return;
		}
		let localName = ctx.identifier() ? ctx.identifier().text : "";
		this.symbolTable.namespaces[localName] = this.lookupNamespace(ctx.URL().text);
		return this.visitChildren(ctx);
	};

	visitAspectFilter = (ctx: AspectFilterContext) => {
		return this.withNewContext(ctx, () => this.visitChildren(ctx));
	};

	visitConstantDeclaration = (ctx: ConstantDeclarationContext) => {
		this.symbolTable.record(ctx.identifier().text, [new VariableInfo(true)], this.context);
		return this.visitChildren(ctx);
	};

	visitAssignedVariable = (ctx: AssignedVariableContext) => {
		this.symbolTable.record(ctx.identifier().text, [new VariableInfo()], this.context);
		return this.symbolTable;
	};

	visitTag = (ctx: TagContext) => {
		this.symbolTable.record("$" + ctx.identifier().text, [new VariableInfo()], this.context);
		return this.visitChildren(ctx);
	};

	visitForExpression = (ctx: ForExpressionContext) => {
		this.symbolTable.record(ctx.forHead().forVariable().identifier().text, [new VariableInfo()], this.context);
		return this.visitChildren(ctx);
	};

	visitFunctionDeclaration = (ctx: FunctionDeclarationContext) => {
		let functionInfo = new FunctionInfo();
		functionInfo.arity = ctx.functionArgument().length;
		this.symbolTable.record(ctx.identifier().text, [functionInfo], this.context);
		return this.withNewContext(ctx, () => this.visitChildren(ctx));
	};

	visitNavigation = (ctx: NavigationContext) => {
		this.symbolTable.record("$relationship", [new VariableInfo()], ctx);
		return this.visitChildren(ctx);
	};

	protected withNewContext<T>(ctx: RuleNode, fn: () => T): T {
		let context = this.context;
		this.context = ctx;
		try {
			return fn();
		} finally {
			this.context = context;
		}
	}

	visitFunctionArgument = (ctx: FunctionArgumentContext) => {
		this.symbolTable.record(ctx.identifier().text, [new VariableInfo()], this.context);
		return this.visitChildren(ctx);
	};

	visitOutputAttributeDeclaration = (ctx: OutputAttributeDeclarationContext) => {
		this.symbolTable.record(ctx.identifier().text, [new OutputAttributeInfo()], this.context);
		return this.visitChildren(ctx);
	};

	protected lookupNamespace(uri: string) {
		for(let n in this.namespaces) {
			let namespace = this.namespaces[n];
			if(namespace.uri == uri) {
				return namespace;
			}
		}
		return new Namespace(uri);
	}
}