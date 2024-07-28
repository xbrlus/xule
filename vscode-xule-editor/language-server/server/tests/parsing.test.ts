import { expect } from 'chai';
import 'mocha';
import {XULEParser} from "../src/parser/XULEParser";
import {CharStreams, CommonTokenStream} from "antlr4ts";
import {XULELexer} from "../src/parser/XULELexer";

describe('Assertions', function() {
	it('can have a name containing numbers and dots', function() {
		const assertion = 'assert F6.110.1 satisfied true';
		let input = CharStreams.fromString(assertion);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.assertion();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
	it("must contain at least an expression",
		function() {
			const xuleCode = `assert F126 unsatisfied $sum1 = 1 message "{$sum1}"`;
			let input = CharStreams.fromString(xuleCode);
			let lexer = new XULELexer(input);
			let parser = new XULEParser(new CommonTokenStream(lexer));
			let parseTree = parser.assertion();
			expect(parser.numberOfSyntaxErrors).to.equal(0);
			expect(input.index).to.not.equal(input.size);
		});
});

describe('Assignments', function() {
	it("don't need to end with a semicolon", function() {
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
	it("supports division", function() {
		const factset = `
{@Unit=* @RetirementPlanSponsorLocationAxis=*
 {@DefinedBenefitPlanFairValueOfPlanAssets @RetirementPlanSponsorLocationAxis = country:US} /
 {@DefinedBenefitPlanBenefitObligation @RetirementPlanSponsorLocationAxis = country:US}}`;
		let input = CharStreams.fromString(factset);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.expression();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
	it("admits nested factsets (1)", function() {
		const factset = `list({covered @Axis2=* {list({@assets},{@liabilities},{@stock})}})`;
		let input = CharStreams.fromString(factset);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.expression();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
	it("admits nested factsets (2)", function() {
		const factset = `
	{@PercentageOfLIFOInventory @Unit=* @RetirementPlanSponsorLocationAxis} !=
	{@Unit=* @RetirementPlanSponsorLocationAxis={@DefinedBenefitPlanFairValueOfPlanAssets @RetirementPlanSponsorLocationAxis = country:US} /
											    {@DefinedBenefitPlanBenefitObligation @RetirementPlanSponsorLocationAxis = country:US}}`;
		let input = CharStreams.fromString(factset);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.expression();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
	it("supports @unit by itself, as a shortcut for @unit=*", function() {
		const factset = `{@concept=textItem @Unit @period=*}`;
		let input = CharStreams.fromString(factset);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.expression();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
	it("admits the nildefault keyword", function() {
		const factset = `{ nildefault @Assets} != {nildefault @LiabilitiesAndStockholdersEquity}`;
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
	it("admits include start",
	function() {
		const xuleCode = `navigate parent-child descendants 2 include start`;
		let input = CharStreams.fromString(xuleCode);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.navigation();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
	it("roles can include list access",
	function() {
		const xuleCode = `navigate summation-item descendants from $balance_sheet_items role $balance_sheet_roles[1] returns set (source)`;
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

describe('Outputs', function() {
	it('can contain numbers and dots', function() {
		const assertion = 'output F.2.1 true';
		let input = CharStreams.fromString(assertion);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.output();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
});

describe('Properties', function() {
	it("may be chained and have parameters", function() {
		const xuleCode = `rule-name().split('.').length`;
		let input = CharStreams.fromString(xuleCode);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.expression();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
});

describe('Rule name prefixes', function() {
	it('can contain numbers and dots', function () {
		const statement = 'rule-name-prefix xbrlus-cc.bc.dim_equivalents assert r14251 satisfied true';
		let input = CharStreams.fromString(statement);
		let lexer = new XULELexer(input);
		let parser = new XULEParser(new CommonTokenStream(lexer));
		let parseTree = parser.xuleFile();
		expect(parser.numberOfSyntaxErrors).to.equal(0);
		expect(input.index).to.equal(input.size);
	});
});