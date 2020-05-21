import {expect} from 'chai';
import 'mocha';
import {XULEParser} from "../src/parser/XULEParser";
import {CharStreams, CommonTokenStream} from "antlr4ts";
import {XULELexer} from "../src/parser/XULELexer";
import {SemanticCheckVisitor} from "../src/semanticCheckVisitor";
import {Namespace, SymbolTable, SymbolTableVisitor} from "../src/symbols";

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
            let symbolTable = new SymbolTableVisitor().withInitialContext(parseTree).visit(parseTree);
            let visitor = new SemanticCheckVisitor(diagnostics, symbolTable, null);
            visitor.checkQNames = false;
            visitor.visit(parseTree);
            expect(diagnostics.length).to.equal(0);
        });
});
describe('Factsets', function() {
    it("invalid forms are detected",
        function() {
            const xuleCode = `$sum1 = {ConstructionWorkInProgress};`;
            let input = CharStreams.fromString(xuleCode);
            let lexer = new XULELexer(input);
            let parser = new XULEParser(new CommonTokenStream(lexer));
            let parseTree = parser.assignment();
            expect(parser.numberOfSyntaxErrors).to.equal(0);
            expect(input.index).to.equal(input.size);
            let diagnostics = [];
            let symbolTable = new SymbolTableVisitor().withInitialContext(parseTree).visit(parseTree);
            let visitor = new SemanticCheckVisitor(diagnostics, symbolTable, null);
            visitor.visit(parseTree);
            expect(diagnostics.length).to.equal(2); //Malformed factset + invalid qname
        });
    it("Qnames are validated in valid forms (1)",
        function() {
            const xuleCode = `$sum1 = {@ConstructionWorkInProgress};`;
            let input = CharStreams.fromString(xuleCode);
            let lexer = new XULELexer(input);
            let parser = new XULEParser(new CommonTokenStream(lexer));
            let parseTree = parser.assignment();
            expect(parser.numberOfSyntaxErrors).to.equal(0);
            expect(input.index).to.equal(input.size);
            let diagnostics = [];
            let symbolTable = new SymbolTableVisitor().withInitialContext(parseTree).visit(parseTree);
            let visitor = new SemanticCheckVisitor(diagnostics, symbolTable, null);
            visitor.visit(parseTree);
            expect(diagnostics.length).to.equal(1);
        });
    it("Qnames are validated in valid forms (2)",
        function() {
            const xuleCode = `$sum1 = {@concept = ConstructionWorkInProgress};`;
            let input = CharStreams.fromString(xuleCode);
            let lexer = new XULELexer(input);
            let parser = new XULEParser(new CommonTokenStream(lexer));
            let parseTree = parser.assignment();
            expect(parser.numberOfSyntaxErrors).to.equal(0);
            expect(input.index).to.equal(input.size);
            let diagnostics = [];
            let symbolTable = new SymbolTableVisitor().withInitialContext(parseTree).visit(parseTree);
            let visitor = new SemanticCheckVisitor(diagnostics, symbolTable, null);
            visitor.visit(parseTree);
            expect(diagnostics.length).to.equal(1);
        });
    it("Qnames are validated in invalid forms",
        function() {
            const xuleCode = `$sum1 = {@conct = ConstructionWorkInProgress};`;
            let input = CharStreams.fromString(xuleCode);
            let lexer = new XULELexer(input);
            let parser = new XULEParser(new CommonTokenStream(lexer));
            let parseTree = parser.assignment();
            expect(parser.numberOfSyntaxErrors).to.equal(0);
            expect(input.index).to.equal(input.size);
            let diagnostics = [];
            let symbolTable = new SymbolTableVisitor().withInitialContext(parseTree).visit(parseTree);
            let visitor = new SemanticCheckVisitor(diagnostics, symbolTable, null);
            visitor.visit(parseTree);
            expect(diagnostics.length).to.equal(2);
        });
});

