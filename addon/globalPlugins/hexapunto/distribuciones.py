# Hexapunto: teclado braille Perkins para NVDA.
# Copyright (C) 2026 hxebolax
# Este archivo está cubierto por la Licencia Pública General de GNU, versión 2 o posterior.
# Consulta el archivo COPYING.txt para más detalles.

"""Distribuciones de teclas del teclado braille.

Las teclas se identifican por su **código de exploración** (la posición
física en el teclado), no por la letra que tienen impresa. Así la
distribución funciona igual con un teclado español, inglés, francés o
alemán: la tecla «Ñ» de un teclado español es la «;» de uno inglés, y las
dos hacen de punto 8 o de retroceso.

La máquina Perkins tiene, de izquierda a derecha, la tecla de interlineado,
las teclas de los puntos 3, 2 y 1, el espaciador, las teclas de los puntos
4, 5 y 6 y la tecla de retroceso. La distribución clásica las pone en la
fila central del teclado: A, S D F, espacio, J K L y Ñ.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass, field

import addonHandler

addonHandler.initTranslation()

#: Papeles de las teclas en el teclado braille.
DOT_ROLES = tuple(f"dot{i}" for i in range(1, 9))
ROLE_SPACE = "space"
ROLE_LINE_FEED = "lineFeed"
ROLE_BACKSPACE = "backspace"
ALL_ROLES = (*DOT_ROLES, ROLE_SPACE, ROLE_LINE_FEED, ROLE_BACKSPACE)

#: Códigos de exploración (conjunto 1) de las teclas que se usan.
SC = {
	"Q": 0x10,
	"W": 0x11,
	"E": 0x12,
	"R": 0x13,
	"T": 0x14,
	"Y": 0x15,
	"U": 0x16,
	"I": 0x17,
	"O": 0x18,
	"P": 0x19,
	"A": 0x1E,
	"S": 0x1F,
	"D": 0x20,
	"F": 0x21,
	"G": 0x22,
	"H": 0x23,
	"J": 0x24,
	"K": 0x25,
	"L": 0x26,
	"Ñ": 0x27,
	"SPACE": 0x39,
}
#: Intro y Retroceso del teclado principal (no los del teclado numérico).
SCAN_ENTER = 0x1C
SCAN_BACKSPACE = 0x0E
#: Escape (para cancelar la captura de una tecla).
SCAN_ESCAPE = 0x01


def roleLabel(role: str) -> str:
	"""Nombre de un papel para mostrarlo a la persona usuaria."""
	if role.startswith("dot"):
		# Translators: name of a braille keyboard key, e.g. "Punto 1"
		return _("Punto {n}").format(n=role[3:])
	labels = {
		# Translators: name of the space bar of the braille keyboard
		ROLE_SPACE: _("Espaciador"),
		# Translators: name of the line feed key of a Perkins brailler
		ROLE_LINE_FEED: _("Interlineado (nueva línea)"),
		# Translators: name of the backspace key of a Perkins brailler
		ROLE_BACKSPACE: _("Retroceso"),
	}
	return labels.get(role, role)


@dataclass(frozen=True)
class Layout:
	"""Una distribución de teclas."""

	id: str
	name: str
	description: str
	keys: dict[str, int] = field(default_factory=dict)


def _layout(id: str, name: str, description: str, **letters: str) -> Layout:
	return Layout(id, name, description, {role: SC[letter] for role, letter in letters.items()})


def builtinLayouts() -> list[Layout]:
	"""Distribuciones incluidas en el complemento."""
	return [
		_layout(
			"perkins",
			# Translators: name of a keyboard layout
			_("Perkins clásica (F D S · J K L)"),
			# Translators: description of a keyboard layout
			_(
				"Puntos 1 2 3 en F D S y 4 5 6 en J K L, como las teclas de una máquina Perkins. "
				"A es el interlineado y Ñ el retroceso; con 8 puntos, A es el punto 7 y Ñ el punto 8.",
			),
			dot1="F",
			dot2="D",
			dot3="S",
			dot4="J",
			dot5="K",
			dot6="L",
			dot7="A",
			dot8="Ñ",
			space="SPACE",
			lineFeed="A",
			backspace="Ñ",
		),
		_layout(
			"slate",
			# Translators: name of a keyboard layout
			_("Pizarra, escritura en espejo (J K L · F D S)"),
			# Translators: description of a keyboard layout
			_(
				"Para quien aprendió con pauta y punzón: los puntos 1 2 3 están a la derecha (J K L) "
				"y los 4 5 6 a la izquierda (F D S), como al escribir en la pizarra.",
			),
			dot1="J",
			dot2="K",
			dot3="L",
			dot4="F",
			dot5="D",
			dot6="S",
			dot7="Ñ",
			dot8="A",
			space="SPACE",
			lineFeed="A",
			backspace="Ñ",
		),
		_layout(
			"topRow",
			# Translators: name of a keyboard layout
			_("Fila superior (R E W · U I O)"),
			# Translators: description of a keyboard layout
			_(
				"Los puntos en la fila de arriba: 1 2 3 en R E W y 4 5 6 en U I O. "
				"Q es el interlineado (o el punto 7) y P el retroceso (o el punto 8).",
			),
			dot1="R",
			dot2="E",
			dot3="W",
			dot4="U",
			dot5="I",
			dot6="O",
			dot7="Q",
			dot8="P",
			space="SPACE",
			lineFeed="Q",
			backspace="P",
		),
		_layout(
			"inner",
			# Translators: name of a keyboard layout
			_("Centrada (G F D · H J K)"),
			# Translators: description of a keyboard layout
			_(
				"Las manos un poco más juntas: 1 2 3 en G F D y 4 5 6 en H J K. "
				"S es el interlineado (o el punto 7) y L el retroceso (o el punto 8).",
			),
			dot1="G",
			dot2="F",
			dot3="D",
			dot4="H",
			dot5="J",
			dot6="K",
			dot7="S",
			dot8="L",
			space="SPACE",
			lineFeed="S",
			backspace="L",
		),
	]


#: Identificador de la distribución personalizada.
CUSTOM_ID = "custom"


def customLayout(keys: dict[str, int]) -> Layout:
	base = getLayout("perkins").keys
	merged = dict(base)
	merged.update({k: v for k, v in keys.items() if k in ALL_ROLES})
	return Layout(
		CUSTOM_ID,
		# Translators: name of the user defined keyboard layout
		_("Personalizada"),
		# Translators: description of the user defined keyboard layout
		_("Las teclas que elijas para cada punto y para las teclas de la máquina."),
		merged,
	)


def getLayout(layoutId: str, custom: dict[str, int] | None = None) -> Layout:
	"""Distribución por su identificador (la clásica si no existe)."""
	if layoutId == CUSTOM_ID:
		return customLayout(custom or {})
	layouts = builtinLayouts()
	for layout in layouts:
		if layout.id == layoutId:
			return layout
	return layouts[0]


def allLayouts(custom: dict[str, int] | None = None) -> list[Layout]:
	return [*builtinLayouts(), customLayout(custom or {})]


def buildScanMap(layout: Layout, dots: int, enterAndBackspace: bool) -> dict[int, str]:
	"""Tabla código de exploración → papel para el teclado en uso.

	- Con 6 puntos no se usan los puntos 7 y 8.
	- Con 8 puntos, si el punto 7 u 8 comparte tecla con el interlineado o el
	  retroceso, la tecla es del punto (el interlineado y el retroceso siguen
	  disponibles con los puntos 8 y 7 solos, como en los teclados braille de
	  NVDA, y con Intro y Retroceso).
	- Si se pide, Intro y Retroceso hacen de interlineado y retroceso braille
	  (así se traduce antes lo que esté a medias, por ejemplo en estenografía).
	"""
	scanMap: dict[int, str] = {}
	if enterAndBackspace:
		scanMap[SCAN_ENTER] = ROLE_LINE_FEED
		scanMap[SCAN_BACKSPACE] = ROLE_BACKSPACE
	for role in (ROLE_LINE_FEED, ROLE_BACKSPACE):
		scan = layout.keys.get(role)
		if scan:
			scanMap[scan] = role
	for role in (*DOT_ROLES, ROLE_SPACE):
		if dots == 6 and role in ("dot7", "dot8"):
			continue
		scan = layout.keys.get(role)
		if scan:
			scanMap[scan] = role
	return scanMap


def findConflicts(keys: dict[str, int], dots: int) -> list[tuple[str, str]]:
	"""Parejas de papeles que comparten tecla y que se estorban.

	Que el punto 7 u 8 comparta tecla con el interlineado o el retroceso no es
	un conflicto (es lo normal), así que no se cuenta.
	"""
	allowed = {
		frozenset(("dot7", ROLE_LINE_FEED)),
		frozenset(("dot8", ROLE_BACKSPACE)),
		frozenset(("dot7", ROLE_BACKSPACE)),
		frozenset(("dot8", ROLE_LINE_FEED)),
	}
	roles = [r for r in ALL_ROLES if keys.get(r) and not (dots == 6 and r in ("dot7", "dot8"))]
	conflicts: list[tuple[str, str]] = []
	for i, a in enumerate(roles):
		for b in roles[i + 1 :]:
			if keys[a] == keys[b] and frozenset((a, b)) not in allowed:
				conflicts.append((a, b))
	return conflicts


def keyName(scanCode: int) -> str:
	"""Nombre de una tecla según la distribución de teclado de Windows («F», «Ñ», «Espacio»)."""
	if not scanCode:
		# Translators: shown when a braille keyboard key has no key assigned
		return _("sin asignar")
	try:
		buf = ctypes.create_unicode_buffer(64)
		user32 = ctypes.windll.user32
		user32.GetKeyNameTextW.argtypes = (ctypes.c_long, ctypes.c_wchar_p, ctypes.c_int)
		user32.GetKeyNameTextW.restype = ctypes.c_int
		if user32.GetKeyNameTextW(scanCode << 16, buf, len(buf)) > 0 and buf.value:
			name = buf.value
			return name if len(name) > 1 else name.upper()
	except Exception:
		pass
	# Translators: name of a key when Windows does not provide one; {code} is a hexadecimal number
	return _("código {code:02X}").format(code=scanCode)
