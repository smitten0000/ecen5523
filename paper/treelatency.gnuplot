# this performs a linear regression
#f(x) = m*x + b
#fit f(x) 'treelatency.dat' using 2:4 via m,b
set terminal epslatex monochrome "" 8 size 3.5in,2in
set output "treelatency.tex"
set xlabel "Number of nodes (in thousands)"
set ylabel "Latency (seconds)"
set nokey
set style line 1 lt 2 lc rgb "red" lw 3
plot 'treelatency.dat' using ($2/1000):4 ls 1 with linespoints
#plot 'treelatency.dat' using 2:4 ls 1 with linespoints, \
#     f(x) title 'Line fit'
