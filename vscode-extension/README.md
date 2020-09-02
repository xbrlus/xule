# XULE Language Support

This extension adds support to the XULE language to Visual Studio Code.

## Features

 * Syntax Highlighting
 * Code Completion (IntelliSense)

## Requirements

All dependencies are available from npm and the build process installs them automatically.

## Extension Settings

There are no settings so far.

## Known Issues

None so far.

## Release Notes

See the [Changelog](CHANGELOG.md).

## Building and Testing

To compile the extension use: `npm run compile`. This will also rebuild the lexer and the parser from the grammar.
To package it: `vsce package`.
To run the tests: `npm run test`.

## Development and Debugging

If we open the extension directory with VSCode, we can:

 * Build and watch for modifications: on OSX, Cmd+Shift+B
 * Launch a new VSCode window with the development extension installed: "Run" panel (Cmd+Shift+D on OSX) and launch the configuration "Client + Server". With this, VSCode should attach the debugger and stop at breakpoints.
 
### Notable extension points

 * Built-in taxonomies are defined in builtInNamespaces.ts.
 * Built-in variables, constants, and some keywords are defined as wellKnownVariables in symbols.ts.
 * Built-in functions and properties and other identifiers/keywords are defined at the bottom of semanticCheckVisitor.ts.
   * These are used by the semantic checker.
 * Syntax highlighting is defined in syntaxes/xule.tmLanguage.json. It includes both keywords and known identifiers (functions, constants, variables).