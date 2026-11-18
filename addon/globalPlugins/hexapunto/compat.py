# Hexapunto: teclado braille Perkins para NVDA.
# Copyright (C) 2026 hxebolax
# Este archivo está cubierto por la Licencia Pública General de GNU, versión 2 o posterior.
# Consulta el archivo COPYING.txt para más detalles.

"""Compatibilidad entre versiones de NVDA (de la 2026.1 a la 2027.x).

NVDA 2026.3 trasladó la entrada braille del módulo ``brailleInput`` al paquete
``braille.input`` (``brailleInput`` sigue existiendo, pero obsoleto y con avisos
en el registro). También cambió la retrotraducción, que ahora hace
``louisHelper.backTranslate``. Este módulo reúne esas diferencias para que el
resto del complemento no tenga que preocuparse de la versión.
"""

from __future__ import annotations

from typing import Any

from logHandler import log

try:
	# NVDA 2026.3 y posteriores.
	import braille.input as _brailleInputModule
	from braille.input.gesture import BrailleInputGesture
except ImportError:
	# NVDA 2026.1 y 2026.2.
	import brailleInput as _brailleInputModule  # type: ignore[no-redef]
	from brailleInput import BrailleInputGesture  # type: ignore[no-redef, attr-defined]

__all__ = [
	"BrailleInputGesture",
	"DOT7",
	"DOT8",
	"backTranslate",
	"formatDots",
	"getInputHandler",
]

#: Máscaras de los puntos 7 y 8 (iguales en todas las versiones).
DOT7 = 1 << 6
DOT8 = 1 << 7

#: Inicio del rango de entrada en puntos de liblouis (modo ``dotsIO``).
_LOUIS_DOTS_IO_START = 0x8000


def getInputHandler() -> Any:
	"""El manejador de la entrada braille de NVDA (``None`` si aún no existe).

	Se consulta cada vez porque NVDA puede volver a crearlo.
	"""
	return getattr(_brailleInputModule, "handler", None)


def formatDots(dots: int) -> str:
	"""Números de los puntos de una celda separados por espacios («1 2 5»)."""
	return " ".join(str(i + 1) for i in range(8) if dots & (1 << i))


def backTranslate(tableFileName: str, cells: list[int]) -> str:
	"""Retrotraduce celdas braille a texto con la tabla indicada.

	Usa ``louisHelper.backTranslate`` si existe (NVDA 2026.3 y posteriores) y,
	si no, llama directamente a liblouis como hacía NVDA 2026.1.
	"""
	tableList = [tableFileName, "braille-patterns.cti"]
	try:
		import louisHelper

		func = getattr(louisHelper, "backTranslate", None)
		if func is not None:
			return func(tableList, cells)
	except ImportError:
		pass
	try:
		import louis

		inbuf = "".join(chr((cell & 0xFF) | _LOUIS_DOTS_IO_START) for cell in cells)
		mode = louis.dotsIO | getattr(louis, "noUndefinedDots", 0)
		return louis.backTranslate(tableList, inbuf, mode=mode)[0]
	except Exception:
		log.debugWarning("Hexapunto: no se pudo retrotraducir %r con %s", cells, tableFileName, exc_info=True)
		return ""
