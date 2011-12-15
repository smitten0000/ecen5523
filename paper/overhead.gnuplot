set terminal epslatex monochrome "" 8 size 3.5in,2.5in
set output "overhead.tex"
set style data histogram
set style histogram gap 1
set style fill solid border -1
set xlabel "Time"
set ylabel "Execution Time (seconds)" offset 1
#set boxwidth 0.85
#set tmargin 5
#set lmargin 7
set key tmargin
plot 'overhead.dat' \
        using 2:xticlabel(1) title columnheader(2) fs solid 0.25, \
     '' using 3:xticlabel(1) title columnheader(3) fs solid 0.50

