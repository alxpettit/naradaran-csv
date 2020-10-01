build:
	pyinstaller --onefile src/main.py --noupx

genTestDir:
	./gen-test-dir.sh

clean:
	rm -rfv dist/ build/ test/ *.spec

windowsPublish:
	rm Y:/main -v
	cp dist/main.exe Y:/main -v
