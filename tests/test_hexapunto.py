# Hexapunto: pruebas automáticas.
# Copyright (C) 2026 Héctor J. Benítez Corredera
# Este archivo está cubierto por la Licencia Pública General de GNU, versión 2 o posterior.

"""Pruebas del motor, las distribuciones, los gestos y las órdenes de Hexapunto."""

from __future__ import annotations

from typing import Any

import pytest

import hexapunto
from hexapunto import ajustes, comandos, distribuciones, gesto, motor
from hexapunto.distribuciones import SC, SCAN_BACKSPACE, SCAN_ENTER

F, D, S, J, K, L, A, N = SC["F"], SC["D"], SC["S"], SC["J"], SC["K"], SC["L"], SC["A"], SC["Ñ"]
SPACE = SC["SPACE"]
VK_LETTER = 0x46  # cualquier tecla virtual de letra


# ====================================================================== utilidades
def press(kb: motor.BrailleKeyboard, *scans: int, injected: bool = False, vk: int = VK_LETTER) -> list[bool]:
	"""Pulsa las teclas en orden y las suelta en orden inverso. Devuelve lo que decide el gancho."""
	results = [
		kb._onRawKey(vkCode=vk, scanCode=s, extended=False, pressed=True, injected=injected) for s in scans
	]
	results += [
		kb._onRawKey(vkCode=vk, scanCode=s, extended=False, pressed=False, injected=injected)
		for s in reversed(scans)
	]
	return results


@pytest.fixture
def kb(env: Any) -> motor.BrailleKeyboard:
	ajustes.setValue("sounds", ajustes.SOUNDS_NONE)
	keyboard = motor.BrailleKeyboard()
	keyboard.onFocus(env.FakeObj())
	keyboard.setEnabled(True)
	yield keyboard
	keyboard.terminate()


def lastGesture(env: Any) -> Any:
	assert env.manager.executed, "no se ejecutó ningún gesto"
	return env.manager.executed[-1]


# ====================================================================== distribuciones
def test_perkins_six_dots_uses_a_and_n_as_machine_keys() -> None:
	layout = distribuciones.getLayout("perkins")
	scanMap = distribuciones.buildScanMap(layout, 6, True)
	assert scanMap[F] == "dot1" and scanMap[D] == "dot2" and scanMap[S] == "dot3"
	assert scanMap[J] == "dot4" and scanMap[K] == "dot5" and scanMap[L] == "dot6"
	assert scanMap[A] == "lineFeed" and scanMap[N] == "backspace"
	assert scanMap[SCAN_ENTER] == "lineFeed" and scanMap[SCAN_BACKSPACE] == "backspace"
	assert "dot7" not in scanMap.values()


def test_perkins_eight_dots_uses_a_and_n_as_dots_7_and_8() -> None:
	scanMap = distribuciones.buildScanMap(distribuciones.getLayout("perkins"), 8, False)
	assert scanMap[A] == "dot7" and scanMap[N] == "dot8"
	assert SCAN_ENTER not in scanMap


def test_slate_layout_is_mirrored() -> None:
	scanMap = distribuciones.buildScanMap(distribuciones.getLayout("slate"), 6, True)
	assert scanMap[J] == "dot1" and scanMap[F] == "dot4"


def test_builtin_layouts_have_no_conflicts() -> None:
	for layout in distribuciones.builtinLayouts():
		for dots in (6, 8):
			assert distribuciones.findConflicts(layout.keys, dots) == [], layout.id


def test_conflicts_detected_in_custom_layout() -> None:
	keys = dict(distribuciones.getLayout("perkins").keys)
	keys["dot2"] = keys["dot1"]
	assert ("dot1", "dot2") in distribuciones.findConflicts(keys, 6)


def test_unknown_layout_falls_back_to_perkins() -> None:
	assert distribuciones.getLayout("noExiste").id == "perkins"


def test_custom_layout_completes_missing_roles() -> None:
	layout = distribuciones.getLayout(distribuciones.CUSTOM_ID, {"dot1": SC["Q"]})
	assert layout.keys["dot1"] == SC["Q"] and layout.keys["dot2"] == D


