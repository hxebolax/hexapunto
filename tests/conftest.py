# Hexapunto: pruebas automáticas.
# Copyright (C) 2026 Héctor J. Benítez Corredera
# Este archivo está cubierto por la Licencia Pública General de GNU, versión 2 o posterior.

"""Entorno de pruebas: módulos de NVDA simulados.

Las pruebas no necesitan NVDA instalado. Este archivo crea versiones mínimas
de los módulos de NVDA que usa el complemento (``inputCore``,
``keyboardHandler``, ``braille.input``, ``config``...) que registran lo que
el complemento hace con ellos, y añade la carpeta ``addon`` a la ruta de
importación.

La prueba del panel de opciones usa además ``gui/guiHelper.py`` del código
fuente real de NVDA si se encuentra (variable de entorno ``NVDA_SOURCE`` o
carpetas ``../nvda/source`` y ``adjuntos/nvda/source``); si no, se omite.
"""

from __future__ import annotations

import builtins
import os
import sys
import types
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
ADDON = ROOT / "addon"


def _findNvdaSource() -> Path | None:
	candidates = [
		os.environ.get("NVDA_SOURCE"),
		ROOT.parent / "nvda" / "source",
		ROOT / "adjuntos" / "nvda" / "source",
	]
	for c in candidates:
		if c and (Path(c) / "gui" / "guiHelper.py").is_file():
			return Path(c)
	return None


NVDA_SOURCE = _findNvdaSource()

builtins._ = lambda s: s  # type: ignore[attr-defined]
builtins.ngettext = lambda s, p, n: s if n == 1 else p  # type: ignore[attr-defined]
builtins.pgettext = lambda c, s: s  # type: ignore[attr-defined]


def _module(name: str, **attrs: Any) -> types.ModuleType:
	mod = types.ModuleType(name)
	mod.__dict__.update(attrs)
	sys.modules[name] = mod
	return mod


# ---------------------------------------------------------------- utilidades
class _Log:
	def __init__(self) -> None:
		self.errors: list[str] = []

	def _record(self, msg: str, *args: Any, **kwargs: Any) -> None:
		self.errors.append(msg % args if args else msg)

	error = exception = _record

	def warning(self, *a: Any, **k: Any) -> None:
		pass

	debug = debugWarning = info = io = warning

	def isEnabledFor(self, level: Any) -> bool:
		return False


log = _Log()
_module("logHandler", log=log)
_module("addonHandler", initTranslation=lambda: None)


class AutoPropertyObject:
	"""Versión mínima de las propiedades automáticas de NVDA (``_get_x`` → ``x``)."""

	def __getattr__(self, name: str) -> Any:
		for cls in type(self).__mro__:
			getter = cls.__dict__.get(f"_get_{name}")
			if getter is not None:
				return getter(self)
		raise AttributeError(name)


# ---------------------------------------------------------------- config
class _Section(dict):
	pass


class _Validation:
	def __init__(self, default: Any) -> None:
		self.default = default


def _parseDefault(spec: str) -> Any:
	import re

	m = re.search(r"default='?([^,')]*)", spec)
	raw = m.group(1) if m else ""
	if spec.startswith("boolean"):
		return raw == "True"
	if spec.startswith("integer"):
		return int(raw)
	return raw


class _Conf(dict):
	def __init__(self) -> None:
		super().__init__()
		self.spec: dict[str, Any] = {}

	def __getitem__(self, key: str) -> Any:
		if key not in self and key in self.spec:
			self[key] = _Section({k: _parseDefault(v) for k, v in self.spec[key].items()})
		return super().__getitem__(key)

	def getConfigValidation(self, keyPath: tuple[str, str]) -> _Validation:
		section, key = keyPath
		return _Validation(_parseDefault(self.spec[section][key]))


class _Action:
	def __init__(self) -> None:
		self.handlers: list[Any] = []

	def register(self, h: Any) -> None:
		self.handlers.append(h)

	def unregister(self, h: Any) -> None:
		if h in self.handlers:
			self.handlers.remove(h)


conf = _Conf()
_module("config", conf=conf, post_configProfileSwitch=_Action())
_module("languageHandler", getLanguage=lambda: "es_ES")
_module(
	"globalVars",
	appArgs=types.SimpleNamespace(secure=True, configPath=str(ROOT / "tests" / "_config")),
	focusObject=None,
)


# ---------------------------------------------------------------- brailleTables
class BrailleTable(types.SimpleNamespace):
	pass


_TABLES = {
	"es-g1.ctb": BrailleTable(
		fileName="es-g1.ctb", displayName="Español grado 1", contracted=False, input=True
	),
	"es-g2.ctb": BrailleTable(
		fileName="es-g2.ctb", displayName="Español grado 2", contracted=True, input=True
	),
	"Es-Es-G0.utb": BrailleTable(
		fileName="Es-Es-G0.utb", displayName="Español 8 puntos", contracted=False, input=True
	),
	"en-ueb-g1.ctb": BrailleTable(
		fileName="en-ueb-g1.ctb", displayName="English UEB 1", contracted=False, input=True
	),
}


