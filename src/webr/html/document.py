from typing import Callable, Optional, Dict, List
from .parser import HTMLParser, HTMLParserSegment, HTMLParserElementSegment, HTMLParserTextSegment, HTMLParserCommentSegment

class HTMLDocument:
	
	_text: str
	_strict: bool
	_comments: bool

	_rootList: List["HTMLNode"]
	_doctype: Optional["HTMLElementNode"]
	_html: Optional["HTMLElementNode"]
	_head: Optional["HTMLElementNode"]
	_body: Optional["HTMLElementNode"]

	_voidTags: List[str] = [
		"!doctype",
		"area",
		"base",
		"br",
		"col",
		"embed",
		"hr",
		"img",
		"input",
		"link",
		"meta",
		"source",
		"track",
		"wbr",
	]

	_neverSelfClosing: List[str] = [
		"script",
		"style",
		"html",
		"head",
		"body"
	]
	

	def __init__(self, html: str, strict: bool = False, comments: bool = False):
		self._text = html
		self._strict = strict
		self._comments = comments

		self._rootList = []
		self._doctype = None
		self._html = None
		self._head = None
		self._body = None

		if not self._load(html):
			raise Exception("An error occurred while attempting to read the html document.")

	@property
	def text(self) -> str:
		return self._text
	
	@property
	def strict(self) -> bool:
		return self._strict
	
	@property
	def comments(self) -> bool:
		return self._comments
	
	@property
	def rootList(self) -> List["HTMLElementNode"]:
		return self._rootList

	@property
	def doctype(self) -> Optional["HTMLElementNode"]:
		return self._doctype
	
	@property
	def html(self) -> Optional["HTMLElementNode"]:
		return self._html
	
	@property
	def head(self) -> Optional["HTMLElementNode"]:
		return self._head
	
	@property
	def body(self) -> Optional["HTMLElementNode"]:
		return self._body
	
	def _load(self, html: str) -> bool:
		"""Loads the document tree from the html text.

		Args:
			html (str): The html text of the document.

		Returns:
			bool: True if the document was loaded correctly. Otherwise, False.
		"""

		segment: HTMLParserSegment
		node: HTMLElementNode
		response: Optional[HTMLParserSegment]

		parser: HTMLParser = HTMLParser(html, self._strict)

		# Iterate through segments at the root level of the document.
		while (segment := parser.next()) is not None:
			if isinstance(segment, HTMLParserElementSegment):
				if segment.open:
					node = self._createNode(segment)
					self._rootList.append(node)

					# If the tag is not self closing, we need to apply any children.
					if not segment.close and segment.name not in self._voidTags:
						response = self._loadChildren(node, parser)

						# If we got a response here, we have a close tag with no match anywhere in the tree.
						if response is not None and self._strict:
							raise Exception("A close tag was found that has no matching open at position: " + str(segment.start))

				elif self._strict:
					raise Exception("A closing tag was found at the root level of the document at position: " + str(segment.start))

			# Comment and text nodes don't have any special behaviour.
			elif isinstance(segment, HTMLParserTextSegment):
				self._rootList.append(self._createNode(segment))
			elif isinstance(segment, HTMLParserCommentSegment) and self._comments:
				self._rootList.append(self._createNode(segment))
			else:
				raise Exception("Unknown node type.")
				
		self._linkNodes()

		return True
				
	def _loadChildren(self, parent: "HTMLElementNode", parser: "HTMLParser") -> Optional["HTMLParserSegment"]:
		"""Recursively deals with building out the node tree for the root based on the parsed HTML segments.

		Returns:
			Optional[HTMLParserSegment]: If a close segment was not consumed, return it so a match can be found at a higher level.
		"""

		segment: Optional[HTMLParser]
		node: Optional[HTMLElementNode]
		response: Optional[HTMLParserSegment]

		while (segment := parser.next()) is not None:
			if isinstance(segment, HTMLParserElementSegment):

				if segment.open:
					node = self._createNode(segment, parent)
					parent.children.append(node)

					# If the tag is not self closing, we need to apply any children.
					if not segment.close and segment.name not in self._voidTags:
						response = self._loadChildren(node, parser)

						# If we get a response back, it means we got a close tag that wasn't resolved one or more descendent levels down.
						if response is not None:
							# Check if the segment's tag name matches this parent's.
							if segment.name == parent.name:
								# It matched. The parent is now closed and we can go up a level cleanly.
								return None
							else:
								# It did not match. We need to kick the problem up the tree.
								return segment


				elif segment.close:
					# Check if the segment's tag name matches this parent's.
					if segment.name == parent.name:
						# It matched. The parent is now closed and we can go up a level cleanly.
						return None
					else:
						# It did not match. We need to kick the problem up the tree.
						return segment

				else:
					# An element node should always be either or both of an open and a close.
					if self._strict:
						raise Exception("An unidentified tag was found at position: " + str(segment.start))

			elif isinstance(segment, HTMLParserTextSegment):
				parent.children.append(self._createNode(segment, parent))
			elif isinstance(segment, HTMLParserCommentSegment):
				if self._comments:
					parent.children.append(self._createNode(segment, parent))
			else:
				raise Exception("Unknown node type.")

		# If we got here, we prematurely ran out of html.
		if self._strict:
			raise Exception("HTML ended before all tags were closed.")
		else:
			return None
		
	def _linkNodes(self) -> None:
		"""Link various key elements (like html, head, and body) to the shortcut accessors.
		"""

		# Link the top level nodes.
		for index, node in enumerate(self._rootList):
			if isinstance(node, HTMLElementNode):
				if node.name == "!doctype":
					if index == 0 or not self._strict:
						self._doctype = node

				elif node.name == "html":
					if index in [0, 1] or not self._strict:
						self._html = node

		# If we found a html node, link the head and body nodes.
		if self.html is not None:
			for index, node in enumerate(self.html.children):
				if isinstance(node, HTMLElementNode):
					if node.name == "head":
						if index == 0 or not self._strict:
							self._head = node

					elif node.name == "body":
						if index in [0, 1] or not self._strict:
							self._body = node

	def _createNode(self, segment: "HTMLParserSegment", parent: Optional["HTMLElementNode"] = None) -> Optional["HTMLNode"]:
		"""Create a node based on the provided html segment.

		Returns:
			Optional[HTMLNode]: The node created from the segment, if one could be created.
		"""

		node: Optional[HTMLNode]

		if isinstance(segment, HTMLParserElementSegment):
			if segment.open:
				node = HTMLElementNode(parent, None, segment.attributes, segment.name)
			else:
				node = None

		elif isinstance(segment, HTMLParserTextSegment):
			node = HTMLTextNode(parent, segment.text)

		elif isinstance(segment, HTMLParserCommentSegment):
			node = HTMLCommentNode(parent, segment.comment)

		else:
			node = None

		return node
	
	def write(self, pretty: bool = True, indent: int = 2, tabs: bool = False, selfClosing: bool = True, shrinkText: bool = True, shrinkLimit: int = 20) -> str:
		"""Write the HTML document as a custom-formatted string.

		Args:
			pretty (bool, optional): Whether to pretty-print the html (newlines, indenting, etc). Defaults to True.
			indent (int, optional): The number of spaces to indent each child node from its parent (disabled if using tabs). Defaults to 2.
			tabs (bool, optional): Whether to use tabs instead of spaces (ignores indent size). Defaults to False.
			selfClosing (bool, optional): Whether to use self closing tags for elements that support them and have no children. Defaults to True.
			shrinkText (bool, optional): Whether to put elements and their content all on the same line if the content is a text node. Defaults to True.
			shrinkLimit (int, optional): If shrinkText is True, the maximum length of content to include in a single line before putting it indented on a new line. Defaults to 20.

		Returns:
			str: A formatted string representation of the HTML document
		"""

		def writeNode(document: HTMLDocument, nodeList: List[HTMLNode], pretty: bool, indent: int, selfClosing: bool, shrinkText: bool, shrinkLimit: int, depth: int = 0, first: bool = True) -> str:
			"""Write a single node.

			Args:
				document (HTMLDocument): The HTMLDocument object that is being written.
				nodeList (List[HTMLNode]): The list of sibling nodes to print.
				pretty (bool): Whether to pretty-print the html (newlines, indenting, etc)
				indent (int): The number of spaces to indent each child node from its parent (disabled if using tabs).
				selfClosing (bool): Whether to use self closing tags for elements that support them and have no children.
				shrinkText (bool): Whether to put elements and their content all on the same line if the content is a text node.
				shrinkLimit (int): If shrinkText is True, the maximum length of content to include in a single line before putting it indented on a new line.
				depth (int, optional): The number of nodes deep the current processing is. Defaults to 0.
				first (bool, optional): Whether the first node in the list is the first node of the document. Defaults to True.

			Returns:
				str: Returns a string representation of the supplied nodes, including any formatting appropriate to their location in the document.
			"""

			html: str = ""

			for node in nodeList:
				prefix: str = ""

				# Handle newlines and indentation if we are pretty printing.
				if pretty:
					# the first line in the document shouldn't have a newline before it.
					if first:
						first = False
					else:
						html += "\r\n"
					
					# Check whether we do tabs or spaces.
					if tabs:
						# For tabs, we will ignore the indent size.
						prefix = "".rjust(depth, "\t")
					else:
						prefix = "".rjust(depth * indent, " ")
					html += prefix

				# Elements and text/comments need to be handled differently.
				if isinstance(node, HTMLElementNode):
					if node.name not in document._neverSelfClosing and (node.name in document._voidTags or (selfClosing and len(node.children) == 0)):
						html += "<"
						if node.name == "!doctype":
							html += node.name.upper()
						else:
							html += node.name

						for key, value in node.attributes.items():
							if node.name == "!doctype" and value == "true":
								html += " " + key
							else:
								html += " " + key + "=\"" + value + "\""

						# Things like doctype tags should't have the "/"".
						if node.name not in document._voidTags:
							if len(node.attributes) > 0:
								html += " "
							html += "/"
						html += ">"

					else:
						html += "<"
						if node.name == "!doctype":
							html += node.name.upper()
						else:
							html += node.name

						for key, value in node.attributes.items():
							if node.name == "!doctype" and value == "true":
								html += " " + key
							else:
								html += " " + key + "=\"" + value + "\""
						html += ">"

						if shrinkText and len(node.children) == 1 and isinstance(node.children[0], HTMLTextNode) and len(node.children[0].html) <= shrinkLimit:
							html += node.children[0].html
						else:
							html += writeNode(document, node.children, pretty, indent, selfClosing, shrinkText, shrinkLimit, depth + 1, first)

							if pretty:
								html += "\r\n" + prefix
						html += "</" + node.name + ">"
				else:
					html += node.html

			return html
			
		return writeNode( self, self._rootList, pretty, indent, selfClosing, shrinkText, shrinkLimit)
			

