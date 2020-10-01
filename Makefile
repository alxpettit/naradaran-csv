build:
	pyinstaller --onefile src/main.py --noupx

genTestDir:
	./gen-test-dir.sh

clean:
	rm -rfv dist/ build/ test/ *.spec