# ====================================================================== signos españoles
@pytest.mark.parametrize(
	("text", "atStart", "expected"),
	[
		("?", True, "¿"),
		("?", False, "?"),
		("¿", False, "?"),
		("!", True, "¡"),
		("¡qué?", True, "¡qué?"),
		("?hola!", True, "¿hola!"),
		("", True, ""),
	],
)
def test_fix_spanish_marks(text: str, atStart: bool, expected: str) -> None:
	assert motor.fixSpanishMarks(text, atStart) == expected


# ====================================================================== gestos
def test_gesture_identifiers_for_cell(env: Any) -> None:
	g = gesto.HexapuntoGesture(0b10011, False)
	assert g.identifiers[0] == "hexapunto:dot1+dot2+dot5"
	assert "bk:dots" in g.identifiers


def test_gesture_identifiers_for_space_chord(env: Any) -> None:
	g = gesto.HexapuntoGesture(0b1, True)
	assert g.identifiers[0] == "hexapunto:dot1+space"
	assert "bk:dots+space" in g.identifiers


def test_gesture_line_feed_is_dot8(env: Any) -> None:
	g = gesto.HexapuntoGesture(extra=gesto.EXTRA_LINE_FEED)
	assert g.dots == 1 << 7 and not g.space
	assert g.identifiers[0] == "hexapunto:linefeed"
	assert "bk:dot8" in g.identifiers


def test_gesture_backspace_is_dot7(env: Any) -> None:
	g = gesto.HexapuntoGesture(extra=gesto.EXTRA_BACKSPACE)
	assert g.dots == 1 << 6
	assert "bk:dot7" in g.identifiers


def test_display_text_for_identifier() -> None:
	source, text = gesto.HexapuntoGesture.getDisplayTextForIdentifier("hexapunto:dot1+dot2+space")
	assert text == "espacio con puntos 1 2"
	assert gesto.HexapuntoGesture.getDisplayTextForIdentifier("hexapunto:linefeed")[1] == "interlineado"


def test_describe() -> None:
	assert gesto.describe(0b1, False) == "punto 1"
	assert gesto.describe(0b101, False) == "puntos 1 3"
	assert gesto.describe(0, True) == "espacio"


# ====================================================================== motor
def test_chord_is_executed_on_release(env: Any, kb: motor.BrailleKeyboard) -> None:
	results = press(kb, F, D)
	assert results == [False, False, False, False], "las teclas de puntos se capturan"
	g = lastGesture(env)
	assert g.dots == 0b11 and not g.space
	assert len(env.manager.executed) == 1


def test_chord_not_sent_until_all_keys_released(env: Any, kb: motor.BrailleKeyboard) -> None:
	kb._onRawKey(vkCode=1, scanCode=F, pressed=True)
	kb._onRawKey(vkCode=1, scanCode=K, pressed=True)
	kb._onRawKey(vkCode=1, scanCode=F, pressed=False)
	assert env.manager.executed == []
	kb._onRawKey(vkCode=1, scanCode=K, pressed=False)
	assert lastGesture(env).dots == 0b10001


def test_auto_repeat_is_swallowed(env: Any, kb: motor.BrailleKeyboard) -> None:
	kb._onRawKey(vkCode=1, scanCode=F, pressed=True)
	assert kb._onRawKey(vkCode=1, scanCode=F, pressed=True) is False
	kb._onRawKey(vkCode=1, scanCode=F, pressed=False)
	assert len(env.manager.executed) == 1


def test_space_alone(env: Any, kb: motor.BrailleKeyboard) -> None:
	press(kb, SPACE)
	g = lastGesture(env)
	assert g.space and g.dots == 0


def test_space_with_dots(env: Any, kb: motor.BrailleKeyboard) -> None:
	press(kb, SPACE, F)
	g = lastGesture(env)
	assert g.space and g.dots == 0b1
	assert g.identifiers[0] == "hexapunto:dot1+space"


def test_unassigned_space_chord_beeps(env: Any, kb: motor.BrailleKeyboard) -> None:
	env.manager.unbound.update({"hexapunto:dot2+dot3+dot6+space", "bk:dot2+dot3+dot6+space", "bk:dots+space"})
	press(kb, SPACE, D, S, L)
	assert env.beeps, "debe sonar el aviso de combinación sin orden"


