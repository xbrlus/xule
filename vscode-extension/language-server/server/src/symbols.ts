import {AbstractParseTreeVisitor, ParseTree} from 'antlr4ts/tree';
import {XULEParserVisitor} from './parser/XULEParserVisitor';
import {
	AspectFilterContext, AssertionContext, AssignedVariableContext, BlockContext,
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
	readonly payload: any;
	readonly text: string;
	children = [];

	accept<T>(visitor: XULEParserVisitor<T>): T {
		if(visitor["visitCompilationUnit"]) {
			return visitor["visitCompilationUnit"](this);
		} else {
			return visitor.visitChildren(this);
		}
	}

	setParent(parent: RuleContext): void {
		throw "Not supported";
	}

	add(file: XuleFileContext) {
		file.setParent(this);
		this.children.push(file);
	}
}

export class SymbolTable {
	public symbols: { scope: ParseTree, environment: Environment }[] = [];
	public namespaces: { [name: string]: { namespace: Namespace, definedAt?: ParseTree }} = {};
	public errors: { message: string, scope: ParseTree }[] = [];

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

	public definedAt: { line: number, column: number };

	constructor(public isConstant?: boolean, public ignoreCase?: boolean) {
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
	"credit": {},
	"debit": {},
	"duration": {},
	"error": {},
	"inf": { isConstant: true, ignoreCase: true },
	"instant": {},
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
	let info = wellKnownVariables[name];
	initialEnvironment.bindings.push({ name: name, meaning: [new VariableInfo(info.isConstant, info.ignoreCase)] });
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
		//Be sure to restore the context on exit
		return this.withNewContext(this.context, () => {
			//We coalesce all imported files into a global context, the compilation unit.
			//Instead, we give the main file – the last one among the compilation unit's children – a more specific scope,
			//so that local definitions can shadow imported definitions.
			if(this.context instanceof CompilationUnit && this.context.children.indexOf(ctx) != this.context.childCount - 1) {
				return this.visitChildren(ctx);
			} else {
				//Establish an environment for the file, so that the scope chain will include it even if it's empty initially
				this.symbolTable.record("global-environment", [], ctx);
				return this.withNewContext(ctx, () => this.visitChildren(ctx));
			}
		});
	};

	visitAssertion = (ctx: AssertionContext) => {
		return this.withNewContext(ctx, () => this.visitChildren(ctx));
	};

	visitNamespaceDeclaration = (ctx: NamespaceDeclarationContext) => {
		if(ctx.exception) {
			return this.symbolTable;
		}
		let localName = ctx.identifier() ? ctx.identifier().text : "";
		if(this.symbolTable.namespaces[localName]) {
			let message = (localName ? `Namespace '${localName}'` : "The default namespace") + " is defined more than once";
			this.symbolTable.errors.push({
				message: message,
				scope: ctx
			});
			let scope = this.symbolTable.namespaces[localName].definedAt;
			if(!this.symbolTable.errors.find(e => e.message == message && e.scope == scope)) {
				this.symbolTable.errors.push({ message: message, scope: scope });
			}
			return this.symbolTable;
		}
		this.symbolTable.namespaces[localName] = {
			namespace: this.lookupNamespace(ctx.URL().text),
			definedAt: ctx
		};
		return this.visitChildren(ctx);
	};

	visitAspectFilter = (ctx: AspectFilterContext) => {
		return this.withNewContext(ctx, () => this.visitChildren(ctx));
	};

	visitBlock = (ctx: BlockContext) => {
		return this.withNewContext(ctx, () => this.visitChildren(ctx));
	};

	visitConstantDeclaration = (ctx: ConstantDeclarationContext) => {
		//Constants are always global in scope
		let context = this.getGlobalContext();
		let name = ctx.identifier().text;
		if(context) {
			let info = new VariableInfo(true);
			info.definedAt = {
				line: ctx.start.line, column: ctx.start.charPositionInLine + 1
			};
			this.symbolTable.record(name, [info], context);
		} else {
			console.warn("Constant outside an assertion, ignoring: " + name);
		}
		return this.visitChildren(ctx);
	};

	visitAssignedVariable = (ctx: AssignedVariableContext) => {
		this.symbolTable.record(ctx.identifier().text, [new VariableInfo()], this.context);
		let assertion = this.context;
		while(assertion && !(assertion instanceof AssertionContext)) {
			assertion = assertion.parent;
		}
		if(assertion instanceof AssertionContext) {
			//Register the variable so that it's declared for every output attribute
			assertion.outputAttribute().forEach(a => {
				this.symbolTable.record(ctx.identifier().text, [new VariableInfo()], a);
			});
		}
		return this.symbolTable;
	};

	visitTag = (ctx: TagContext) => {
		//Tags are always global in scope
		let context = this.getGlobalContext();
		let tag = ctx.identifier().text;
		if(context) {
			this.symbolTable.record("$" + tag, [new VariableInfo()], context);
		} else {
			console.warn("Tag outside an assertion, ignoring: " + tag);
		}
		return this.visitChildren(ctx);
	};

	protected getGlobalContext(context: ParseTree = this.context) {
		while (context && !(context instanceof XuleFileContext || context instanceof CompilationUnit)) {
			context = context.parent;
		}
		return context;
	}

	visitForExpression = (ctx: ForExpressionContext) => {
		this.symbolTable.record(ctx.forHead().forVariable().identifier().text, [new VariableInfo()], this.context);
		return this.visitChildren(ctx);
	};

	visitFunctionDeclaration = (ctx: FunctionDeclarationContext) => {
		let functionInfo = new FunctionInfo();
		functionInfo.arity = ctx.functionArgument().length;
		//Functions are always global in scope
		let context = this.getGlobalContext();
		let name = ctx.identifier().text;
		if(context) {
			this.symbolTable.record(name, [functionInfo], context);
		} else {
			console.warn("Function outside an assertion, ignoring: " + name);
		}
		return this.withNewContext(ctx, () => this.visitChildren(ctx));
	};

	visitNavigation = (ctx: NavigationContext) => {
		this.symbolTable.record("$relationship", [new VariableInfo()], ctx);
		return this.visitChildren(ctx);
	};

	protected withNewContext<T>(ctx: ParseTree, fn: () => T): T {
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