import {ParserRuleContext} from "antlr4ts";
import {ParseTree, TerminalNode} from "antlr4ts/tree";

export function getRange(parseTree: ParseTree) {
    let start, stop;
    if(parseTree instanceof ParserRuleContext) {
        start = parseTree.start;
        stop = parseTree.stop;
    } else if(parseTree instanceof TerminalNode) {
        start = stop = parseTree.symbol;
    }
    const lines = stop.text.match(LINES_REGEXP);
    let endCharacter
    if(lines.length == 1) {
        endCharacter = stop.charPositionInLine + lines[0].length;
    } else {
        endCharacter = lines[lines.length - 1].length;
    }
    return {
        start: { line: start.line - 1, character: start.charPositionInLine },
        end: {
            line: stop.line - 1 + lines.length - 1,
            character: endCharacter
        }
    };
}

export const LINES_REGEXP = /[^\n\r]*(\r\n|\n|\r)|[^\n\r]+$/g;