def test_other_keys_pass_through(env: Any, kb: motor.BrailleKeyboard) -> None:
	assert press(kb, SC["G"]) == [True, True]
	assert env.manager.executed == []


def test_extended_keys_pass_through(env: Any, kb: motor.BrailleKeyboard) -> None:
	assert kb._onRawKey(vkCode=1, scanCode=F, extended=True, pressed=True) is True


def test_modifiers_pass_through(env: Any, kb: motor.BrailleKeyboard) -> None:
	env.keyboardHandler.currentModifiers.add((0x11, False))
	assert press(kb, F) == [True, True]
	assert env.manager.executed == []


def test_injected_keys_pass_through(env: Any, kb: motor.BrailleKeyboard) -> None:
	assert press(kb, F, injected=True) == [True, True]


def test_nvda_emulated_keys_pass_through_on_2026_1(env: Any, kb: motor.BrailleKeyboard) -> None:
	"""NVDA 2026.1 no pasa ``injected``: se usa ``keyboardHandler.ignoreInjected``."""
	env.keyboardHandler.ignoreInjected = True
	assert press(kb, SCAN_BACKSPACE) == [True, True]
	assert env.manager.executed == []


def test_unicode_packets_pass_through(env: Any, kb: motor.BrailleKeyboard) -> None:
	"""Los caracteres que envía NVDA llegan con VK_PACKET y el carácter como código."""
	assert press(kb, 0x21, vk=motor.VK_PACKET) == [True, True]


def test_release_is_processed_even_if_nvda_is_injecting(env: Any, kb: motor.BrailleKeyboard) -> None:
	kb._onRawKey(vkCode=1, scanCode=F, pressed=True)
	env.keyboardHandler.ignoreInjected = True
	assert kb._onRawKey(vkCode=1, scanCode=F, pressed=False) is False
	assert lastGesture(env).dots == 0b1


def test_pass_key_through(env: Any, kb: motor.BrailleKeyboard) -> None:
	env.keyboardHandler.passKeyThroughCount = 0
	assert press(kb, F) == [True, True]


def test_not_active_outside_text_fields(env: Any, kb: motor.BrailleKeyboard) -> None:
	kb.onFocus(env.FakeObj(role=env.Role.BUTTON, states=set()))
	assert press(kb, F) == [True, True]


def test_scope_always(env: Any, kb: motor.BrailleKeyboard) -> None:
	ajustes.setValue("scope", ajustes.SCOPE_ALWAYS)
	kb.onFocus(env.FakeObj(role=env.Role.BUTTON, states=set()))
	assert press(kb, F) == [False, False]


def test_browse_mode_is_not_active(env: Any, kb: motor.BrailleKeyboard) -> None:
	class TI:
		_passThrough = False

	ti = TI()
	kb.onFocus(env.FakeObj(ti=ti))
	assert press(kb, F) == [True, True]
	ti._passThrough = True
	assert press(kb, F) == [False, False]


def test_disabled_keyboard_does_nothing(env: Any, kb: motor.BrailleKeyboard) -> None:
	kb.setEnabled(False)
	assert press(kb, F) == [True, True]


def test_line_feed_and_backspace_keys(env: Any, kb: motor.BrailleKeyboard) -> None:
	assert press(kb, A) == [False, False]
	assert lastGesture(env).extra == gesto.EXTRA_LINE_FEED
	press(kb, N)
	assert lastGesture(env).extra == gesto.EXTRA_BACKSPACE
	press(kb, SCAN_ENTER)
	assert lastGesture(env).extra == gesto.EXTRA_LINE_FEED
	press(kb, SCAN_BACKSPACE)
	assert lastGesture(env).extra == gesto.EXTRA_BACKSPACE


def test_enter_passes_if_option_disabled(env: Any, kb: motor.BrailleKeyboard) -> None:
	ajustes.setValue("enterAndBackspaceAsPerkins", False)
	kb.reloadSettings()
	assert press(kb, SCAN_ENTER) == [True, True]


