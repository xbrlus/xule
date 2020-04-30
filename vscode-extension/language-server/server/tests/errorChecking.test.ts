import { expect } from 'chai';
import 'mocha';
import {XULEParser} from "../src/parser/XULEParser";
import {CharStreams, CommonTokenStream} from "antlr4ts";
import {XULELexer} from "../src/parser/XULELexer";
import {SemanticCheckVisitor} from "../src/semanticCheckVisitor";

describe('Functions', function() {
	it("may not have a name that begins with $: function call", function() {
		const xuleCode = `$foo()`;
		let input = CharStreams.fromString(xuleCode);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.expression();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
		let diagnostics = [];
		new SemanticCheckVisitor(diagnostics, null, null).visit(parseTree);
		expect(diagnostics.length).to.equal(1);
	});
	it("may not have a name that begins with $: function declaration", function() {
		const xuleCode = `function $foo() 42`;
		let input = CharStreams.fromString(xuleCode);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.functionDeclaration();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
		let diagnostics = [];
		new SemanticCheckVisitor(diagnostics, null, null).visit(parseTree);
		expect(diagnostics.length).to.equal(1);
	});
});