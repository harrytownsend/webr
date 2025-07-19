from typing import Optional, Dict, List

class URL:

	# URL components
	protocol: Optional[str]
	_domain: List[str]
	port: Optional[int]
	_directory: List[str]
	file: Optional[str]
	_query: Dict[str, str]

	def __init__(self, url: Optional[str]):
		self.protocol = None
		self._domain = []
		self.port = None
		self._directory = []
		self.file = None
		self._query = {}

		if url is not None:
			self._parseURL(url)
	
	@property
	def domain(self) -> List[str]:
		return self._domain
	
	@domain.setter
	def domain(self, domain: List[str]) -> None:
		self._domain.clear()
		self._domain.extend(domain)

	@property
	def directory(self) -> List[str]:
		return self._directory
	
	@directory.setter
	def directory(self, directory: List[str]) -> None:
		self._directory.clear()
		self._directory.extend(directory)
	
	@property
	def query(self) -> Dict[str, str]:
		return self._query
	
	@query.setter
	def query(self, query: Dict[str, str]) -> None:
		self._query.clear()
		self._query.update(query)
	
	@property
	def URL(self) -> str:
		
		url: str = ""

		if self.protocol is not None:
			url += self.protocol + "://"

		if len(self._domain) > 0:
			url += ".".join(self.domain)

		if self.port is not None:
			url += ":" + str(self.port)

		if len(self._directory) > 0:
			url += "/" + "/".join(self._directory)

		if self.file is not None:
			url += "/" + self.file
		
		if len(self._query) > 0:
			url += "?"

			queries: List[str] = []
			for attribute in self._query:
				queries.append(URL.encode(attribute) + "=" + URL.encode(self._query[attribute]))
			url += "&".join(queries)

		return url

	@staticmethod
	def decode(text: str) -> str:
		"""Decode a URL encoded string.

		Args:
			text (str): The URL encoded text to decode.

		Returns:
			str: The decoded text.
		"""

		decoded: str = ""

		i: int = 0
		length: int = len(text)
		while i < length:
			char: str = text[i]

			if char == "&" and i + 2 < length:
				hexCode: str = text[i+1:i+3]
				asciiCode: int = int(hexCode, 16)
				decoded += chr(asciiCode)
				i += 3

			elif char == "+":
				decoded += " "
				i += 1
			else:
				decoded += char
				i += 1
		
		return decoded

	@staticmethod
	def encode(text: str) -> str:
		"""URL encode a string.

		Args:
			text (str): The text to be URL encoded.

		Returns:
			str: The URL encoded text
		"""

		encoded: str = ""
		for char in text:
			if char.isalnum() or char in ["-", "_", ".", "~"]:
				encoded += char
			else:
				asciiCode: int = ord(char)
				hexCode: int = hex(asciiCode)[2:].upper()  # Convert to hex and remove '0x' prefix, uppercase for URL encoding
				encoded += "%" + hexCode

		return encoded
	
	def _parseURL(self, url: str) -> None:
		"""Parse the URL string and populate the relevant fields.

		Args:
			url (str): The URL to parse.

		Raises:
			Exception: Invalid port format.
		"""
		
		protocolEnd: int
		domainStart: int
		domainEnd: int
		portStart: int
		portEnd: int
		directoryStart: int
		fileEnd: int
		queryStart: int

		length: int = len(url)

		protocolEnd = url.find("://")
		if protocolEnd >= 0:
			self.protocol = url[0:protocolEnd]
			domainStart = protocolEnd + 3
		else:
			domainStart = 0

		queryStart = url.find("?")
		if queryStart >= 0:
			fileEnd = queryStart

			if queryStart + 1 != length:
				queryDelimiter: str = "&" if url.find("&") >= 0 else ";"
				queries: List[str] = url[queryStart + 1:].split(queryDelimiter)
				for query in queries:
					attribute, value = query.split("=")
					attribute = URL.decode(attribute)
					value = URL.decode(value)

					self.query[attribute] = value
		else:
			fileEnd = length

		directoryStart = url.find("/", domainStart)
		if directoryStart >= 0:
			portEnd = directoryStart
			directoryStart += 1

			parts: List[str] = url[directoryStart:fileEnd].split("/")
			count: int = len(parts)

			self._directory = parts[0:count - 1]
			self.file = parts[count - 1]
		else:
			portEnd = queryStart if queryStart >= 0 else length

		portStart = url.find(":", domainStart)
		if portStart >= 0:
			domainEnd = portStart
			portStart += 1

			try:
				self.port = int(url[portStart:portEnd])
			except:
				raise Exception("Unable to parse port: " + url[portStart:portEnd])
		else:
			domainEnd = portEnd

		if domainStart != domainEnd:
			self._domain = url[domainStart:domainEnd].split(".")