def test_eight_dots(env: Any, kb: motor.BrailleKeyboard) -> None:
	ajustes.setValue("dots", 8)
	kb.reloadSettings()
	press(kb, A, F)
	assert lastGesture(env).dots == 0b1000001


def test_block_other_keys(env: Any, kb: motor.BrailleKeyboard) -> None:
	ajustes.setValue("blockOtherKeys", True)
	assert press(kb, SC["G"], vk=0x47) == [False, False]
	assert env.beeps
	# Las que no son de escritura (por ejemplo, Tabulador) siguen pasando.
	assert press(kb, 0x0F, vk=0x09) == [True, True]


def test_one_hand_mode(env: Any, kb: motor.BrailleKeyboard) -> None:
	ajustes.setValue("oneHand", True)
	press(kb, F)
	press(kb, J)
	assert env.manager.executed == []
	press(kb, SPACE)
	assert lastGesture(env).dots == 0b1001 and not lastGesture(env).space
	press(kb, SPACE)
	assert lastGesture(env).space


def test_one_hand_backspace_discards_partial_cell(env: Any, kb: motor.BrailleKeyboard) -> None:
	ajustes.setValue("oneHand", True)
	press(kb, F)
	press(kb, N)
	assert env.manager.executed == []
	assert "celda descartada" in env.spoken


def test_practice_mode_speaks_and_does_not_type(env: Any, kb: motor.BrailleKeyboard) -> None:
	ajustes.setValue("practiceMode", True)
	ajustes.setValue("table", "es-g1.ctb")
	press(kb, F, D)
	assert env.manager.executed == []
	assert env.spoken[-1] == "b, puntos 1 2"


def test_practice_mode_still_runs_commands(env: Any, kb: motor.BrailleKeyboard) -> None:
	ajustes.setValue("practiceMode", True)
	press(kb, SPACE, F)
	assert lastGesture(env).space


def test_table_is_applied_and_restored(env: Any, kb: motor.BrailleKeyboard) -> None:
	handler = env.handler
	assert handler._table.fileName == "es-g1.ctb", "tabla automática integral en español"
	kb.setEnabled(False)
	assert handler._table.fileName == "Es-Es-G0.utb", "vuelve la tabla de NVDA"


def test_nvda_table_option_does_not_touch_table(env: Any, kb: motor.BrailleKeyboard) -> None:
	kb.setEnabled(False)
	ajustes.setValue("table", ajustes.TABLE_NVDA)
	kb.setEnabled(True)
	assert env.handler._table.fileName == "Es-Es-G0.utb"


def test_spanish_marks_hook(env: Any, kb: motor.BrailleKeyboard) -> None:
	handler = env.handler
	handler.bufferText = "?"
	handler.sendChars("?")
	handler.bufferText = "hola?"
	handler.sendChars("?")
	assert handler.sent == ["¿", "?"]
	kb.setEnabled(False)
	assert "sendChars" not in vars(handler), "al desactivar se quita el gancho"


def test_speak_dots_option(env: Any, kb: motor.BrailleKeyboard) -> None:
	ajustes.setValue("speakDots", True)
	press(kb, F, D, J)
	assert env.spoken[-1] == "puntos 1 2 4"


def test_suspended_keyboard_lets_keys_through(env: Any, kb: motor.BrailleKeyboard) -> None:
	kb.suspended = True
	assert press(kb, F) == [True, True]


def test_bell_rings_near_end_of_line(env: Any, kb: motor.BrailleKeyboard) -> None:
	played: list[str] = []
	kb.machine.player.play = played.append  # type: ignore[method-assign]
	ajustes.setValue("lineLength", 10)
	ajustes.setValue("bellCells", 2)
	for _ in range(8):
		press(kb, F)
	assert "campana" in played
	press(kb, A)
	assert kb.machine.column == 0


def test_status_text(env: Any, kb: motor.BrailleKeyboard) -> None:
	text = kb.statusText()
	assert "Teclado braille activado" in text and "6 puntos" in text and "Español grado 1" in text


def test_hook_errors_never_block_the_keyboard(env: Any, kb: motor.BrailleKeyboard) -> None:
	kb._scanMap = None  # type: ignore[assignment]
	assert kb._onRawKey(vkCode=1, scanCode=F, pressed=True) is True
	assert env.log.errors


