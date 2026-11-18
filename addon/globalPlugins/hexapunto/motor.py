# Hexapunto: teclado braille Perkins para NVDA.
# Copyright (C) 2026 hxebolax
# Este archivo está cubierto por la Licencia Pública General de GNU, versión 2 o posterior.
# Consulta el archivo COPYING.txt para más detalles.

"""Motor del teclado braille: convierte el teclado del PC en una máquina Perkins.

Funcionamiento
==============

1. El motor se registra en ``inputCore.decide_handleRawKey``, el punto de
   extensión que NVDA consulta con cada pulsación y soltura de tecla **antes
   de procesarla**. Este código corre en el hilo del gancho del teclado: tiene
   que ser muy rápido y no puede tocar objetos de NVDA que hagan llamadas
   entre procesos. Por eso solo lee datos ya calculados (si el foco es un
   campo de texto lo anota el hilo principal al cambiar el foco).
2. Mientras se mantienen pulsadas teclas de puntos, se acumulan en una
   combinación (acorde). Las teclas se capturan: no llegan a Windows.
3. Al soltar **todas** las teclas, la combinación se envía al hilo principal de
   NVDA, que crea un :class:`gesto.HexapuntoGesture` y lo ejecuta con
   ``inputCore.manager.executeGesture``, igual que haría una línea braille.

Las demás teclas del teclado siguen funcionando como siempre, y cualquier
tecla pulsada con Control, Alt, Windows, Mayúsculas o la tecla NVDA llega
sin cambios (los atajos siguen funcionando).
"""

from __future__ import annotations

import time
import weakref
from typing import Any

import addonHandler
import brailleTables
import controlTypes
import inputCore
import keyboardHandler
import queueHandler
import speech
import tones
import ui
from logHandler import log

from . import ajustes, compat, distribuciones
from .distribuciones import ROLE_BACKSPACE, ROLE_LINE_FEED, ROLE_SPACE
from .gesto import EXTRA_BACKSPACE, EXTRA_LINE_FEED, HexapuntoGesture, describe
from .maquina import PerkinsMachine

addonHandler.initTranslation()

#: Signos que en braille español son la misma celda al abrir y al cerrar.
_OPENING = {"?": "¿", "!": "¡"}
_CLOSING = {v: k for k, v in _OPENING.items()}

#: Tablas del braille literario español, donde «¿» y «?» (y «¡» y «!») son la misma celda.
_SPANISH_LITERARY_TABLES = frozenset(("es-g1.ctb", "es-g2.ctb"))

#: Tecla virtual de los caracteres Unicode enviados con SendInput (KEYEVENTF_UNICODE).
VK_PACKET = 0xE7

#: Teclas virtuales de escritura (letras, números y signos) que se pueden
#: bloquear mientras el teclado braille está activo.
_TYPING_VKS = frozenset(
	[*range(0x30, 0x3A), *range(0x41, 0x5B), *range(0xBA, 0xC1), *range(0xDB, 0xE0), 0xE2],
)


def fixSpanishMarks(text: str, atWordStart: bool) -> str:
	"""«¿» y «¡» al principio de la palabra; «?» y «!» en el resto.

	En braille español la interrogación (puntos 2 6) y la exclamación (puntos
	2 3 5) son la misma celda al abrir y al cerrar: se distinguen por su
	posición, como al leer en papel.
	"""
	if not text:
		return text
	chars = list(text)
	for i, ch in enumerate(chars):
		if i == 0 and atWordStart:
			chars[i] = _OPENING.get(ch, ch)
		else:
			chars[i] = _CLOSING.get(ch, ch)
	return "".join(chars)


def _isLockScreenActive() -> bool:
	"""¿Está la pantalla de bloqueo de Windows? (hilo principal: hace consultas al sistema)."""
	try:
		from winAPI.sessionTracking import isLockScreenModeActive

		return bool(isLockScreenModeActive())
	except Exception:
		return False


def _isEditable(obj: Any) -> bool:
	"""¿Es un sitio donde se escribe? (hilo principal)."""
	if obj is None:
		return False
	try:
		states = obj.states
		role = obj.role
	except Exception:
		return False
	if controlTypes.State.EDITABLE in states:
		return True
	if role in (controlTypes.Role.EDITABLETEXT, controlTypes.Role.TERMINAL, controlTypes.Role.PASSWORDEDIT):
		return True
	try:
		from NVDAObjects.behaviors import EditableText

		if isinstance(obj, EditableText) and controlTypes.State.READONLY not in states:
			return True
	except ImportError:
		pass
	return False


