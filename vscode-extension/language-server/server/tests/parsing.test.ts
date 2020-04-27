import { expect } from 'chai';
import 'mocha';
import {XULEParser} from "../src/parser/XULEParser";
import {CharStreams, CommonTokenStream} from "antlr4ts";
import {XULELexer} from "../src/parser/XULELexer";

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