class HTMLNode:
	
	parent: Optional["HTMLNode"]

	def __init__(self, parent: Optional["HTMLNode"] = None):
		self.parent = parent

	@property
	def html(self) -> str:
		return ""

class HTMLElementNode(HTMLNode):
	
	_children: List[HTMLNode]
	_attributes: Dict[str, str]

	name: str

	def __init__(self, parent: Optional[HTMLNode] = None, children: Optional[List[HTMLNode]] = None, attributes: Optional[Dict[str, str]] = None, name: str = "html"):
		super().__init__(parent)
		self.name = name
		
		if isinstance(children, list):
			self._children = children
		else:
			self._children = []

		if isinstance(attributes, dict):
			self._attributes = attributes
		else:
			self._attributes = {}

	@property
	def children(self) -> List[HTMLNode]:
		return self._children
	
	@property
	def attributes(self) -> Dict[str, str]:
		return self._attributes
	
	@property
	def html(self) -> str:
		"""Get the node and its descendants as a basic HTML string.

		Returns:
			str: Representation of the node and all children.
		"""

		html: str = "<" + self.name

		# Add attributes
		for key, value in self.attributes.items():
			html += " " + key + "=\"" + value + "\""
		
		# Check whether we should make the tag self closing.
		if len(self.children) > 0:
			html += ">" + self.innerHtml + "</" + self.name + ">"
		else:
			html += "/>"

		return html

	@property
	def innerHtml(self) -> str:
		"""Get the children of this node as a basic HTML string.

		Returns:
			str: Representation of all children.
		"""

		html: str = ""
		for child in self.children:
			html += child.html

		return html
	
	def getElementById(self, id: str) -> Optional["HTMLElementNode"]:
		"""Get the node with the specified id.

		Args:
			id (str): The id of the element to find.

		Returns:
			Optional[HTMLElementNode]: The first node with the specified id.
		"""

		def filter(node: HTMLNode) -> bool:
			return isinstance(node, HTMLElementNode) and "id" in node.attributes and node.attributes["id"] == id
		
		results: List[HTMLElementNode] = self.search(filter, maxResults = 1)
		if len(results) > 0:
			return results[0]
		else:
			return None
	
	def getElementsByAttribute(self, attribute: str, value: Optional[str] = None) -> List["HTMLElementNode"]:
		"""Get all elements with the specified attribute and, optionally, value. If the value is not specified,
			all elements that possess an attribute with the matching name, irrespective of value, will be returned.

		Args:
			attribute (str): The name of the attribute to look for in each node.
			value (str, optional): The value of the attribute.

		Returns:
			List[HTMLElementNode]: A list of all matching elements.
		"""

		def filter(node: HTMLNode) -> bool:
			return isinstance(node, HTMLElementNode) and attribute in node.attributes and (value is None or node.attributes[attribute] == value)
		
		return self.search(filter)

	def getElementsByClassName(self, className: str) -> List["HTMLElementNode"]:
		"""Get all elements where the specified class is among those on the element.

		Args:
			className (str): The name of the class to look for.

		Returns:
			List[HTMLElementNode]: A list of all matching elements.
		"""

		def filter(node: HTMLNode) -> bool:
			return isinstance(node, HTMLElementNode) and node.hasClass(className)
		
		return self.search(filter)
	
	def getElementsById(self, id: str) -> List["HTMLElementNode"]:
		"""Get all elements with the specified id. (In a well formed document, there should be 0-1)

		Args:
			id (str): The id to look for.

		Returns:
			List[HTMLElementNode]: A list of all matching elements.
		"""

		return self.getElementsByAttribute("id", id)

	def getElementsByName(self, name: str) -> List["HTMLElementNode"]:
		"""Get all elements with the specified name. (In a well formed document, there should be 0-1)

		Args:
			name (str): The name of the element to look for.

		Returns:
			List[HTMLElementNode]: A list of all matching elements.
		"""

		return self.getElementsByAttribute("name", name)

	def getElementsByTagName(self, tagName: str) -> List["HTMLElementNode"]:
		"""Get all elements of the specified tag type.

		Args:
			tagName (str): The type of tag to look for.

		Returns:
			List[HTMLElementNode]: A list of all matching elements.
		"""

		def filter(node: HTMLNode) -> bool:
			return isinstance(node, HTMLElementNode) and node.name == tagName
	
		return self.search(filter)
	
	def getText(self, maxDepth: Optional[int] = None, maxResults: Optional[int] = None) -> List[str]:
		"""Get the text from all text nodes under the current element.

		Args:
			maxDepth (Optional[int], optional): The maximum depth from the current node to search for text nodes in.
			maxResults (Optional[int], optional): The maximum number of results to find.

		Returns:
			List[str]: A list of text found (depth first).
		"""

		def filter(node: HTMLNode) -> bool:
			return isinstance(node, HTMLTextNode)
		
		textNodeList: List[HTMLTextNode] = self.search(filter, maxDepth = maxDepth, maxResults = maxResults)
		
		return [textNode.text for textNode in textNodeList]
	
	def hasClass(self, className: str) -> bool:
		"""Checks whether the specified class is among those on the element.

		Args:
			className (str): The name of the class to check for.

		Returns:
			bool: Whether the class was found on the element.
		"""

		if "class" in self.attributes:
			classList: List[str] = self.attributes["class"].split(" ")
			return className in classList
		else:
			return False

	def search(self, filter: Callable[[HTMLNode], bool], maxDepth: Optional[int] = None, maxResults: Optional[int] = None) -> List[HTMLNode]:
		"""Search for all elements in the node tree (including the parent) based on the specified filter function.

		Args:
			filter (Callable[[HTMLNode], bool]): The filter function that will return True/False indicating whether to include the element.
			maxDepth (Optional[int], optional): The maximum number of younger generations to search for the element (min 0). Defaults to None.
			maxResults (Optional[int], optional): The maximum number of the specified elements to return. Defaults to None.

		Returns:
			List[HTMLNode]: A list of all elements that match all of the specified crtieria for the search.
		"""
		
		def searchRecursive(results: List[HTMLNode], node: HTMLNode, filter: Callable[[HTMLNode], bool], depthRemaining: Optional[int], maxResults: Optional[int]) -> bool:
			"""Recursively check the specified node and all of its descendants for matches.

			Args:
				results (List[HTMLNode]): The list that matching elements should be added to.
				node (HTMLNode): The node to check for a match on and to check its children for.
				filter (Callable[[HTMLNode], bool]): The filter function that will return True/False indicating whether to include the element.
				depthRemaining (Optional[int]): The number of remaining generations to search through. None indicates all.
				maxResults (Optional[int]): The maximum number of the specified elements to return.

			Returns:
				bool: _description_
			"""

			if filter(node):
				results.append(node)
				if maxResults is not None and len(results) >= maxResults:
					return False

			if isinstance(node, HTMLElementNode) and (depthRemaining is None or (depthRemaining := depthRemaining - 1) >= 0):
				for child in node.children:
					if not searchRecursive(results, child, filter, depthRemaining, maxResults):
						return False
					
			return True
		
		results: List[HTMLNode] = []
		searchRecursive(results, self, filter, maxDepth, maxResults)

		return results

class HTMLTextNode(HTMLNode):
	
	text: str

	def __init__(self, parent: Optional[HTMLNode] = None, text: str = ""):
		super().__init__(parent)
		self.text = text

	@property
	def html(self) -> str:
		return self.text

class HTMLCommentNode(HTMLNode):
	
	comment: str

	def __init__(self, parent: Optional[HTMLNode] = None, comment: str = ""):
		super().__init__(parent)
		self.comment = comment

	@property
	def html(self) -> str:
		return "<!-- " + self.comment + " -->"