.PHONY: all test clean

all:
	python src/wealth_distribution.py

test:
	python -m unittest discover -s tests -v

clean:
	rm -f outputs/*.csv outputs/*.png outputs/*.svg
