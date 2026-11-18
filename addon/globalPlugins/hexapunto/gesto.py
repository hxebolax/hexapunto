# Hexapunto: teclado braille Perkins para NVDA.
# Copyright (C) 2026 hxebolax
# Este archivo está cubierto por la Licencia Pública General de GNU, versión 2 o posterior.
# Consulta el archivo COPYING.txt para más detalles.

"""Gesto de entrada del teclado braille Hexapunto.

Cada combinación que se escribe con el teclado braille se convierte en un
gesto de NVDA, una subclase de ``BrailleInputGesture``, la misma clase que
usan las líneas braille con teclado braille. Así el gesto pasa por todo el
sistema de entrada de NVDA:

- las celdas se escriben con las órdenes de entrada braille de NVDA
  (``bk:dots``), con la tabla, el braille estenográfico, el eco de caracteres,
  los modificadores virtuales y la línea braille tal y como funcionan con un
  teclado braille de verdad;
- la ayuda de entrada (NVDA+1) dice qué hace cada combinación;
- en «Gestos de entrada» se puede asignar cualquier orden de NVDA a una
  combinación de Hexapunto, y las combinaciones aparecen con su nombre.

Los identificadores tienen dos partes: el propio de Hexapunto, que va
primero (``hexapunto:dot1+dot2+space``) y que solo existe con este teclado, y
los genéricos de teclado braille de NVDA (``bk:...``). Por eso las órdenes de
Hexapunto no afectan a los teclados braille de las líneas.
"""

from __future__ import annotations

import addonHandler
import inputCore

from .compat import DOT7, DOT8, BrailleInputGesture, formatDots

addonHandler.initTranslation()

#: Prefijo de los identificadores de los gestos de Hexapunto.
SOURCE = "hexapunto"
#: Teclas de la máquina que no son puntos.
EXTRA_LINE_FEED = "linefeed"
EXTRA_BACKSPACE = "backspace"


def makeIdentifier(dots: int, space: bool = False, extra: str | None = None) -> str:
	"""Identificador normalizado de un gesto de Hexapunto."""
	if extra:
		return inputCore.normalizeGestureIdentifier(f"{SOURCE}:{extra}")
	keys = [f"dot{i + 1}" for i in range(8) if dots & (1 << i)]
	if space:
		keys.append("space")
	return inputCore.normalizeGestureIdentifier(f"{SOURCE}:{'+'.join(keys)}")


def describe(dots: int, space: bool, extra: str | None = None) -> str:
	"""Descripción en español de una combinación («espacio con puntos 1 2»)."""
	if extra == EXTRA_LINE_FEED:
		# Translators: the line feed key of the braille keyboard
		return _("interlineado")
	if extra == EXTRA_BACKSPACE:
		# Translators: the backspace key of the braille keyboard
		return _("retroceso")
	numbers = formatDots(dots)
	if space and dots:
		# Translators: a chord of the space bar with dots; {dots} are dot numbers, e.g. "1 2 5"
		return _("espacio con puntos {dots}").format(dots=numbers)
	if space:
		# Translators: the space bar of the braille keyboard
		return _("espacio")
	if dots and (dots & (dots - 1)) == 0:
		# Translators: a single dot; {dots} is a dot number
		return _("punto {dots}").format(dots=numbers)
	# Translators: several dots pressed together; {dots} are dot numbers
	return _("puntos {dots}").format(dots=numbers)


class HexapuntoGesture(BrailleInputGesture):
	"""Una combinación escrita con el teclado braille Hexapunto."""

	def __init__(self, dots: int = 0, space: bool = False, extra: str | None = None) -> None:
		super().__init__()
		self.extra = extra
		if extra == EXTRA_LINE_FEED:
			# El interlineado equivale al punto 8 solo de los teclados braille (Intro).
			dots, space = DOT8, False
		elif extra == EXTRA_BACKSPACE:
			# El retroceso equivale al punto 7 solo (borrar la última celda).
			dots, space = DOT7, False
		self.dots = dots
		self.space = space

	def _get_identifiers(self) -> tuple[str, ...]:
		own = makeIdentifier(self.dots, self.space, self.extra)
		generic = tuple(BrailleInputGesture._get_identifiers(self))
		return (own, *generic)

	def _get_displayName(self) -> str | None:
		if not self.dots and not self.space:
			return None
		return describe(self.dots, self.space, self.extra)

	@classmethod
	def getDisplayTextForIdentifier(cls, identifier: str) -> tuple[str, str]:
		# Translators: name of the input source shown in the Input Gestures dialog
		source = _("Teclado braille Hexapunto")
		main = identifier.split(":", 1)[1] if ":" in identifier else identifier
		if main == EXTRA_LINE_FEED:
			return source, describe(0, False, EXTRA_LINE_FEED)
		if main == EXTRA_BACKSPACE:
			return source, describe(0, False, EXTRA_BACKSPACE)
		dots = 0
		space = False
		for part in main.split("+"):
			if part == "space":
				space = True
			elif part.startswith("dot") and part[3:].isdigit():
				dots |= 1 << (int(part[3:]) - 1)
		return source, describe(dots, space)


def register() -> None:
	"""Registra el origen de gestos para que NVDA sepa mostrar sus nombres."""
	inputCore.registerGestureSource(SOURCE, HexapuntoGesture)
