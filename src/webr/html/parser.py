from typing import Optional, Dict, List

class HTMLParser:

	_html: str
	_strict: bool

	_position: int
	_segmentCurrent: Optional["HTMLParserSegment"]
	_segmentNext: Optional["HTMLParserSegment"]

	_htmlLength: int

	_contextSwitchTags: List[str] = [
		"script",
		"style",
		"block"
	]

	def __init__(self, html: str, strict: bool = False):
		self._html = html
		self._strict = strict

		self._position = 0
		self._segmentCurrent = None
		self._segmentNext = None

		self._htmlLength = len(html)

	def __iter__(self) -> "HTMLParser":
		return self

	def __next__(self) -> "HTMLParserSegment":
		segment: HTMLParserSegment = self.next()
		if segment == None:
			raise StopIteration
		else:
			return segment

	@property
	def html(self) -> str:
		return self._html
	
	@property
	def strict(self) -> bool:
		return self._strict
	
	@property
	def current(self) -> Optional["HTMLParserSegment"]:
		return self._segmentCurrent
	
	def next(self) -> Optional["HTMLParserSegment"]:
		"""Get the next html segment from the html text.

		Returns:
			Optional[HTMLParserSegment]: The next segment or None if there are no more.
		"""

		segment: Optional[HTMLParserSegment]

		segmentCurrent: Optional[HTMLParserSegment] = self._segmentCurrent

		self._position = self._readWhitespace(self._position)
		if self._position == self._htmlLength:
			return None

		# Check for a cached segment.
		if (segment := self._segmentNext) is not None:
			self._segmentNext = None

		# Check if we're in a special context tag.
		elif segmentCurrent is not None and isinstance(segmentCurrent, HTMLParserElementSegment) and not segmentCurrent.close and segmentCurrent.name in self._contextSwitchTags:
			if (segment := self._readSpecialContextTagEnd(self._position, segmentCurrent.name)) is None and (segment := self._readSpecialContextText(self._position, segmentCurrent.name)) is None:
				return None

		# Check for an uncached segment.
		elif (segment := self._readComment(self._position)) is None and (segment := self._readTag(self._position)) is None and (segment := self._readText(self._position)) is None:
			if self._position == self._htmlLength:
				return None
			else:
				raise Exception("Could not read a node, text node or comment at position " + str(self._position) + " in the string.")

		# Update parser location and state.
		self._segmentCurrent = segment
		self._position = segment.end
		
		return segment





	"""
		Parsing Main Methods
	"""
	
	def _readTag(self, position: int) -> Optional["HTMLParserElementSegment"]:
		"""Attempt to read a valid HTML tag (open or close) at the specified location.

		Args:
			position (int): The position in the html text to start reading form.

		Returns:
			Optional[HTMLParserElementSegment]: The segment representing the html element if one was found, otherwise None.
		"""

		segment: HTMLParserElementSegment = HTMLParserElementSegment()
		segment.start = position

		result: Optional[int]

		# Check for opening angle bracket.
		if self._html[position] == "<":
			position += 1
		else:
			return None
		
		# Check if the tag is marked as a close tag.
		if self._html[position] == "/":
			position += 1
			segment.open = False
			segment.close = True
		else:
			segment.open = True
			segment.close = False
		
		# Check for spaces before the tag name.
		if not self._strict:
			position = self._readWhitespace(position)

		# Read the tag name.
		result = self._readTagName(position)
		if result is not None:
			segment.name = self._unwrap(self._html[position:result]).lower()
			position = result
		else:
			return None
		
		# Read all attributes.
		position = self._readWhitespace(position)
		while (result := self._readTagAttribute(position, segment.attributes)) is not None:
			position = self._readWhitespace(result)

		# Close tags should not have any attributes.
		if not segment.open and len(segment.attributes) > 0:
			return None
		
		# Check for a self-closing tag.
		if self._html[position] == "/":
			if self._strict and segment.close:
				return None
			else:
				segment.close = True
				position += 1

		# Check for a space between the end slash and the closing angle bracket.
		if not self._strict:
			position = self._readWhitespace(position)

		# Check for an angle bracket.
		if self._html[position] == ">":
			segment.end = position + 1
			segment.text = self._html[segment.start:segment.end]
		else:
			return None

		return segment

	def _readComment(self, position: int) -> Optional["HTMLParserCommentSegment"]:
		"""Attempt to read a comment tag at the specified location in the html text.

		Args:
			position (int): The position in the html text to start reading form.

		Returns:
			Optional[HTMLParserCommentSegment]: A segment representing the found comment, or None if one was not found.
		"""

		segment: HTMLParserCommentSegment = HTMLParserCommentSegment()
		segment.start = position

		# Check for the start of a comment.
		if self._html[position:position + 4] == "<!--":
			position += 4
		else:
			return None

		# check for the end of the comment.
		find: int = self._html.find("-->", position)
		if find >= 0:
			segment.end = find + 3
			segment.text = self._html[segment.start:segment.end]
			segment.comment = self._html[position:find].strip()
		else:
			return None
		
		return segment

	def _readText(self, position: int) -> Optional["HTMLParserTextSegment"]:
		"""Attempt to read regular text at the specified location in the html text.

		Args:
			position (int): The position in the html text to start looking from.

		Returns:
			Optional[HTMLParserSegmentText]: A segment representing the text that was found, or None if no text was found.
		"""

		segment: HTMLParserTextSegment = HTMLParserTextSegment()
		segment.start = position

		# Look for a text element or a comment to terminate the text node.
		while (position := self._html.find("<", position)) >= 0:
			segmentNext: Optional[HTMLParserSegment]

			# Check for a comment or a tag (in that order).
			if (segmentNext := self._readComment(position)) is not None or (segmentNext := self._readTag(position)) is not None:
				self._segmentNext = segmentNext

				segment.end = segmentNext.start
				segment.text = self._html[segment.start:segment.end].strip()
				return segment

			else:
				position += 1

		# This text node is the end of the file. This should not normally be possible.
		if not self._strict:
			segment.end = self._htmlLength
			segment.text = self._html[segment.start:segment.end].strip()
			return segment
		else:
			return None
		
	def _readSpecialContextTagEnd(self, position: int, contextTag: str) -> Optional["HTMLParserElementSegment"]:
		"""Attempt to read a closing tag of a specified type. This is intented for use in looking for the end of sections
			of the html text where the context changes, such as with a script or style tag.

		Args:
			position (int): The position in the html text to look for the closing tag.
			contextTag (str): The name of the closing tag to look for.

		Returns:
			Optional[HTMLParserElementSegment]: The segment representing the close tag, or None if one wasn't found.
		"""

		segment: Optional[HTMLParserElementSegment] = self._readTag(position)
		if segment is not None and not segment.open and segment.close and segment.name == contextTag:
			return segment
		else:
			return None

	def _readSpecialContextText(self, position: int, contextTag: str) -> Optional["HTMLParserTextSegment"]:
		"""Attempt to read all of the text contained within a special context tag, like script or style.

		Args:
			position (int): The location in the html text to look for the text.
			contextTag (str): The name of the context tag we're in.

		Returns:
			Optional[HTMLParserTextSegment]: The segment representing the text, or None if none was found.
		"""

		segment: HTMLParserTextSegment = HTMLParserTextSegment()
		segment.start = position

		# Look for a text element or a comment to terminate the text node.
		while (position := self._html.find("<", position)) >= 0:
			segmentNext: Optional[HTMLParserSegment]

			# Check for a comment or a tag (in that order).
			if (segmentNext := self._readSpecialContextTagEnd(position, contextTag)) is not None:
				self._segmentNext = segmentNext

				segment.end = segmentNext.start
				segment.text = self._html[segment.start:segment.end].strip()
				return segment
			else:
				position += 1

		# This text node is the end of the file. This should not normally be possible.
		if not self._strict:
			segment.end = self._htmlLength
			segment.text = self._html[segment.start:segment.end].strip()
			return segment
		else:
			return None


	"""
		Parsing Utility Methods
	"""

	def _readTagAttribute(self, position: int, attributes: Dict[str, str]) -> Optional[int]:
		"""Read an attribute from within an open tag at the specified location.

		Args:
			position (int): The position in the html text to look for the attribute.
			attributes (Dict[str, str]): The dictionary to add the found attribute/value to.

		Returns:
			Optional[int]: The end location of the attribute, or None if one wasn't found.
		"""

		start: int = position

		name: Optional[str] = None
		value: Optional[str] = None
		result: Optional[int] = None

		# Read a property name.
		position = self._readWhitespace(position)
		result = self._readTagAttributeProperty(position)
		if result is not None:
			name = self._unwrap(self._html[position:result]).strip().lower()
			position = result
		else:
			return None
		
		position = self._readWhitespace(position)
		if self._html[position] == "=":
			position += 1

			result = self._readTagAttributeValue(position)
			if result is not None:
				value = self._unwrap(self._html[position:result])
				position = result
			else:
				return None

		else:
			value = "true"

		if self._strict and name in attributes:
			return None
		
		attributes[name] = value

		return position

	def _readTagAttributeProperty(self, position: int) -> Optional[int]:
		"""Attempt to read the name of a property at the specified location in the html text.

		Args:
			position (int): The position in the html text to look for the attribute name.

		Returns:
			Optional[int]: The position of the end of the attribute name, or None if one was not found.
		"""

		start: int = position

		# HTML elements should not have a quoted attribute name.
		if self._strict and self._html[position] in ["\"", "'"]:
			return None
		
		# Deal with quoted attribute names and non-quoted attribute names separately.
		if self._html[position] in ["\"", "'"]:
			quote: str = self._html[position]
			position += 1

			matched: bool = False
			while position < self._htmlLength:
				char: str = self._html[position]

				if char == quote:
					matched = True
					position += 1
					break
				elif char == "\\":
					position += 2
				else:
					position += 1

			if matched:
				return position
			else:
				return None

		else:
			while position < self._htmlLength:
				char: str = self._html[position]

				if char.isspace() or char in ["=", "/", ">"]:
					break
				elif self._strict and not char.isalnum and char not in ["-", "_", "."]:
					return None
				
				position += 1

			if position > start:
				return position
			else:
				return None

	def _readTagAttributeValue(self, position: int) -> Optional[int]:
		"""Attempt to find the value of an attribute in the html text.

		Args:
			position (int): The position in the html text to look for the value.

		Returns:
			Optional[int]: The end position of the value, or None if one was not found.
		"""

		start: int = position

		if self._html[position] in ["\"", "'"]:
			quote: str = self._html[position]
			position += 1

			matched: bool = False
			while position < self._htmlLength:
				char: str = self._html[position]

				if char == quote:
					matched = True
					position += 1
					break
				elif char == "\\":
					position += 2
				else:
					position += 1

			if matched:
				return position
			else:
				return None

		elif not self._strict:
			while position < self._htmlLength:
				char: str = self._html[position]

				if char.isspace() or char in ["/", ">"]:
					break

				position += 1

			return position

		else:
			return None

	def _readTagName(self, position: int) -> Optional[int]:
		"""Attempt to read the name of a tag at the specified position in the html text.

		Args:
			position (int): The position in the html text to look for the tag name.

		Returns:
			Optional[int]: The position of the end of the tag name, or None if one was not found.
		"""

		start: int = position

		# Check for the exceptional case of the doctype tag.
		result: Optional[int] = self._readTagNameDoctype(position)
		if result is not None:
			return result

		while position < self._htmlLength:
			char: str = self._html[position]

			if char.isspace() or char in ["/", ">"]:
				break

			elif self._strict:
				if position == start:
					if not char.isalpha() and char not in ["_"]:
						return None
				else:
					if not char.isalnum() and char not in ["-", "_", "."]:
						return None

			position += 1

		if position > start:
			return position
		else:
			return None

	def _readTagNameDoctype(self, position: int) -> Optional[int]:
		"""Attempt to read a doctype tag name at the specified position in the html text.

		Args:
			position (int): The position in the html string to look for the doctype tag name.

		Returns:
			Optional[int]: The position of the end of the doctype tag name, or None if one was not found.
		"""

		doctype: str = "!DOCTYPE"
		end: int = position + len(doctype)

		if end < self._htmlLength and (self._html[position:end] == doctype or (not self._strict and self._html[position:end].upper() == doctype)):
			char: str = self._html[end]
			if char.isspace() or char in ["/", ">"]:
				return end
			else:
				return None

		else:
			return None

	def _readWhitespace(self, position: int) -> int:
		"""Read all whitespace in the document at the specified location.

		Args:
			position (int): The position in the html text to look for the whitespace.

		Returns:
			int: The position of the first non-whitespace character.
		"""

		while position < self._htmlLength and self._html[position].isspace():
			position += 1

		return position
	
	def _unwrap(self, text: str) -> str:
		"""Remove any quotes around the value.

		Args:
			text (str): The text to remove the quotes from.

		Returns:
			str: The string sans quotes.
		"""

		if text.startswith("\"") or text.startswith("'"):
			return text[1:len(text)-1]
		else:
			return text
	
class HTMLParserSegment:

	text: str
	start: int
	end: int

	def __init__(self, text: str = "", start: int = 0, end: int = 0):
		self.text = text
		self.start = start
		self.end = end

class HTMLParserElementSegment(HTMLParserSegment):

	name: str
	attributes: Dict[str, str]
	open: bool
	close: bool

	def __init__(self, text: str = "", start: int = 0, end: int = 0, name: str = "", open: bool = False, close: bool = False, attributes: Optional[Dict[str, str]] = None):
		super().__init__(text, start, end)
		self.name = name
		self.open = open
		self.close = close

		if isinstance(attributes, dict):
			self.attributes = attributes
		else:
			self.attributes = {}

class HTMLParserTextSegment(HTMLParserSegment):
	pass

class HTMLParserCommentSegment(HTMLParserSegment):
	
	comment: str

	def __init__(self, text: str = "", start: int = 0, end: int = 0, comment: str = ""):
		super().__init__(text, start, end)
		self.comment = comment