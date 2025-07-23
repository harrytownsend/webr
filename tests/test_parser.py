import pytest

from webr.html import HTMLParser, HTMLParserSegment, HTMLParserElementSegment, HTMLParserTextSegment, HTMLParserCommentSegment
from typing import Dict, Optional

from htmltools.builder import HTMLSegmentBuilder

values: Dict[str, str] = {
	"title": "Testing...",
	"script": "alert(\"<p>\")",
	"input.type": "text",
	"input.value": "testing...",
}

builder: HTMLSegmentBuilder = HTMLSegmentBuilder()

(
	builder
		.doctype("html", "doctype")
		.open("html", {}, "html")
			.open("head", {}, "head")
				.open("title", {}, "title")
					.text(values["title"], "title-text")
				.close("title", "/title")
				.open("script", {},"script")
					.text(values["script"], "script-text")
				.close("script", "/script")
			.close("head", "/head")
			.open("body", {},"body")
				.void("input", {
					"type": values["input.type"],
					"value": values["input.value"],
				}, "input")
			.close("body", "/body")
		.close("html", "/html")
)

@pytest.fixture
def html() -> str:
	return builder.html


class TestHTMLParser:

	def test_html(self, html) -> None:
		parser: HTMLParser = HTMLParser(html, strict = True)
		assert parser.html == html


	@pytest.mark.parametrize("strict", [
		True,
		False,
	])
	def test_strict(self, html, strict: bool) -> None:
		parser: HTMLParser = HTMLParser(html, strict)

		assert parser.strict == strict

	@pytest.mark.parametrize("segmentNo", [
		(builder.getIdByName("doctype")),
		(builder.getIdByName("input")),
	])
	def test_current(self,
		html: str,
		segmentNo: int
	):
		parser: HTMLParser = HTMLParser(html = html, strict = True)

		current: HTMLParserSegment
		for i in range(segmentNo + 1):
			current = parser.next()

		assert parser.current == current

	@pytest.mark.parametrize("segmentNo, className, name, open, close, attributes, text", [
		(builder.getIdByName("doctype"), HTMLParserElementSegment, "!doctype", True, False, { "html": "true" }, None),
		(builder.getIdByName("html"), HTMLParserElementSegment, "html", True, False, {}, None),
		(builder.getIdByName("/html"), HTMLParserElementSegment, "html", False, True, {}, None),
		(builder.getIdByName("head"), HTMLParserElementSegment, "head", True, False, {}, None),
		(builder.getIdByName("/head"), HTMLParserElementSegment, "head", False, True, {}, None),
		(builder.getIdByName("title-text"), HTMLParserTextSegment, None, False, False, None, values["title"]),
		(builder.getIdByName("script-text"), HTMLParserTextSegment, None, False, False, None, values["script"]),
		(builder.getIdByName("input"), HTMLParserElementSegment, "input", True, True, { "type": values["input.type"], "value": values["input.value"] }, None),
	])
	def test_next(self,
		html: str,
		segmentNo: int,
		className: type,
		name: Optional[str],
		open: Optional[bool],
		close: Optional[bool],
		attributes: Optional[Dict[str, str]],
		text: Optional[str]
	):
		parser: HTMLParser = HTMLParser(html = html, strict = True)

		segment: HTMLParserSegment
		for i in range(segmentNo + 1):
			segment = parser.next()

		assert isinstance(segment, className)
		
		if isinstance(segment, HTMLParserElementSegment):
			segment: HTMLParserElementSegment

			assert segment.name == name
			assert segment.open == open
			assert segment.close == close

			if open:
				# Check everything in the node is in the expected.
				for key, value in segment.attributes.items():
					assert key in attributes
					assert attributes[key] == value

				# Check everything in the expectd is in the node.
				for key, value in attributes.items():
					assert key in segment.attributes
					assert segment.attributes[key] == value

		elif isinstance(segment, HTMLParserTextSegment):
			segment: HTMLParserTextSegment

			assert segment.text == text

		elif isinstance(segment, HTMLParserCommentSegment):
			segment: HTMLParserCommentSegment

			assert segment.comment == text

	def test_iter_count(self, html: str):
		parser: HTMLParser = HTMLParser(html = html, strict = True)

		expected: int = builder.count

		actual: int = 0
		for segment in parser:
			actual += 1

		assert expected == actual
