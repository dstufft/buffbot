UI_FILES := $(wildcard src/main/python/buffbot/ui/generated/*.py)

ui: $(UI_FILES)

src/main/python/buffbot/ui/generated/add_spell.py: gui/AddSpell.ui
	pyuic5 gui/AddSpell.ui -o src/main/python/buffbot/ui/generated/add_spell.py

src/main/python/buffbot/ui/generated/main_window.py: gui/MainWindow.ui
	pyuic5 gui/MainWindow.ui -o src/main/python/buffbot/ui/generated/main_window.py


.PHONY: ui
