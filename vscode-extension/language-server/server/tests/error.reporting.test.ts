import { expect } from 'chai';
import 'mocha';
import {XULEParser} from "../src/parser/XULEParser";
import {CharStreams, CommonTokenStream} from "antlr4ts";
import {XULELexer} from "../src/parser/XULELexer";

describe('Assert rule names', function() {
	it('can contain numbers and dots', function() {
		const assertion = 'assert F6.110.1 satisfied true';
		let input = CharStreams.fromString(assertion);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.assertion();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
	});
});

describe('Factset', function() {
	it('supports @unit != unit(...)', function() {
		const factset = '{nonils @concept.data-type = num:perShareItemType @unit != unit(iso4217:USD, xbrli:shares)}';
		let input = CharStreams.fromString(factset);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.factset();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
	});
});