class BrailleKeyboard:
	"""El teclado braille Perkins sobre el teclado del PC."""

	def __init__(self) -> None:
		self.enabled = False
		#: Pausa temporal (por ejemplo, mientras se captura una tecla en las opciones).
		self.suspended = False
		self.machine = PerkinsMachine()
		self._registered = False
		self._scanMap: dict[int, str] = {}
		#: Teclas de puntos pulsadas ahora y papeles de la combinación en curso.
		self._down: set[int] = set()
		self._chord: set[str] = set()
		#: Teclas capturadas al pulsarlas cuya soltura también hay que capturar.
		self._swallowRelease: set[int] = set()
		#: Modo de una mano: puntos acumulados de la celda en curso.
		self._pendingDots = 0
		#: Estado del foco que anota el hilo principal.
		self._focusEditable = False
		self._focusSleep = False
		#: Pantalla de bloqueo de Windows: ahí NVDA no ejecuta órdenes y no se captura nada.
		self._lockScreen = False
		self._treeInterceptorRef: weakref.ReferenceType[Any] | None = None
		#: Tabla que se ha puesto en la entrada braille de NVDA (o ``None``).
		self._appliedTable: str | None = None
		self._originalSendChars: Any = None
		self._lastFieldBeep = 0.0
		self.reloadSettings()

	# ================================================================ opciones
	def reloadSettings(self) -> None:
		"""Vuelve a leer las opciones (al guardarlas o al cambiar de perfil)."""
		layout = distribuciones.getLayout(ajustes.get("layout") or "perkins", ajustes.customKeys())
		dots = 8 if int(ajustes.get("dots") or 6) == 8 else 6
		# La asignación es atómica: el hilo del gancho ve el mapa viejo o el nuevo.
		self._scanMap = distribuciones.buildScanMap(
			layout, dots, bool(ajustes.get("enterAndBackspaceAsPerkins"))
		)
		self.machine.player.clearCache()
		if self.enabled:
			self._applyTable()
		if not ajustes.get("oneHand"):
			self._pendingDots = 0

	# ================================================================ activar
	def setEnabled(self, on: bool) -> None:
		if on == self.enabled:
			return
		self._resetChord()
		self._pendingDots = 0
		if on:
			self.reloadSettings()
			self.enabled = True
			self._register()
			self._installSendCharsHook()
			self._applyTable()
			self.machine.paperIn()
		else:
			self.enabled = False
			self._unregister()
			self._restoreTable()
			self._removeSendCharsHook()
			self.machine.paperOut()

	def toggle(self) -> None:
		self.setEnabled(not self.enabled)
		if self.enabled:
			if ajustes.get("scope") == ajustes.SCOPE_EDITABLE and not self.activeHere():
				# Translators: reported when the braille keyboard is turned on outside a text field
				ui.message(_("Teclado braille activado; se usará al escribir en un campo de texto"))
			else:
				# Translators: reported when the braille keyboard is turned on
				ui.message(_("Teclado braille activado"))
		else:
			# Translators: reported when the braille keyboard is turned off
			ui.message(_("Teclado braille desactivado"))

	def terminate(self) -> None:
		self.setEnabled(False)
		self._unregister()
		self.machine.player.stop()

	def _register(self) -> None:
		if not self._registered:
			inputCore.decide_handleRawKey.register(self._onRawKey)
			self._registered = True

	def _unregister(self) -> None:
		if self._registered:
			inputCore.decide_handleRawKey.unregister(self._onRawKey)
			self._registered = False

	def _resetChord(self) -> None:
		self._down.clear()
		self._chord.clear()
		self._swallowRelease.clear()

	# ================================================================ tabla
	def _applyTable(self) -> None:
		"""Pone la tabla del teclado braille en la entrada braille de NVDA.

		No se cambia la configuración de NVDA: al desactivar el teclado vuelve
		la tabla de entrada que haya elegido la persona usuaria.
		"""
		handler = compat.getInputHandler()
		if handler is None:
			return
		name = ajustes.resolvedTableFileName()
		if name is None:
			self._restoreTable()
			return
		try:
			if handler._table.fileName != name:
				handler.flushBuffer()
				handler._table = brailleTables.getTable(name)
			self._appliedTable = name
		except Exception:
			log.error("Hexapunto: no se pudo poner la tabla %s", name, exc_info=True)

	def _restoreTable(self) -> None:
		if self._appliedTable is None:
			return
		self._appliedTable = None
		handler = compat.getInputHandler()
		if handler is None:
			return
		try:
			handler.flushBuffer()
			# Vuelve a leer la tabla de la configuración (la cambia si es distinta).
			handler.handlePostConfigProfileSwitch()
		except Exception:
			log.error("Hexapunto: no se pudo restaurar la tabla de entrada", exc_info=True)

	def tableFileName(self) -> str:
		"""Tabla con la que se escribe ahora."""
		name = ajustes.resolvedTableFileName()
		if name:
			return name
		handler = compat.getInputHandler()
		try:
			return handler._table.fileName
		except Exception:
			return "en-ueb-g1.ctb"

	def tableDisplayName(self) -> str:
		name = self.tableFileName()
		try:
			return brailleTables.getTable(name).displayName
		except LookupError:
			return name

	# ================================================================ signos españoles
	def _installSendCharsHook(self) -> None:
		"""Corrige «¿» y «¡» en el texto que envía la entrada braille de NVDA."""
		handler = compat.getInputHandler()
		if handler is None or self._originalSendChars is not None:
			return
		original = handler.sendChars
		keyboard = self

		def sendChars(chars: str) -> None:
			try:
				if keyboard.enabled and keyboard._spanishMarksActive():
					atStart = handler.bufferText == chars
					chars = fixSpanishMarks(chars, atStart)
			except Exception:
				log.debugWarning("Hexapunto: error corrigiendo signos", exc_info=True)
			original(chars)

		handler.sendChars = sendChars
		self._originalSendChars = (handler, original)

	def _removeSendCharsHook(self) -> None:
		if self._originalSendChars is None:
			return
		handler, _original = self._originalSendChars
		self._originalSendChars = None
		try:
			del handler.sendChars
		except AttributeError:
			pass

	def _spanishMarksActive(self) -> bool:
		return bool(ajustes.get("spanishMarks")) and self.tableFileName().lower() in _SPANISH_LITERARY_TABLES

	# ================================================================ foco
	def onFocus(self, obj: Any) -> None:
		"""Hilo principal: anota si el foco nuevo es un sitio donde se escribe."""
		wasActive = self.enabled and self.activeHere()
		self._focusEditable = _isEditable(obj)
		try:
			self._focusSleep = bool(obj.sleepMode)
		except Exception:
			self._focusSleep = False
		self._lockScreen = _isLockScreenActive()
		try:
			ti = obj.treeInterceptor
			self._treeInterceptorRef = weakref.ref(ti) if ti is not None else None
		except Exception:
			self._treeInterceptorRef = None
		self._pendingDots = 0
		self.machine.reset()
		if (
			self.enabled
			and not wasActive
			and self.activeHere()
			and ajustes.get("announceActivationInField")
			and time.monotonic() - self._lastFieldBeep > 0.5
		):
			self._lastFieldBeep = time.monotonic()
			tones.beep(1318, 30)

	def activeHere(self) -> bool:
		"""¿Actúa ahora el teclado braille? Se llama en el hilo del gancho: solo lee datos."""
		if self._focusSleep or self._lockScreen:
			return False
		if ajustes.get("scope") == ajustes.SCOPE_ALWAYS:
			return True
		if not self._focusEditable:
			return False
		ti = self._treeInterceptorRef() if self._treeInterceptorRef is not None else None
		# En el modo exploración de una página las letras son de navegación rápida.
		return ti is None or bool(getattr(ti, "_passThrough", True))

	# ================================================================ gancho (hilo del gancho)
	def _onRawKey(
		self,
		vkCode: int = 0,
		scanCode: int = 0,
		extended: bool = False,
		pressed: bool = True,
		injected: bool = False,
		**kwargs: Any,
	) -> bool:
		"""``True`` deja pasar la tecla; ``False`` la captura."""
		try:
			return self._handleRawKey(vkCode, scanCode, extended, pressed, injected)
		except Exception:
			log.error("Hexapunto: error en el gancho del teclado", exc_info=True)
			self._resetChord()
			return True

	@staticmethod
	def _modifiersHeld() -> bool:
		return bool(keyboardHandler.currentModifiers)

	@staticmethod
	def _passingKeysThrough() -> bool:
		return getattr(keyboardHandler, "passKeyThroughCount", -1) >= 0

	def _handleRawKey(
		self, vkCode: int, scanCode: int, extended: bool, pressed: bool, injected: bool
	) -> bool:
		if not self.enabled or self.suspended or vkCode == VK_PACKET:
			# VK_PACKET: caracteres que envía la entrada braille de NVDA (su «código
			# de exploración» es el propio carácter, así que nunca son teclas de puntos).
			return True
		if not pressed and not injected and (scanCode in self._down or scanCode in self._swallowRelease):
			# La soltura de una tecla que capturamos al pulsarla: siempre se procesa.
			return self._handleRelease(scanCode, extended)
		if injected or keyboardHandler.ignoreInjected:
			# Teclas que emula NVDA (por ejemplo, el retroceso de «borrar la última
			# celda»). NVDA 2026.1 y 2026.2 no pasan ``injected`` al gancho, pero
			# mientras NVDA emula teclas ``ignoreInjected`` vale ``True``.
			return True
		if not pressed:
			return self._handleRelease(scanCode, extended)
		if scanCode in self._down:
			# Repetición automática de una tecla mantenida.
			return False
		if scanCode in self._swallowRelease:
			# Repetición de una tecla de una sola pulsación (interlineado, retroceso...).
			return False
		role = None if extended else self._scanMap.get(scanCode)
		if role is None:
			return self._handleOtherKey(vkCode, scanCode, extended)
		if not self._down:
			# Empieza una combinación: ¿hay que actuar?
			if self._modifiersHeld() or self._passingKeysThrough() or not self.activeHere():
				return True
		if role in (ROLE_LINE_FEED, ROLE_BACKSPACE):
			if self._down:
				# Dentro de una combinación no hacen nada (y no se escriben).
				self._swallowRelease.add(scanCode)
				return False
			self._swallowRelease.add(scanCode)
			queueHandler.queueFunction(queueHandler.eventQueue, self._executeMachineKey, role)
			return False
		if not self._down:
			# La máquina suena al bajar la primera tecla, no al soltarlas.
			self.machine.keyDown(role == ROLE_SPACE)
		self._down.add(scanCode)
		self._chord.add(role)
		return False

	def _handleRelease(self, scanCode: int, extended: bool) -> bool:
		if scanCode in self._swallowRelease:
			self._swallowRelease.discard(scanCode)
			return False
		if extended or scanCode not in self._down:
			return True
		self._down.discard(scanCode)
		if not self._down and self._chord:
			chord = self._chord
			self._chord = set()
			dots = 0
			for role in chord:
				if role.startswith("dot"):
					dots |= 1 << (int(role[3:]) - 1)
			queueHandler.queueFunction(queueHandler.eventQueue, self._executeChord, dots, ROLE_SPACE in chord)
		return False

	def _handleOtherKey(self, vkCode: int, scanCode: int, extended: bool) -> bool:
		"""Una tecla que no es del teclado braille."""
		if self._down:
			# Pulsada en mitad de una combinación: se deja pasar.
			return True
		if (
			not extended
			and vkCode in _TYPING_VKS
			and ajustes.get("blockOtherKeys")
			and not self._modifiersHeld()
			and not self._passingKeysThrough()
			and self.activeHere()
		):
			self._swallowRelease.add(scanCode)
			queueHandler.queueFunction(queueHandler.eventQueue, tones.beep, 220, 25)
			return False
		return True

	# ================================================================ ejecución (hilo principal)
	def _executeMachineKey(self, role: str) -> None:
		"""Interlineado o retroceso de la máquina."""
		if role == ROLE_BACKSPACE and self._pendingDots:
			# Modo de una mano: descarta la celda a medias.
			self._pendingDots = 0
			self.machine.backspace()
			# Translators: reported in one hand mode when the partial cell is discarded
			speech.speakMessage(_("celda descartada"))
			return
		if role == ROLE_LINE_FEED:
			self.machine.newLine()
			extra = EXTRA_LINE_FEED
		else:
			self.machine.backspace()
			extra = EXTRA_BACKSPACE
		if ajustes.get("practiceMode"):
			speech.speakMessage(describe(0, False, extra))
			return
		self._executeGesture(HexapuntoGesture(extra=extra))

	def _executeChord(self, dots: int, space: bool) -> None:
		"""Una combinación completa (todas las teclas soltadas)."""
		if ajustes.get("oneHand") and not space and dots:
			# Modo de una mano: los puntos se suman hasta pulsar el espaciador.
			self._pendingDots |= dots
			speech.speakMessage(describe(self._pendingDots, False))
			return
		if ajustes.get("oneHand") and space and not dots and self._pendingDots:
			dots, space = self._pendingDots, False
			self._pendingDots = 0
		if ajustes.get("practiceMode") and not (space and dots):
			self._practice(dots, space)
			return
		if bool(dots) != bool(space) and not inputCore.manager.isInputHelpActive:
			# Una celda o un espacio: el carro avanza (y quizá suena la campana).
			self.machine.advance()
		gesture = HexapuntoGesture(dots, space)
		executed = self._executeGesture(gesture)
		if executed and dots and not space and ajustes.get("speakDots"):
			queueHandler.queueFunction(queueHandler.eventQueue, speech.speakMessage, describe(dots, False))

	def _executeGesture(self, gesture: HexapuntoGesture) -> bool:
		"""Ejecuta el gesto con el sistema de entrada de NVDA. ``False`` si no tiene orden."""
		self._applyTable()
		try:
			inputCore.manager.executeGesture(gesture)
			return True
		except inputCore.NoInputGestureAction:
			if gesture.space and gesture.dots:
				self._reportUnassigned(gesture)
			return False
		except Exception:
			log.error("Hexapunto: error ejecutando %s", gesture.identifiers, exc_info=True)
			return False

	def _reportUnassigned(self, gesture: HexapuntoGesture) -> None:
		feedback = ajustes.get("unassignedFeedback")
		if feedback == ajustes.UNASSIGNED_BEEP:
			tones.beep(330, 60)
		elif feedback == ajustes.UNASSIGNED_SPEECH:
			# Translators: reported when a space + dots chord has no command; {chord} describes it
			speech.speakMessage(_("{chord}: sin orden asignada").format(chord=gesture.displayName))

	def _practice(self, dots: int, space: bool) -> None:
		"""Modo de práctica: dice qué se escribiría, sin escribir nada."""
		if space and not dots:
			self.machine.advance()
			speech.speakMessage(describe(0, True))
			return
		self.machine.advance()
		text = compat.backTranslate(self.tableFileName(), [dots]).strip()
		numbers = describe(dots, False)
		if text:
			speech.speakMessage(f"{text}, {numbers}")
		else:
			# Translators: practice mode, the cell does not produce text by itself (e.g. capital sign)
			speech.speakMessage(_("{dots}, sin carácter por sí sola").format(dots=numbers))

	# ================================================================ estado
	def statusText(self) -> str:
		layout = distribuciones.getLayout(ajustes.get("layout") or "perkins", ajustes.customKeys())
		parts = [
			# Translators: part of the status report
			_("Teclado braille activado") if self.enabled else _("Teclado braille desactivado"),
		]
		if self.enabled and not self.activeHere():
			# Translators: part of the status report
			parts.append(_("en espera: no estás en un campo de texto"))
		# Translators: part of the status report; {n} is 6 or 8
		parts.append(_("{n} puntos").format(n=8 if int(ajustes.get("dots") or 6) == 8 else 6))
		parts.append(layout.name)
		# Translators: part of the status report; {table} is a braille table name
		parts.append(_("tabla {table}").format(table=self.tableDisplayName()))
		if ajustes.get("oneHand"):
			# Translators: part of the status report
			parts.append(_("modo de una mano"))
		if ajustes.get("practiceMode"):
			# Translators: part of the status report
			parts.append(_("modo de práctica"))
		# Translators: part of the status report; carriage position
		parts.append(
			_("columna {col} de {total}").format(
				col=self.machine.column + 1, total=self.machine.lineLength()
			),
		)
		return ", ".join(parts)
