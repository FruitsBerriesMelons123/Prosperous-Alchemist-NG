#pragma once

#include <cstdint>

namespace alchemist::ui {
	void NotifyNewGame();
	void NotifyGameLoadStarted();
	void NotifyGameLoadFinished();
	void SetVisible(bool a_visible);
	void SetGameWindowFocused(bool a_focused);
	void SetCursorPosition(float a_x, float a_y);
	void SetLeftMouseButtonDown(bool a_down);
	bool IsLeftMouseButtonDown();
	void AddMouseWheel(float a_delta);
	void AddInputCharacter(std::uint32_t a_codePoint);
	void AddInputKey(std::uint32_t a_keyCode, bool a_pressed);
	void UpdateImGuiMouseInput();
	void ProcessKeyboardInput();
	void ResetInputState();
	bool IsSearchInputFocused();
	void ClearSearchFocus();
	bool IsVisible();
	bool IsCursorOverWindow();
	void DrawCursor();
	void DrawWindow();
}
