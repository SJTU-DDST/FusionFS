#!/bin/bash

rm -rf *.eps

for i in `ls *.gp`
do
    gnuplot $i
done

# 将EPS文件转换为PDF
for i in `ls *.eps`
do
    epstopdf $i
done

# for i in `ls *.pdf`
# do
#     pdfcrop $i
#     mv $i-crop.pdf $i
# done