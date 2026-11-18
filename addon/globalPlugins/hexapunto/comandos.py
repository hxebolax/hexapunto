# Hexapunto: teclado braille Perkins para NVDA.
# Copyright (C) 2026 hxebolax
# Este archivo está cubierto por la Licencia Pública General de GNU, versión 2 o posterior.
# Consulta el archivo COPYING.txt para más detalles.

"""Órdenes de espacio con puntos que vienen asignadas de fábrica.

Las combinaciones siguen las de los teclados braille de las líneas HIMS,
Freedom Scientific y Seika que documenta la guía de NVDA (por ejemplo,
espacio con punto 1 es la flecha arriba y espacio con puntos 1 5, «e», es
Escape), así que quien ya use una línea braille no tiene que aprender nada
nuevo.

Todas son órdenes normales de NVDA de la categoría «Hexapunto»: se pueden
cambiar, quitar o añadir en Preferencias > Gestos de entrada, y a cualquier
combinación de Hexapunto se le puede asignar cualquier otra orden de NVDA.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import addonHandler
import inputCore
import keyboardHandler
from logHandler import log
from scriptHandler import script

from . import compat
from .gesto import SOURCE

addonHandler.initTranslation()

# Translators: category of the add-on commands in the Input Gestures dialog
CATEGORY = _("Hexapunto (teclado braille)")


def chord(*dots: int) -> str:
	"""Identificador de un gesto de espacio con puntos: ``chord(1, 2)`` → ``hexapunto:space+dot1+dot2``."""
	return f"{SOURCE}:" + "+".join(["space", *(f"dot{d}" for d in dots)])


#: Teclas emuladas: (nombre de la tecla para NVDA, descripción, gesto por defecto o ``None``).
EMULATED_KEYS: list[tuple[str, str, str | None]] = [
	# Translators: description of a command that emulates a key
	("upArrow", _("Pulsa la flecha arriba"), chord(1)),
	# Translators: description of a command that emulates a key
	("downArrow", _("Pulsa la flecha abajo"), chord(4)),
	# Translators: description of a command that emulates a key
	("leftArrow", _("Pulsa la flecha izquierda"), chord(3)),
	# Translators: description of a command that emulates a key
	("rightArrow", _("Pulsa la flecha derecha"), chord(6)),
	# Translators: description of a command that emulates a key
	("home", _("Pulsa Inicio"), chord(1, 2)),
	# Translators: description of a command that emulates a key
	("end", _("Pulsa Fin"), chord(4, 5)),
	# Translators: description of a command that emulates a key
	("control+home", _("Pulsa Control+Inicio (principio del texto)"), chord(1, 2, 3)),
	# Translators: description of a command that emulates a key
	("control+end", _("Pulsa Control+Fin (final del texto)"), chord(4, 5, 6)),
	# Translators: description of a command that emulates a key
	("control+leftArrow", _("Pulsa Control+flecha izquierda (palabra anterior)"), chord(2)),
	# Translators: description of a command that emulates a key
	("control+rightArrow", _("Pulsa Control+flecha derecha (palabra siguiente)"), chord(5)),
	# Translators: description of a command that emulates a key
	("pageUp", _("Pulsa Retroceder página"), chord(1, 2, 6)),
	# Translators: description of a command that emulates a key
	("pageDown", _("Pulsa Avanzar página"), chord(3, 4, 5)),
	# Translators: description of a command that emulates a key
	("shift+tab", _("Pulsa Mayúsculas+Tabulador"), chord(1, 3)),
	# Translators: description of a command that emulates a key
	("tab", _("Pulsa Tabulador"), chord(4, 6)),
	# Translators: description of a command that emulates a key
	("escape", _("Pulsa Escape"), chord(1, 5)),
	# Translators: description of a command that emulates a key
	("delete", _("Pulsa Suprimir"), chord(2, 5)),
	# Translators: description of a command that emulates a key
	("alt", _("Pulsa Alt (barra de menús)"), chord(1, 3, 4)),
	# Translators: description of a command that emulates a key
	("windows", _("Pulsa la tecla Windows"), chord(3, 4)),
	# Translators: description of a command that emulates a key
	("alt+tab", _("Pulsa Alt+Tabulador"), chord(2, 3, 4, 5)),
	# Translators: description of a command that emulates a key
	("windows+d", _("Pulsa Windows+D (mostrar el escritorio)"), chord(1, 4, 5)),
	# Translators: description of a command that emulates a key
	("applications", _("Pulsa la tecla de aplicaciones (menú contextual)"), chord(1, 2, 3, 4, 6)),
	# Translators: description of a command that emulates a key
	("control+z", _("Pulsa Control+Z (deshacer)"), chord(1, 3, 5, 6)),
	# Translators: description of a command that emulates a key
	("control+s", _("Pulsa Control+S (guardar)"), None),
	# Translators: description of a command that emulates a key
	("control+a", _("Pulsa Control+A (seleccionar todo en la mayoría de programas)"), None),
	# Translators: description of a command that emulates a key
	("control+c", _("Pulsa Control+C (copiar)"), None),
	# Translators: description of a command that emulates a key
	("control+x", _("Pulsa Control+X (cortar)"), None),
	# Translators: description of a command that emulates a key
	("control+v", _("Pulsa Control+V (pegar)"), None),
	# Translators: description of a command that emulates a key
	("enter", _("Pulsa Intro (sin pasar por la entrada braille)"), None),
	# Translators: description of a command that emulates a key
	("backspace", _("Pulsa Retroceso (sin pasar por la entrada braille)"), None),
]

#: Modificadores virtuales de la entrada braille de NVDA: (modificador, descripción).
VIRTUAL_MODIFIERS: list[tuple[str, str]] = [
	# Translators: description of a command that toggles a virtual modifier key
	("control", _("Activa o desactiva Control para la siguiente celda o tecla")),
	# Translators: description of a command that toggles a virtual modifier key
	("alt", _("Activa o desactiva Alt para la siguiente celda o tecla")),
	# Translators: description of a command that toggles a virtual modifier key
	("shift", _("Activa o desactiva Mayúsculas para la siguiente celda o tecla")),
	# Translators: description of a command that toggles a virtual modifier key
	("windows", _("Activa o desactiva Windows para la siguiente celda o tecla")),
	# Translators: description of a command that toggles a virtual modifier key
	("NVDA", _("Activa o desactiva la tecla NVDA para la siguiente celda o tecla")),
]

#: Gestos de fábrica de las órdenes propias del complemento.
DEFAULT_GESTURES: dict[str, list[str]] = {
	"toggle": ["kb:NVDA+alt+b"],
	"status": [chord(2, 4)],
	"cycleSounds": [chord(2, 3, 4)],
	"togglePractice": [chord(1, 2, 3, 4)],
	"commandList": [chord(1, 2, 5)],
	"showNvdaMenu": [chord(1, 3, 4, 5)],
	"sayAll": [chord(1, 2, 3, 4, 5, 6)],
}


def _safeName(key: str) -> str:
	return key.replace("+", "_")


def emulateKey(key: str) -> None:
	"""Pulsa una tecla, respetando lo que la entrada braille tenga a medias.

	Antes de mover el cursor se traduce lo que quede pendiente (una palabra en
	estenografía, por ejemplo) y, si hay modificadores virtuales activados con
	la entrada braille, se pulsan con la tecla.
	"""
	handler = compat.getInputHandler()
	try:
		if handler is not None:
			if handler.bufferBraille:
				handler.translate()
			if handler.currentModifiers:
				handler.emulateKey(key)
				handler.currentModifiers.clear()
				return
		inputCore.manager.emulateGesture(keyboardHandler.KeyboardInputGesture.fromName(key))
	except Exception:
		log.error("Hexapunto: no se pudo emular la tecla %s", key, exc_info=True)


def _makeEmulationScript(key: str, description: str, gesture: str | None) -> Callable[..., Any]:
	def emulationScript(self: Any, gesture: inputCore.InputGesture) -> None:
		emulateKey(key)

	emulationScript.__name__ = f"script_emulate_{_safeName(key)}"
	emulationScript.__doc__ = description
	return script(
		description=description,
		category=CATEGORY,
		gesture=gesture,
	)(emulationScript)


def _makeModifierScript(modifier: str, description: str) -> Callable[..., Any]:
	def modifierScript(self: Any, gesture: inputCore.InputGesture) -> None:
		handler = compat.getInputHandler()
		if handler is not None:
			handler.toggleModifier(modifier)

	modifierScript.__name__ = f"script_virtualModifier_{modifier}"
	modifierScript.__doc__ = description
	return script(description=description, category=CATEGORY)(modifierScript)


def generatedScripts() -> dict[str, Callable[..., Any]]:
	"""Órdenes generadas (emulación de teclas y modificadores virtuales)."""
	scripts: dict[str, Callable[..., Any]] = {}
	for key, description, gesture in EMULATED_KEYS:
		scripts[f"script_emulate_{_safeName(key)}"] = _makeEmulationScript(key, description, gesture)
	for modifier, description in VIRTUAL_MODIFIERS:
		scripts[f"script_virtualModifier_{modifier}"] = _makeModifierScript(modifier, description)
	return scripts
