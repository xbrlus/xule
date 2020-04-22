import {ParseTree, AbstractParseTreeVisitor, RuleNode} from 'antlr4ts/tree';
import { XULEParserVisitor } from './parser/XULEParserVisitor';
import { ConstantDeclarationContext, AssignmentContext, FunctionDeclarationContext, FunctionArgumentContext, ExpressionContext, PropertyAccessContext, XuleFileContext } from './parser/XULEParser';

export type Binding = { name: any, meaning: any };

export class Environment {

	public bindings: Binding[] = [];
	constructor(public parent?: Environment) {}

	find(what, test: (obj: any) => boolean = (obj) => obj.name == what): Binding {
		const binding = this.bindings.find(mapping => test(mapping));
		if(binding) {
			return binding;
		} else if(this.parent) {
			return this.parent.find(what, test);
		} else {
			return undefined;
		}
	}

	findAll(what, test: (obj, name) => boolean = (obj, name) => obj.name == name): Binding[] {
		const bindings = this.bindings.filter(mapping => test(mapping, what));
		if(this.parent) {
			return bindings.concat(this.parent.findAll(what, test));
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

export class SymbolTable {

	public symbols: { scope: ParseTree, environment: Environment }[] = [];

	lookup(name, scope: ParseTree) {
		const env = this.lookupEnvironment(scope);
		if(env) {
			return env.find(name);
		}
	}

	lookupAll(name, scope: ParseTree, test: (binding: Binding, name) => boolean = (b, n) => b.name == n) {
		const env = this.lookupEnvironment(scope);
		if(env) {
			return env.findAll(name, test);
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
			return undefined;
		}
	}

}

export enum DeclarationType {
	CONSTANT, FUNCTION, VARIABLE
}

export class SymbolTableVisitor extends AbstractParseTreeVisitor<SymbolTable> implements XULEParserVisitor<SymbolTable> {

	protected symbolTable: SymbolTable;
	protected context: ParseTree;

	protected defaultResult(): SymbolTable {
		return this.symbolTable;
	}

	visitXuleFile = (ctx: XuleFileContext) => {
		this.symbolTable = new SymbolTable();
		return this.visitChildrenInNewContext(ctx);
	};

	visitConstantDeclaration = (ctx: ConstantDeclarationContext) => {
		this.symbolTable.record(ctx.identifier().text, [DeclarationType.CONSTANT], this.context);
		return this.visitChildren(ctx);
	};

	visitAssignment = (ctx: AssignmentContext) => {
		this.symbolTable.record(ctx.identifier().text, [DeclarationType.VARIABLE], this.context);
		return this.visitChildrenInNewContext(ctx);
	};

	visitFunctionDeclaration = (ctx: FunctionDeclarationContext) => {
		this.symbolTable.record(ctx.identifier().text, [DeclarationType.FUNCTION], this.context);
		return this.visitChildrenInNewContext(ctx);
	};

	protected visitChildrenInNewContext(ctx: RuleNode) {
		let context = this.context;
		this.context = ctx;
		try {
			return this.visitChildren(ctx);
		} finally {
			this.context = context;
		}
	}

	visitFunctionArgument = (ctx: FunctionArgumentContext) => {
		this.symbolTable.record(ctx.identifier().text, [DeclarationType.VARIABLE], this.context);
		return this.visitChildren(ctx);
	};

	/*visitPropertyAccess = (ctx: PropertyAccessContext) => {
		let context = this.context;
		this.context = ctx;
		this.symbolTable.record(ctx.identifier().text, [DeclarationType.VARIABLE], this.context);
		try {
			return this.visitChildren(ctx);
		} finally {
			this.context = context;
		}
	};*/
	
}