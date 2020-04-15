import { ParseTree, AbstractParseTreeVisitor } from 'antlr4ts/tree';
import { XULEParserVisitor } from './parser/XULEParserVisitor';
import { ConstantDeclarationContext, AssignmentContext, FunctionDeclarationContext, FunctionArgumentContext } from './parser/XULEParser';

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

	findAll(what, test: (obj: any) => boolean = (obj) => obj.name == what): Binding[] {
		const bindings = this.bindings.filter(mapping => test(mapping));
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

	public symbols: { context: ParseTree, environment: Environment }[] = [];

	lookup(name, context: ParseTree) {
		const env = this.lookupEnvironment(context);
		if(env) {
			return env.find(name);
		}
	}

	lookupAll(name, context: ParseTree, test: (binding: Binding) => boolean = b => b.name == name) {
		const env = this.lookupEnvironment(context);
		if(env) {
			return env.findAll(name, test);
		} else {
			return [];
		}
	}

	record(name, meaning, context: ParseTree, combinator: (binding: Binding, meaning: any) => any = (binding, meaning) => {
		return ensureArray(binding.meaning).concat(ensureArray(meaning));
	}) {
		const info = this.symbols.find(s => s.context == context);
		if(info) {
			info.environment.bindings.push({ name: name, meaning: meaning });
		} else {
			const env = new Environment();
			env.parent = this.lookupEnvironment(context);
			const existing = env.bindings.find(b => b.name == name);
			if(existing) {
				existing.meaning = combinator(existing, meaning);
			} else {
				env.bindings.push({ name: name, meaning: meaning });
			}
			this.symbols.push({ context: context, environment: env });
		}
	}

	lookupEnvironment(context: ParseTree): Environment {
		const info = this.symbols.find(s => s.context == context);
		if(info) {
			return info.environment;
		} else if(context.parent) {
			return this.lookupEnvironment(context.parent);
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

	visit(tree: ParseTree): SymbolTable {
		this.symbolTable = new SymbolTable();
		this.context = tree;
		return super.visit(tree);
	}

	visitConstantDeclaration = (ctx: ConstantDeclarationContext) => {
		this.symbolTable.record(ctx.identifier().text, [DeclarationType.CONSTANT], this.context);
		return this.visitChildren(ctx);
	};

	visitAssignment = (ctx: AssignmentContext) => {
		this.symbolTable.record(ctx.identifier().text, [DeclarationType.VARIABLE], this.context);
		return this.visitChildren(ctx);
	};

	visitFunctionDeclaration = (ctx: FunctionDeclarationContext) => {
		let context = this.context;
		this.context = ctx;
		this.symbolTable.record(ctx.identifier().text, [DeclarationType.FUNCTION], context);
		try {
			return this.visitChildren(ctx);
		} finally {
			this.context = context;
		}
	};

	visitFunctionArgument = (ctx: FunctionArgumentContext) => {
		this.symbolTable.record(ctx.identifier().text, [DeclarationType.VARIABLE], this.context);
		return this.visitChildren(ctx);
	};
	
}