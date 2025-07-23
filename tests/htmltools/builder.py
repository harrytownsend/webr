from typing import List, Dict, Optional

class HTMLSegmentBuilder:
	"""A utility class for building HTML documents for testing purposes.
	"""

	_segments: List[str]
	_index: Dict[str, int]

	_pretty: bool
	_indentText: str
	_indentLevel: int

	def __init__(self, pretty: bool = False, indent: str = "\t"):
		self._segments = []
		self._index = {}

		self._pretty = pretty
		self._indentText = indent
		self._indentLevel = 0
	
	@property
	def count(self) -> int:
		return len(self._segments)
	
	@property
	def html(self) -> str:
		return "".join(self._segments)
	
	@property
	def indentationLevel(self) -> int:
		return self._indentLevel
	
	def _add(self, segment: str, name: Optional[str] = None) -> None:
		"""Add a segment to the document.

		Args:
			segment (str): The text of the segment.
			name (Optional[str], optional): The name for the segment for use when looking it up.

		Raises:
			Exception: Name already in use.
		"""

		index: int = len(self._segments)

		formattedSegment: str = self._getPrefix() + segment

		self._segments.append(formattedSegment)

		if name:
			if name in self._index:
				raise Exception(f"A segment already exists with the name: {name}")

			self._index[name] = index
	
	def _indentModify(self, indentModifier: int) -> None:

		indentLevel = self._indentLevel + indentModifier
		if indentLevel < 0:
			raise Exception("There are more closing elements than opening ones, resulting in invalid HTML.")
		
		self._indentLevel = indentLevel
	
	def _getPrefix(self) -> str:

		prefix: str = ""

		if self._pretty:
			if self.count > 0:
				prefix += "\n"

			prefix += self._indentText * self._indentLevel

		return prefix
	
	def _open(self, tagName: str, attributes: Optional[Dict[str, str]] = None, selfClosing: bool = False, name: Optional[str] = None) -> "HTMLSegmentBuilder":
		"""Add an open tag (including self-closing) to the document.

		Args:
			tagName (str): The type of tag.
			attributes (Optional[Dict[str, str]], optional): The attributes of the element.
			selfClosing (bool, optional): Whether the tag is self-closing.
			name (Optional[str], optional): The name used to reference this segment of the HTML.

		Returns:
			HTMLSegmentBuilder: self
		"""

		# Build the HTML for the attributes.
		attributeText: str = ""
		if attributes and len(attributes) > 0:
			attributeText: str = " " + " ".join([f"{name}=\"{value}\"" for name, value in attributes.items()])

		# Build the HTML for the self-closing.
		selfClosingText: str = ""
		if selfClosing:
			selfClosingText = " /"

		segment: str = f"<{tagName}{attributeText}{selfClosingText}>"
		self._add(segment, name)

		return self

	def close(self, tagName: str, name: Optional[str] = None) -> "HTMLSegmentBuilder":
		"""Add a closing tag to the document.

		Args:
			tagName (str): The type of tag.
			name (Optional[str], optional): The name used to reference this segment of the HTML.

		Returns:
			HTMLSegmentBuilder: self
		"""

		self._indentModify(-1)
		segment: str = f"</{tagName}>"
		self._add(segment, name)

		return self
	
	def comment(self, comment: str, name: Optional[str] = None) -> "HTMLSegmentBuilder":
		"""Add a comment to the document.

		Args:
			comment (str): The text of the comment.
			name (Optional[str], optional): The name used to reference this segment of the HTML.

		Returns:
			HTMLSegmentBuilder: self
		"""

		segment: str = f"<!-- {comment} -->"
		self._add(segment, name)

		return self

	def doctype(self, type: str = "html", name: Optional[str] = None) -> "HTMLSegmentBuilder":
		"""Add a doctype to the beginning of the document.

		Args:
			type (str, optional): The type of document. Defaults to "html".
			name (Optional[str], optional): The name used to reference this segment of the HTML.

		Returns:
			HTMLSegmentBuilder: self
		"""

		segment: str = f"<!DOCTYPE {type}>"
		self._add(segment, name)

		return self
	
	def getIdByName(self, name: str) -> int:
		"""Get the index of the semgent by its name.

		Args:
			name (str): The name of the segment to look for.

		Returns:
			int: The index of the segment.
		"""

		return self._index[name]
	
	def getSegmentById(self, index: int) -> str:
		"""Get a segment's HTML text by its id.

		Args:
			index (int): The id of the segment assigned when it was added.

		Returns:
			str: The resulting HTML text of the segment.
		"""

		return self._segments[index]
	
	def getSegmentByName(self, name: str) -> str:
		"""Get a segment's HTML text by its name.

		Args:
			name (str): The name of the segment to return.

		Returns:
			str: The resulting HTML text of the segment.
		"""

		index: int = self.getSegmentByName(name)

		return self.getSegmentById(index)
	
	def open(self, tagName: str, attributes: Optional[Dict[str, str]] = None, name: Optional[str] = None) -> "HTMLSegmentBuilder":
		"""Add an open tag to the document.

		Args:
			tagName (str): The type of tag/
			attributes (Optional[Dict[str, str]], optional): A element's attributes.
			name (Optional[str], optional): The name used to reference this segment of the HTML.

		Returns:
			HTMLSegmentBuilder: self
		"""

		self._open(tagName, attributes, False, name)
		self._indentModify(1)

		return self

	
	def text(self, text:str, name: Optional[str] = None) -> "HTMLSegmentBuilder":
		"""Add a text node to the document.

		Args:
			text (str): The text to add to the document.
			name (Optional[str], optional): The name used to reference this segment of the HTML.

		Returns:
			HTMLSegmentBuilder: self
		"""

		self._add(text, name)

		return self
	
	def void(self, tagName: str, attributes: Optional[Dict[str, str]] = None, name: Optional[str] = None) -> "HTMLSegmentBuilder":
		"""Add an open tag to the document.

		Args:
			tagName (str): The type of tag/
			attributes (Optional[Dict[str, str]], optional): A element's attributes.
			name (Optional[str], optional): The name used to reference this segment of the HTML.

		Returns:
			HTMLSegmentBuilder: self
		"""

		self._open(tagName, attributes, True, name)

		return self