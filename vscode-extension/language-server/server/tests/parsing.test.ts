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

describe('Variable assignment', function() {
	it("doesn't need to end with a semicolon", function() {
		const xuleCode = `
output ND8
$results = count(navigate dimensions descendants from StatementTable drs-role ConsolidatedBalanceSheet returns usable)

output ND9
count(taxonomy().dimensions)`;
		let input = CharStreams.fromString(xuleCode);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.xuleFile();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
	});
});

describe('Factset filtering', function() {
	it("admits = none", function() {
		const xuleCode = `list({covered @RetirementPlanSponsorLocationAxis = none where $fact.dimensions().values.name.contains(country:US)})`;
		let input = CharStreams.fromString(xuleCode);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.expression();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
	});
	it("admits != *", function() {
		const xuleCode = `list({covered @RetirementPlanSponsorLocationAxis != * where $fact.dimensions().values.name.contains(country:US)})`;
		let input = CharStreams.fromString(xuleCode);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.expression();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
	});
	it('supports @unit != unit(...)', function() {
		const factset = '{nonils @concept.data-type = num:perShareItemType @unit != unit(iso4217:USD, xbrli:shares)}';
		let input = CharStreams.fromString(factset);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.factset();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
	});
});