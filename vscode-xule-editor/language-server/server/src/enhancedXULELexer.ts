import {XULELexer} from "./parser/XULELexer";
import {LexerNoViableAltException, Token} from "antlr4ts";

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
        let virtualWSToken = this.tokenFactory.create(
            { source: this, stream: this.inputStream }, XULELexer.WS, "", defaultChannel + 1000,
            this.lastToken.startIndex, this.lastToken.stopIndex, this.lastToken.line, this.lastToken.charPositionInLine);
        this.lastToken = virtualWSToken;
        return virtualWSToken;
    }

    protected nextRealToken() {
        try {
            return super.nextToken();
        } catch (e) {
            if (e.message == 'EmptyStackException') {
                let token = this.emit();
                if (token.text == '}') {
                    this.notifyListeners(new LexerNoViableAltException(this, this._input, this._tokenStartCharIndex, undefined));
                    return token;
                }
            }
            throw e;
        }
    }
}