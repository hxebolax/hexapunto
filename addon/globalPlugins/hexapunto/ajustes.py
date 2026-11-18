# Hexapunto: teclado braille Perkins para NVDA.
# Copyright (C) 2026 hxebolax
# Este archivo está cubierto por la Licencia Pública General de GNU, versión 2 o posterior.
# Consulta el archivo COPYING.txt para más detalles.

"""Opciones del complemento en la configuración de NVDA.

Las opciones viven en la sección ``[hexapunto]`` de la configuración de NVDA,
así que funcionan con los perfiles de configuración: se puede, por ejemplo,
tener un perfil para un procesador de textos con otra tabla o sin sonidos.
"""

from __future__ import annotations

import json
from typing import Any

import addonHandler
import config
import languageHandler
from logHandler import log

addonHandler.initTranslation()

SECTION = "hexapunto"

#: Ámbito: dónde actúa el teclado braille cuando está activado.
SCOPE_EDITABLE = "editable"
SCOPE_ALWAYS = "always"

#: Aviso al pulsar una combinación de espacio con puntos sin orden asignada.
UNASSIGNED_BEEP = "beep"
UNASSIGNED_SPEECH = "speech"
UNASSIGNED_NONE = "none"

#: Juegos de sonidos.
SOUNDS_PERKINS = "perkins"
SOUNDS_SOFT = "soft"
SOUNDS_NONE = "none"

#: Tabla braille: la de entrada de NVDA, o la automática (integral del idioma).
TABLE_NVDA = "nvda"
TABLE_AUTO = "auto"

#: Tabla integral (literaria) de 6 puntos por idioma para la tabla automática.
#: Una máquina Perkins escribe braille literario: con la tabla informática de
#: 8 puntos «Hola» saldría mal escrito.
LITERARY_TABLES = {
	"es": "es-g1.ctb",
	"gl": "es-g1.ctb",
	"ca": "ca-g1.ctb",
	"eu": "es-g1.ctb",
	"pt": "Pt-Pt-g1.utb",
	"en": "en-ueb-g1.ctb",
	"fr": "fr-bfu-comp6.utb",
	"it": "it-it-comp6.utb",
	"de": "de-g1.ctb",
}

confspec: dict[str, str] = {
	# General
	"enableOnStartup": "boolean(default=False)",
	"scope": f"option('{SCOPE_EDITABLE}', '{SCOPE_ALWAYS}', default='{SCOPE_EDITABLE}')",
	"announceActivationInField": "boolean(default=False)",
	# Teclado
	"layout": "string(default='perkins')",
	"customKeys": "string(default='')",
	"dots": "integer(default=6, min=6, max=8)",
	"enterAndBackspaceAsPerkins": "boolean(default=True)",
	"blockOtherKeys": "boolean(default=False)",
	"oneHand": "boolean(default=False)",
	# Escritura
	"table": f"string(default='{TABLE_AUTO}')",
	"spanishMarks": "boolean(default=True)",
	"practiceMode": "boolean(default=False)",
	"speakDots": "boolean(default=False)",
	"unassignedFeedback": (
		f"option('{UNASSIGNED_BEEP}', '{UNASSIGNED_SPEECH}', '{UNASSIGNED_NONE}', default='{UNASSIGNED_BEEP}')"
	),
	# Sonidos y máquina
	"sounds": f"option('{SOUNDS_PERKINS}', '{SOUNDS_SOFT}', '{SOUNDS_NONE}', default='{SOUNDS_PERKINS}')",
	"volume": "integer(default=80, min=0, max=100)",
	"paperSounds": "boolean(default=True)",
	"bell": "boolean(default=True)",
	"lineLength": "integer(default=40, min=10, max=100)",
	"bellCells": "integer(default=6, min=1, max=20)",
	"marginStop": "boolean(default=False)",
}


def register() -> None:
	"""Añade la especificación de las opciones a la configuración de NVDA."""
	config.conf.spec[SECTION] = confspec


def section() -> Any:
	return config.conf[SECTION]


def get(key: str) -> Any:
	"""Valor de una opción (con el valor por defecto si algo falla)."""
	try:
		return config.conf[SECTION][key]
	except Exception:
		log.debugWarning("Hexapunto: no se pudo leer la opción %s", key, exc_info=True)
		spec = confspec.get(key, "")
		if spec.startswith("boolean"):
			return "default=True" in spec
		return None


def setValue(key: str, value: Any) -> None:
	config.conf[SECTION][key] = value


def customKeys() -> dict[str, int]:
	"""Teclas de la distribución personalizada: papel → código de exploración."""
	raw = get("customKeys") or ""
	if not raw:
		return {}
	try:
		data = json.loads(raw)
		return {str(k): int(v) for k, v in data.items() if v is not None}
	except Exception:
		log.debugWarning("Hexapunto: distribución personalizada no válida: %r", raw, exc_info=True)
		return {}


def setCustomKeys(keys: dict[str, int]) -> None:
	setValue("customKeys", json.dumps(keys, sort_keys=True))


def autoTableFileName() -> str | None:
	"""Tabla integral del idioma de NVDA, o ``None`` si no hay una conocida."""
	import brailleTables

	lang = (languageHandler.getLanguage() or "").split("_")[0].lower()
	name = LITERARY_TABLES.get(lang)
	if name is None:
		return None
	try:
		brailleTables.getTable(name)
	except LookupError:
		return None
	return name


def resolvedTableFileName() -> str | None:
	"""Archivo de la tabla que usa el teclado braille.

	``None`` significa «la tabla de entrada de NVDA, sin cambiarla». La tabla
	automática es la integral (literaria) del idioma con 6 puntos y la de
	entrada de NVDA con 8 puntos.
	"""
	import brailleTables

	name = get("table") or TABLE_AUTO
	if name == TABLE_NVDA:
		return None
	if name == TABLE_AUTO:
		# Con 8 puntos se escribe braille informático: la tabla de entrada de NVDA.
		if int(get("dots") or 6) == 8:
			return None
		return autoTableFileName()
	try:
		brailleTables.getTable(name)
	except LookupError:
		log.warning("Hexapunto: la tabla %s no existe; se usa la tabla de entrada de NVDA", name)
		return None
	return name
