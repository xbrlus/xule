import {XULELexer} from "./parser/XULELexer";
import {CommonToken, LexerNoViableAltException, Token} from "antlr4ng";

export class EnhancedXULELexer extends XULELexer {

    protected lastToken: Token;
    protected actualNextToken: Token;

    nextToken(): Token {
        if(this.actualNextToken) {
            this.lastToken = this.actualNextToken;
            this.actualNextToken = null;
            return this.lastToken;
        }
        let next = this.nextRealToken();
        let defaultChannel = XULELexer.DEFAULT_TOKEN_CHANNEL;
        if(!this.lastToken || this.lastToken.channel != defaultChannel || next.channel != defaultChannel || next.type == XULELexer.EOF) {
            this.lastToken = next;
            return next;
        }
        //Insert virtual whitespace token for better autocompletion
        this.actualNextToken = next;
        const virtualWSToken = CommonToken.fromSource(
            [this, this.inputStream], XULELexer.WS, defaultChannel + 1000,
            this.lastToken.start, this.lastToken.stop);
        virtualWSToken.line = this.lastToken.line;
        virtualWSToken.column = this.lastToken.column;
        this.lastToken = virtualWSToken;
        return virtualWSToken;
    }

    protected nextRealToken() {
        try {
            return super.nextToken();
        } catch (e) {
            if (e.message === 'Empty Stack') {
                let token = this.emit();
                if (token.text == '}') {
                    this.notifyListeners(new LexerNoViableAltException(this, this.inputStream, this.tokenStartCharIndex, undefined));
                    return token;
                }
            }
            throw e;
        }
    }
}