def _getTable(name: str) -> BrailleTable:
	try:
		return _TABLES[name]
	except KeyError:
		raise LookupError(name) from None


_module("brailleTables", getTable=_getTable, listTables=lambda: list(_TABLES.values()))


# ---------------------------------------------------------------- entrada
class NoInputGestureAction(LookupError):
	pass


def normalizeGestureIdentifier(identifier: str) -> str:
	identifier = identifier.lower()
	prefix, main = identifier.split(":", 1)
	parts = main.split("+")
	parts.sort()
	return f"{prefix}:{'+'.join(parts)}"


class InputGesture(AutoPropertyObject):
	pass


class _Manager:
	def __init__(self) -> None:
		self.executed: list[Any] = []
		self.emulated: list[Any] = []
		#: Identificadores sin orden (executeGesture lanza NoInputGestureAction).
		self.unbound: set[str] = set()
		self.isInputHelpActive = False

	def executeGesture(self, gesture: Any) -> None:
		self.executed.append(gesture)
		if all(normalizeGestureIdentifier(i) in self.unbound for i in gesture.identifiers):
			raise NoInputGestureAction

	def emulateGesture(self, gesture: Any) -> None:
		self.emulated.append(gesture)

	def getAllGestureMappings(self) -> dict[str, Any]:
		return {}


class _Decider:
	def __init__(self) -> None:
		self.handlers: list[Any] = []

	def register(self, h: Any) -> None:
		self.handlers.append(h)

	def unregister(self, h: Any) -> None:
		if h in self.handlers:
			self.handlers.remove(h)

	def decide(self, **kwargs: Any) -> bool:
		return all(h(**kwargs) for h in list(self.handlers))


gestureSources: dict[str, Any] = {}
inputCore = _module(
	"inputCore",
	NoInputGestureAction=NoInputGestureAction,
	normalizeGestureIdentifier=normalizeGestureIdentifier,
	InputGesture=InputGesture,
	manager=_Manager(),
	decide_handleRawKey=_Decider(),
	gestureSources=gestureSources,
	registerGestureSource=lambda s, c: gestureSources.__setitem__(s, c),
	getDisplayTextForGestureIdentifier=lambda i: ("", i),
)


class KeyboardInputGesture:
	def __init__(self, name: str) -> None:
		self.name = name

	@classmethod
	def fromName(cls, name: str) -> KeyboardInputGesture:
		return cls(name)


keyboardHandler = _module(
	"keyboardHandler",
	currentModifiers=set(),
	passKeyThroughCount=-1,
	ignoreInjected=False,
	KeyboardInputGesture=KeyboardInputGesture,
)


# Cola de NVDA: en las pruebas las funciones se ejecutan al momento.
def _queueFunction(queue: Any, func: Any, *args: Any, **kwargs: Any) -> None:
	kwargs.pop("_immediate", None)
	func(*args, **kwargs)


_module("queueHandler", eventQueue=object(), queueFunction=_queueFunction)

spoken: list[str] = []
beeps: list[tuple[int, int]] = []
_module("speech", speakMessage=lambda text, *a, **k: spoken.append(text))
_module("ui", message=lambda text, *a, **k: spoken.append(text), browseableMessage=lambda *a, **k: None)
_module("tones", beep=lambda hz, ms, left=50, right=50: beeps.append((hz, ms)))
_module("nvwave", playWaveFile=lambda *a, **k: None)
_module("api", getFocusObject=lambda: None)


class Role:
	EDITABLETEXT = "editableText"
	TERMINAL = "terminal"
	PASSWORDEDIT = "passwordEdit"
	DOCUMENT = "document"
	BUTTON = "button"


class State:
	EDITABLE = "editable"
	READONLY = "readonly"


_module("controlTypes", Role=Role, State=State)
_module("NVDAObjects")
_module("NVDAObjects.behaviors", EditableText=type("EditableText", (), {}))


# ---------------------------------------------------------------- braille.input
DOT7 = 1 << 6
DOT8 = 1 << 7


class BrailleInputGesture(InputGesture):
	"""Copia de la lógica de identificadores de NVDA (braille/input/gesture.py)."""

	dots = 0
	space = False

	def _makeDotsId(self) -> str:
		items = [f"dot{i + 1}" for i in range(8) if self.dots & (1 << i)]
		if self.space:
			items.append("space")
		return "bk:" + "+".join(items)

	GENERIC_ID_SPACE_DOTS = normalizeGestureIdentifier("bk:space+dots")
	GENERIC_ID_DOTS = normalizeGestureIdentifier("bk:dots")

	def _get_identifiers(self) -> tuple[str, ...]:
		if self.space and self.dots:
			return (self._makeDotsId(), self.GENERIC_ID_SPACE_DOTS)
		elif self.dots in (DOT7, DOT8, DOT7 | DOT8):
			return (self._makeDotsId(), self.GENERIC_ID_DOTS)
		elif self.dots or self.space:
			return (self.GENERIC_ID_DOTS,)
		return ()


