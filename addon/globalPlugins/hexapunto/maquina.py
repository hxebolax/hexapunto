# Hexapunto: teclado braille Perkins para NVDA.
# Copyright (C) 2026 hxebolax
# Este archivo está cubierto por la Licencia Pública General de GNU, versión 2 o posterior.
# Consulta el archivo COPYING.txt para más detalles.

"""La máquina Perkins emulada: sonidos y posición del carro.

Sonidos (carpeta ``sounds`` del complemento):

- ``teclaN.wav``: golpe de las teclas de los puntos (se elige uno al azar);
- ``espacioN.wav``: el espaciador;
- ``retroceso.wav``: la tecla de retroceso;
- ``linea.wav``: la tecla de interlineado (y meter el papel);
- ``campana.wav``: la campana que avisa del final de la línea;
- ``papel.wav``: sacar el papel (al desactivar el teclado).

Quien quiera otros sonidos puede poner los suyos, con esos mismos nombres, en
la carpeta ``hexapunto\\sonidos`` de la configuración de NVDA: tienen
preferencia y no se pierden al actualizar el complemento.

Los sonidos se reproducen en un hilo propio: el hilo del gancho del teclado
nunca espera por ellos.
"""

from __future__ import annotations

import hashlib
import os
import queue
import random
import tempfile
import threading
import wave
from array import array

import globalVars
import nvwave
import tones
from logHandler import log

from . import ajustes

#: Nombres de los sonidos de la máquina.
KEY = "tecla"
SPACE = "espacio"
BACKSPACE = "retroceso"
LINE = "linea"
BELL = "campana"
PAPER_OUT = "papel"
#: Tope del margen (no es un sonido grabado: siempre es un pitido grave).
MARGIN = "tope"
SOUND_NAMES = (KEY, SPACE, BACKSPACE, LINE, BELL, PAPER_OUT)

#: Pitidos del juego de sonidos «suave»: frecuencia (Hz) y duración (ms).
_SOFT_TONES: dict[str, tuple[int, int]] = {
	KEY: (1760, 6),
	SPACE: (1100, 8),
	BACKSPACE: (520, 25),
	LINE: (660, 45),
	BELL: (2093, 140),
	PAPER_OUT: (330, 90),
	MARGIN: (196, 70),
}

ADDON_SOUNDS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sounds"))


def userSoundsDir() -> str:
	"""Carpeta de sonidos propios de la persona usuaria."""
	return os.path.join(globalVars.appArgs.configPath, "hexapunto", "sonidos")


def _cacheDir() -> str:
	return os.path.join(tempfile.gettempdir(), "nvda-hexapunto")


def soundFiles(name: str) -> list[str]:
	"""Archivos de un sonido: los de la carpeta propia si hay alguno; si no, los del complemento.

	Un sonido puede tener variantes (``tecla1.wav``, ``tecla2.wav``...).
	"""
	for folder in (userSoundsDir(), ADDON_SOUNDS_DIR):
		try:
			names = os.listdir(folder)
		except OSError:
			continue
		found = sorted(
			os.path.join(folder, n)
			for n in names
			if n.lower().endswith(".wav")
			and (n.lower() == f"{name}.wav" or (n.lower().startswith(name) and n[len(name) : -4].isdigit()))
		)
		if found:
			return found
	return []


def scaledCopy(path: str, volume: int) -> str:
	"""Copia del sonido con el volumen indicado (0-100), guardada en una caché temporal.

	Solo se escalan los WAV PCM de 16 bits; los demás se reproducen tal cual.
	"""
	if volume >= 100:
		return path
	try:
		stamp = f"{os.path.abspath(path)}|{os.path.getmtime(path)}|{volume}"
		digest = hashlib.sha1(stamp.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]
		out = os.path.join(_cacheDir(), f"{digest}.wav")
		if os.path.isfile(out):
			return out
		with wave.open(path, "rb") as src:
			params = src.getparams()
			frames = src.readframes(src.getnframes())
		if params.sampwidth != 2:
			return path
		samples = array("h")
		samples.frombytes(frames)
		factor = max(0, volume) / 100.0
		scaled = array("h", (int(s * factor) for s in samples))
		os.makedirs(_cacheDir(), exist_ok=True)
		tmp = out + ".tmp"
		with wave.open(tmp, "wb") as dst:
			dst.setparams(params)
			dst.writeframes(scaled.tobytes())
		os.replace(tmp, out)
		return out
	except Exception:
		log.debugWarning("Hexapunto: no se pudo ajustar el volumen de %s", path, exc_info=True)
		return path