describe('Assertions', function() {
    it("must contain at least an expression",
        function() {
            const xuleCode = `assert F126 unsatisfied $sum1 = 1 message "{$sum1}"`;
            let input = CharStreams.fromString(xuleCode);
            let lexer = new XULELexer(input);
            let parser = new XULEParser(new CommonTokenStream(lexer));
            let parseTree = parser.assertion();
            expect(parser.numberOfSyntaxErrors).to.equal(0);
            expect(input.index).to.equal(input.size);
            let diagnostics = [];
            let symbolTable = new SymbolTableVisitor().withInitialContext(parseTree).visit(parseTree);
            new SemanticCheckVisitor(diagnostics, symbolTable, null).visit(parseTree);
            expect(diagnostics.length).to.equal(1);
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
            let symbolTable = new SymbolTableVisitor().withSymbolTable(new SymbolTable()).visit(parseTree);
            let visitor = new SemanticCheckVisitor(diagnostics, symbolTable, null);
            visitor.checkQNames = false;
            visitor.visit(parseTree);
            expect(diagnostics.length).to.equal(0);
        });
});

describe('Qnames', function() {
    it("are checked in filters: @concept = qname",
        function() {
            const xuleCode = `{@concept = Assets}`;
            let input = CharStreams.fromString(xuleCode);
            let lexer = new XULELexer(input);
            let parser = new XULEParser(new CommonTokenStream(lexer));
            let parseTree = parser.factset();
            expect(parser.numberOfSyntaxErrors).to.equal(0);
            expect(input.index).to.equal(input.size);

            let diagnostics = [];
            let namespace = new Namespace("", [{ localName: 'Assets' }]);
            let symbolTable = new SymbolTableVisitor().visit(parseTree);
            symbolTable.namespaces[""] = namespace;
            new SemanticCheckVisitor(diagnostics, symbolTable, null).visit(parseTree);
            expect(diagnostics.length).to.equal(0);

            symbolTable.namespaces = {};
            diagnostics = [];
            symbolTable = new SymbolTableVisitor().visit(parseTree);
            new SemanticCheckVisitor(diagnostics, symbolTable, null).visit(parseTree);
            expect(diagnostics.length).to.equal(1);
        });
    it("are checked in filters: @qname",
        function() {
            const xuleCode = `{@Assets}`;
            let input = CharStreams.fromString(xuleCode);
            let lexer = new XULELexer(input);
            let parser = new XULEParser(new CommonTokenStream(lexer));
            let parseTree = parser.factset();
            expect(parser.numberOfSyntaxErrors).to.equal(0);
            expect(input.index).to.equal(input.size);

            let diagnostics = [];
            let namespace = new Namespace("", [{ localName: 'Assets' }]);
            let symbolTable = new SymbolTableVisitor().visit(parseTree);
            symbolTable.namespaces[""] = namespace;
            new SemanticCheckVisitor(diagnostics, symbolTable, null).visit(parseTree);
            expect(diagnostics.length).to.equal(0);

            symbolTable.namespaces = {};
            diagnostics = [];
            symbolTable = new SymbolTableVisitor().visit(parseTree);
            new SemanticCheckVisitor(diagnostics, symbolTable, null).visit(parseTree);
            expect(diagnostics.length).to.equal(1);
        });
    it("are checked in filters: axis",
        function() {
            const xuleCode = `{@concept = Assets @BalanceSheetLocationAxis=ABCMember}`;
            let input = CharStreams.fromString(xuleCode);
            let lexer = new XULELexer(input);
            let parser = new XULEParser(new CommonTokenStream(lexer));
            let parseTree = parser.factset();
            expect(parser.numberOfSyntaxErrors).to.equal(0);
            expect(input.index).to.equal(input.size);

            let diagnostics = [];
            let namespace = new Namespace("", [{ localName: 'Assets' }, { localName: 'ABCMember' }]);
            let symbolTable = new SymbolTableVisitor().visit(parseTree);
            symbolTable.namespaces[""] = namespace;
            new SemanticCheckVisitor(diagnostics, symbolTable, null).visit(parseTree);
            expect(diagnostics.length).to.equal(1);
        });
});