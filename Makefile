ui: src/main/python/buffbot/ui/generated/main_window.py

src/main/python/buffbot/ui/generated/main_window.py: gui/MainWindow.ui
	pyuic5 gui/MainWindow.ui -o src/main/python/buffbot/ui/generated/main_window.py


.PHONY: ui
