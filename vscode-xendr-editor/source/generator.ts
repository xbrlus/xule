import { BlockKind, XendrReport } from "./report";

export function generateXuleCode(report: XendrReport): string
{
	let xuleLines: string[] = [];

	xuleLines[0] = headerLine(report);

	for (let block of report.blocks)
	{
		let {kind, elements} = block;
		let listsOpened = 0;

		for (let element of elements)
		{
			let startLine = element.start.line - 1;
			let startColumn = element._content.start.charPositionInLine;
			let contentLines = element._content.text.split("\n").map(decode);

			switch(kind)
			{
				case BlockKind.SingleExpression:
				{
					if (element === elements[0])
					{
						let prelude = `output ${block.name}`;
						xuleLines[startLine] = `${prelude}${" ".repeat(startColumn - prelude.length)}${contentLines[0]}`;
					}
					else
					{
						xuleLines[startLine] = `${" ".repeat(startColumn)}${contentLines[0]}`;
					}
					for (let i = 1; i < contentLines.length; i++)
					{
						xuleLines[startLine + i] = contentLines[i];
					}
				}
				break; case BlockKind.SingleStatement:
				{
					xuleLines[startLine] = `${" ".repeat(startColumn)}${contentLines[0]}`;
					for (let i = 1; i < contentLines.length; i++)
					{
						xuleLines[startLine + i] = contentLines[i];
					}
				}
				break; case BlockKind.ExpressionList:
				{
					if (element === elements[0])
					{
						let prelude = `output ${block.name} list(`;
						xuleLines[startLine] = `${prelude}${" ".repeat(startColumn - prelude.length)}${contentLines[0]}`;
					}
					else
					{
						xuleLines[startLine] = `${" ".repeat(startColumn)}${contentLines[0]}`;
					}
					for (let i = 1; i < contentLines.length; i++)
					{
						xuleLines[startLine + i] = contentLines[i];
					}
					if (element === elements[elements.length - 1])
					{
						xuleLines[xuleLines.length - 1] += ")";
					}
					else
					{
						xuleLines[xuleLines.length - 1] += ",";
					}
				}
				break; case BlockKind.Parts:
				{
					if (element === elements[0])
					{
						let prelude = `output ${block.name}`;
						xuleLines[startLine] = `${prelude}${" ".repeat(startColumn - prelude.length)}${contentLines[0]}`;
					}
					else
					{
						xuleLines[startLine] = `${" ".repeat(startColumn)}${contentLines[0]}`;
					}
					for (let i = 1; i < contentLines.length; i++)
					{
						xuleLines[startLine + i] = contentLines[i];
					}
					if (element._name.text?.endsWith("expression") && !element._attributes.some(x => x._name.text === "part"))
					{
						xuleLines[xuleLines.length - 1] += " list(";
						listsOpened++;
					}
					else if (element === elements[elements.length - 1])
					{
						xuleLines[xuleLines.length - 1] += ")".repeat(listsOpened);
					}
					else
					{
						xuleLines[xuleLines.length - 1] += ",";
					}
				}
			}
		}
	}

	let xuleCode = xuleLines.join("\n");

	return xuleCode;
}

function headerLine(report: XendrReport): string
{
	let line = "";
	for (let [name, url] of report.namespaces.entries())
	{
		line += name ? ` namespace ${name} = ${url}` : ` namespace ${url}`;
	}
	if (report.footnotesPresent)
	{
		line += ` constant $footnoteFacts = list()`;
	}
	return line;
}

function decode(html: string): string
{
	return html.replace(/&lt;/g, "  < ");
}