def test_register_and_unregister_hook(env: Any) -> None:
	import inputCore

	keyboard = motor.BrailleKeyboard()
	keyboard.setEnabled(True)
	assert keyboard._onRawKey in inputCore.decide_handleRawKey.handlers
	keyboard.terminate()
	assert keyboard._onRawKey not in inputCore.decide_handleRawKey.handlers


# ====================================================================== órdenes y complemento
def test_default_chords_are_unique() -> None:
	gestures: list[str] = []
	for _key, _desc, g in comandos.EMULATED_KEYS:
		if g:
			gestures.append(g)
	for gs in comandos.DEFAULT_GESTURES.values():
		gestures.extend(gs)
	assert len(gestures) == len(set(gestures)), "hay combinaciones repetidas"


def test_emulation_script_translates_pending_braille_first(env: Any) -> None:
	env.handler.bufferBraille = [1, 2]
	comandos.emulateKey("upArrow")
	assert env.handler.bufferBraille == []
	assert env.manager.emulated[-1].name == "upArrow"


def test_emulation_uses_virtual_modifiers(env: Any) -> None:
	env.handler.currentModifiers = {"control"}
	comandos.emulateKey("home")
	assert env.handler.sent[-1] == "<control+home>"
	assert not env.handler.currentModifiers


def test_global_plugin_binds_gestures(env: Any) -> None:
	plugin = hexapunto.GlobalPlugin()
	try:
		assert plugin._gestureMap["kb:alt+b+nvda"] == "toggle"
		assert plugin._gestureMap["hexapunto:dot1+space"] == "emulate_upArrow"
		assert plugin._gestureMap["hexapunto:dot1+dot2+dot3+dot4+dot5+dot6+space"] == "sayAll"
		assert callable(plugin.script_virtualModifier_control)
	finally:
		plugin.terminate()


def test_global_plugin_scripts(env: Any) -> None:
	plugin = hexapunto.GlobalPlugin()
	try:
		plugin.script_toggle(None)
		assert plugin.keyboard.enabled
		plugin.script_cycleSounds(None)
		plugin.script_toggleDots(None)
		assert ajustes.get("dots") == 8
		plugin.script_cycleLayout(None)
		assert ajustes.get("layout") == "slate"
		plugin.script_status(None)
		plugin.script_toggle(None)
		assert not plugin.keyboard.enabled
	finally:
		plugin.terminate()


def test_eight_dots_auto_table_is_nvda_table(env: Any, kb: motor.BrailleKeyboard) -> None:
	ajustes.setValue("dots", 8)
	kb.reloadSettings()
	assert ajustes.resolvedTableFileName() is None
	assert env.handler._table.fileName == "Es-Es-G0.utb"


def test_spanish_marks_only_with_literary_tables(env: Any, kb: motor.BrailleKeyboard) -> None:
	ajustes.setValue("table", "Es-Es-G0.utb")
	handler = env.handler
	handler.bufferText = "?"
	handler.sendChars("?")
	assert handler.sent == ["?"]


def test_key_held_while_disabling_is_not_swallowed_later(env: Any, kb: motor.BrailleKeyboard) -> None:
	kb._onRawKey(vkCode=1, scanCode=A, pressed=True)  # interlineado: se captura hasta soltarlo
	kb.setEnabled(False)
	kb._onRawKey(vkCode=1, scanCode=A, pressed=False)
	kb.setEnabled(True)
	assert press(kb, A) == [False, False]
	assert lastGesture(env).extra == gesto.EXTRA_LINE_FEED


def test_lock_screen_is_not_active(env: Any, kb: motor.BrailleKeyboard, monkeypatch: Any) -> None:
	monkeypatch.setattr(motor, "_isLockScreenActive", lambda: True)
	kb.onFocus(env.FakeObj())
	assert press(kb, F) == [True, True]


def test_input_help_does_not_move_carriage(env: Any, kb: motor.BrailleKeyboard) -> None:
	env.manager.isInputHelpActive = True
	try:
		press(kb, F)
		assert kb.machine.column == 0
	finally:
		env.manager.isInputHelpActive = False