class FakeInputHandler:
	def __init__(self) -> None:
		self._table = _TABLES["Es-Es-G0.utb"]
		self.bufferBraille: list[int] = []
		self.bufferText = ""
		self.currentModifiers: set[str] = set()
		self.sent: list[str] = []
		self.flushed = 0

	def flushBuffer(self) -> None:
		self.flushed += 1

	def handlePostConfigProfileSwitch(self) -> None:
		self._table = _TABLES["Es-Es-G0.utb"]

	def sendChars(self, chars: str) -> None:
		self.sent.append(chars)

	def translate(self) -> None:
		self.bufferBraille = []

	def emulateKey(self, key: str) -> None:
		self.sent.append(f"<{'+'.join([*sorted(self.currentModifiers), key])}>")

	def toggleModifier(self, m: str) -> None:
		self.currentModifiers ^= {m}


braillePkg = _module("braille")
braillePkg.__path__ = []  # type: ignore[attr-defined]
brailleInputPkg = _module("braille.input", handler=FakeInputHandler())
brailleInputPkg.__path__ = []  # type: ignore[attr-defined]
braillePkg.input = brailleInputPkg  # type: ignore[attr-defined]
_module("braille.input.gesture", BrailleInputGesture=BrailleInputGesture)


def _backTranslate(tables: list[str], cells: list[int]) -> str:
	letters = {0b1: "a", 0b11: "b", 0b1001: "c", 0b100010: "?", 0b10110: "!"}
	return "".join(letters.get(c, "") for c in cells)


_module("louisHelper", backTranslate=_backTranslate)


# ---------------------------------------------------------------- scriptHandler y complementos
def script(**kwargs: Any) -> Any:
	def decorator(func: Any) -> Any:
		gestures = list(kwargs.get("gestures") or [])
		if kwargs.get("gesture"):
			gestures.append(kwargs["gesture"])
		func.gestures = gestures
		func.category = kwargs.get("category")
		func.__doc__ = kwargs.get("description")
		return func

	return decorator


_module("scriptHandler", script=script)


class ScriptableType(type):
	def __new__(mcs, name: str, bases: tuple[type, ...], ns: dict[str, Any]) -> Any:
		cls = super().__new__(mcs, name, bases, ns)
		gestures: dict[str, str] = {}
		for attr, value in ns.items():
			if attr.startswith("script_"):
				for g in getattr(value, "gestures", []):
					gestures[g] = attr[len("script_") :]
		setattr(cls, f"_{name}__gestures", gestures)
		return cls


class GlobalPlugin(metaclass=ScriptableType):
	def __init__(self) -> None:
		self._gestureMap: dict[str, str] = {}
		for cls in reversed(type(self).__mro__):
			for g, s in getattr(cls, f"_{cls.__name__}__gestures", {}).items():
				self._gestureMap[normalizeGestureIdentifier(g)] = s

	def terminate(self) -> None:
		pass


_module("globalPluginHandler", GlobalPlugin=GlobalPlugin)
_module(
	"globalCommands",
	commands=types.SimpleNamespace(script_showGui=lambda g: None, script_sayAll=lambda g: None),
)
guiMod = _module("gui", mainFrame=None, messageBox=lambda *a, **k: None)
guiMod.settingsDialogs = _module(  # type: ignore[attr-defined]
	"gui.settingsDialogs",
	NVDASettingsDialog=types.SimpleNamespace(categoryClasses=[]),
)

sys.path.insert(0, str(ADDON))
sys.path.insert(0, str(ADDON / "globalPlugins"))


# ---------------------------------------------------------------- objetos de prueba
class FakeObj:
	def __init__(self, role: str = Role.EDITABLETEXT, states: set[str] | None = None, ti: Any = None) -> None:
		self.role = role
		self.states = states if states is not None else {State.EDITABLE}
		self.treeInterceptor = ti
		self.sleepMode = False


@pytest.fixture
def env() -> Any:
	"""Estado limpio para cada prueba."""
	conf.clear()
	inputCore.manager.executed.clear()
	inputCore.manager.emulated.clear()
	inputCore.manager.unbound.clear()
	keyboardHandler.currentModifiers.clear()
	keyboardHandler.ignoreInjected = False
	keyboardHandler.passKeyThroughCount = -1
	spoken.clear()
	beeps.clear()
	brailleInputPkg.handler = FakeInputHandler()
	log.errors.clear()
	return types.SimpleNamespace(
		conf=conf,
		manager=inputCore.manager,
		keyboardHandler=keyboardHandler,
		spoken=spoken,
		beeps=beeps,
		handler=brailleInputPkg.handler,
		log=log,
		FakeObj=FakeObj,
		Role=Role,
		State=State,
	)
