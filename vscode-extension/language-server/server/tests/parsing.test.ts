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
		expect(input.index).to.equal(input.size);
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
		expect(input.index).to.equal(input.size);
	});
});

describe('Concept', function() {
	it("has a balance property", function () {
		const xuleCode = `$results = list([covered @concept.balance = debit]);`;
		let input = CharStreams.fromString(xuleCode);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.assignment();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
	it("has a period-type property", function () {
		const xuleCode = `$results = list([covered @concept.period-type = instant]);`;
		let input = CharStreams.fromString(xuleCode);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.assignment();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
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
		expect(input.index).to.equal(input.size);
	});
	it("admits != *", function() {
		const xuleCode = `list({covered @RetirementPlanSponsorLocationAxis != * where $fact.dimensions().values.name.contains(country:US)})`;
		let input = CharStreams.fromString(xuleCode);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.expression();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
	it('supports @unit != unit(...)', function() {
		const factset = '{nonils @concept.data-type = num:perShareItemType @unit != unit(iso4217:USD, xbrli:shares)}';
		let input = CharStreams.fromString(factset);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.factset();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
	it("can be just {covered-dims}", function() {
		const factset = '{covered-dims}';
		let input = CharStreams.fromString(factset);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.factset();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
	it("admits covered with no filter", function() {
		const factset = 'count(list({covered where $fact.concept.name == Revenues}))';
		let input = CharStreams.fromString(factset);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.expression();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
});

describe('Navigation', function() {
	it("for descendants and ancestors, the number of levels to navigate can be specified after the direction",
		function() {
		const xuleCode = `navigate parent-child descendants 2`;
		let input = CharStreams.fromString(xuleCode);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.navigation();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
});

describe('Numbers', function() {
	it("may have a decimal part", function() {
		const xuleCode = `$expected = 92088098335.8388;`;
		let input = CharStreams.fromString(xuleCode);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.assignment();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
});