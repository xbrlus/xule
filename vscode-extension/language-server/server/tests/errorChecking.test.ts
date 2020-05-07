import {expect} from 'chai';
import 'mocha';
import {XULEParser} from "../src/parser/XULEParser";
import {CharStreams, CommonTokenStream} from "antlr4ts";
import {XULELexer} from "../src/parser/XULELexer";
import {SemanticCheckVisitor} from "../src/semanticCheckVisitor";
import {initialEnvironment, SymbolTable, SymbolTableVisitor} from "../src/symbols";

describe('Aspect filters', function() {
    it("can declare variables with `as <identifier>`",
        function() {
            const xuleCode = `$results = list({covered @Assets @ConsolidationItemsAxis = * as $myMember where $fact > 0 and $myMember == OperatingSegmentsMember});`;
            let input = CharStreams.fromString(xuleCode);
            let lexer = new XULELexer(input);
            let parser = new XULEParser(new CommonTokenStream(lexer));
            let parseTree = parser.assignment();
            expect(parser.numberOfSyntaxErrors).to.equal(0);
            expect(input.index).to.equal(input.size);
            let diagnostics = [];
            let symbolTable = new SymbolTableVisitor(new SymbolTable(initialEnvironment), parseTree).visit(parseTree);
            new SemanticCheckVisitor(diagnostics, symbolTable, null).visit(parseTree);
            expect(diagnostics.length).to.equal(0);
        });
});

describe('Functions', function () {
    it("may not have a name that begins with $: function call", function () {
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
    it("may not have a name that begins with $: function declaration", function () {
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

describe('Navigation', function() {
    it("introduces the $relationship variable",
        function() {
            const xuleCode = `count(navigate summation-item descendants include start from Assets stop when $relationship.weight == 1 returns (source-name, target-name, weight, navigation-depth)) `;
            let input = CharStreams.fromString(xuleCode);
            let lexer = new XULELexer(input);
            let parser = new XULEParser(new CommonTokenStream(lexer));
            let parseTree = parser.expression();
            expect(parser.numberOfSyntaxErrors).to.equal(0);
            expect(input.index).to.equal(input.size);
            let diagnostics = [];
            let symbolTable = new SymbolTableVisitor(new SymbolTable()).visit(parseTree);
            new SemanticCheckVisitor(diagnostics, symbolTable, null).visit(parseTree);
            expect(diagnostics.length).to.equal(0);
        });
});