// antlr4ng-cli 2.0.0 emits `this._input.LT(1)` in semantic-predicate code even when the
// grammar uses `this.tokenStream.LT(1)`. `_input` does not exist on the generated Parser
// subclass, so this patch runs after every generation to keep the output compilable.
'use strict';

const fs = require('fs');
const path = require('path');

const parserFile = path.join(__dirname, '..', 'src', 'parser', 'XULEParser.ts');
const before = fs.readFileSync(parserFile, 'utf8');

const content = before.split('this._input.LT(1)').join('this.tokenStream.LT(1)');

if (content !== before) {
	fs.writeFileSync(parserFile, content);
	console.log('patch-generated-parser: replaced this._input.LT(1) -> this.tokenStream.LT(1) in XULEParser.ts');
} else {
	console.log('patch-generated-parser: no matching pattern found, nothing to patch');
}
