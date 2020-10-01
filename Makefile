build:
	pyinstaller --onefile src/main.py

genTestDir:
	./gen-test-dir.sh