class SoundPlayer:
	"""Reproduce los sonidos en un hilo propio."""

	def __init__(self) -> None:
		self._queue: queue.SimpleQueue[str | None] = queue.SimpleQueue()
		self._thread: threading.Thread | None = None
		self._lock = threading.Lock()
		self._files: dict[str, list[str]] = {}

	def clearCache(self) -> None:
		"""Olvida los archivos encontrados (tras cambiar de sonidos o de volumen)."""
		self._files = {}

	def play(self, name: str) -> None:
		theme = ajustes.get("sounds")
		if theme == ajustes.SOUNDS_NONE and name != MARGIN:
			return
		with self._lock:
			if self._thread is None or not self._thread.is_alive():
				self._thread = threading.Thread(target=self._run, name="Hexapunto: sonidos", daemon=True)
				self._thread.start()
		self._queue.put(name)

	def stop(self) -> None:
		self._queue.put(None)

	def _run(self) -> None:
		while True:
			name = self._queue.get()
			if name is None:
				return
			try:
				self._playNow(name)
			except Exception:
				log.debugWarning("Hexapunto: no se pudo reproducir el sonido %s", name, exc_info=True)

	def _playNow(self, name: str) -> None:
		volume = int(ajustes.get("volume") or 0)
		if volume <= 0:
			return
		theme = ajustes.get("sounds")
		if theme == ajustes.SOUNDS_SOFT or name == MARGIN:
			hz, ms = _SOFT_TONES[name]
			level = max(1, round(50 * volume / 100))
			tones.beep(hz, ms, left=level, right=level)
			return
		if theme != ajustes.SOUNDS_PERKINS:
			return
		files = self._files.get(name)
		if files is None:
			files = self._files[name] = soundFiles(name)
		if not files:
			return
		nvwave.playWaveFile(scaledCopy(random.choice(files), volume), asynchronous=True)


class PerkinsMachine:
	"""Sonidos y posición del carro de la máquina emulada."""

	def __init__(self, player: SoundPlayer | None = None) -> None:
		self.column = 0
		self.player = player or SoundPlayer()

	def _play(self, name: str) -> None:
		self.player.play(name)

	# ---------------------------------------------------------- opciones
	@staticmethod
	def lineLength() -> int:
		return max(10, int(ajustes.get("lineLength") or 40))

	@staticmethod
	def bellColumn() -> int:
		"""Columna en la que suena la campana."""
		length = PerkinsMachine.lineLength()
		return max(1, length - int(ajustes.get("bellCells") or 6))

	# ---------------------------------------------------------- acciones
	def reset(self) -> None:
		"""Papel nuevo (al activar el teclado o al cambiar de campo)."""
		self.column = 0

	def keyDown(self, space: bool) -> None:
		"""Primera tecla de una combinación (hilo del gancho): el golpe de la máquina."""
		self._play(SPACE if space else KEY)

	def advance(self) -> None:
		"""Una celda o un espacio escritos: el carro avanza; la campana avisa cerca del final."""
		self.column += 1
		if ajustes.get("bell") and self.column == self.bellColumn():
			self._play(BELL)
		elif ajustes.get("marginStop") and self.column > self.lineLength():
			self._play(MARGIN)

	def newLine(self) -> None:
		"""Tecla de interlineado: el carro vuelve al principio."""
		self.column = 0
		self._play(LINE)

	def backspace(self) -> None:
		if self.column > 0:
			self.column -= 1
		self._play(BACKSPACE)

	def paperIn(self) -> None:
		self.column = 0
		if ajustes.get("paperSounds"):
			self._play(LINE)

	def paperOut(self) -> None:
		if ajustes.get("paperSounds"):
			self._play(PAPER_OUT)
