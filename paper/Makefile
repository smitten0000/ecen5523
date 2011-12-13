# Brent Smith
# 
# Makefile for the paper

PAPER = paper.tex
#FIGURES = slot_runtime.pdf
FIGURES =

SUFFIXES = .pdf .eps .gnuplot

default: paper

clean: figures-clean paper-clean

paper: figures
	pdflatex $(PAPER)
	bibtex $(PAPER:.tex=)
	pdflatex $(PAPER)
	pdflatex $(PAPER)

paper-clean: figures-clean
	rm -f $(PAPER:.tex=.pdf) $(PAPER:.tex=.bbl) \
          $(PAPER:.tex=.blg) $(PAPER:.tex=.log) \
          $(PAPER:.tex=.aux) $(PAPER:.tex=.out) \
          texput.log

figures: $(FIGURES)

figures-clean:
	rm -f $(FIGURES) $(FIGURES:.pdf=.eps) $(FIGURES:.pdf=.tex)

%.eps: %.gnuplot
	gnuplot $<

%.pdf: %.eps
	epstopdf $<
