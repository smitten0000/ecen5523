set terminal epslatex monochrome "" 8 size 3.5in,2.5in
set output "slot_runtime.tex"
set style data histogram
set style histogram gap 1
set style fill solid border -1
#set title "Comparison of Total Execution time per Benchmark"
set xlabel "Benchmark"
set ylabel "Execution Time (seconds)" offset 1
#set boxwidth 0.85
set tmargin 5
set lmargin 7
set key tmargin
plot 'slot_runtime.dat' \
        using 2:xticlabel(1) title columnheader(2) fs solid 0.25, \
     '' using 3:xticlabel(1) title columnheader(3) fs solid 0.50, \
     '' using 4:xticlabel(1) title columnheader(4) fs solid 0.75, \
     '' using 5:xticlabel(1) title columnheader(5) fs solid 1.00
