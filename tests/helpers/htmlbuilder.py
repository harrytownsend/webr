from typing import List, Optional

class HTMLBuilder:

	_nodes: List[str]

	def __init__(self):
		self._nodes = []

	@property
	def nodes(self) -> List[str]:
		return self._nodes
	
	def get(self, spacing: bool = False) -> str:
		delimiter: str = "\n\t " if spacing else ""

		return delimiter.join(self._nodes)
	
	def append(self, node: str) -> int:
		index: int = len(self._nodes)
		self._nodes.append(node)
		return index