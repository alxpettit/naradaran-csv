build:
	pyinstaller --onefile src/main.py

genTestDir:
	./gen-test-dir.sh

clean:
	rm -rfv dist/ build/ test/ *.spec
