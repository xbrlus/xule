import {XULELexer} from "./parser/XULELexer";
import {LexerNoViableAltException, Token} from "antlr4ts";

export class SafeXULELexer extends XULELexer {
    
    nextToken(): Token {
        try {
            return super.nextToken();
        } catch (e) {
            if(e.message == 'EmptyStackException') {
                let token = this.emit();
                if(token.text == '}') {
                    this.notifyListeners(new LexerNoViableAltException(this, this._input, this._tokenStartCharIndex, undefined));
                    return token;
                }
            }
            throw e;
        }
    }
}