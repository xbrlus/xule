import { HtmlElementContext } from "./antlr/HTMLParser";

export class XendrReport
{
	namespaces: Map<String, String>;
	blocks: XuleBlock[];
	footnotesPresent: boolean;

	constructor()
	{
		this.blocks = [];
		this.namespaces = new Map<String, String>();
		this.footnotesPresent = false;
	}

	addNamespace(name: String, target: String)
	{
		this.namespaces.set(name, target);
	}

	addBlock(block: XuleBlock): XuleBlock
	{
		this.blocks.push(block);
		return block;
	}

	getBlockWithName(name: String | undefined) : XuleBlock | undefined
	{
		return this.blocks.find(x => x.name === name);
	}

	getMostRecentBlock()
	{
		return this.blocks[this.blocks.length - 1];
	}

	setFootnotesPresent()
	{
		this.footnotesPresent = true;
	}

	isValid()
	{
		return [...this.namespaces.values()].includes("http://xbrl.us/xendr/2.0/template");
	}
}

export class XuleBlock
{
	name : string | undefined;
	elements : HtmlElementContext[];
	kind : BlockKind;

	constructor(kind: BlockKind, name: string | undefined = undefined)
	{
		this.kind = kind;
		this.name = name;
		this.elements = [];
	}

	addElement(element: HtmlElementContext)
	{
		if (!this.name && !this.elements.length)
		{
			this.name = `o${element.start.line}`;
		}
		this.elements.push(element);
	}
}

export enum BlockKind
{
	SingleExpression,
	SingleStatement,
	ExpressionList,
	Parts
}