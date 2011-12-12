#!/bin/sh
# Quick script to compile a given file with the necessary options

if [ "$#" -ne "1" ] ; then
  echo "Usage: `basename $0` <source-file>"
  exit 1
fi

PYFILE=$1
BASENAME=`echo "$PYFILE" | cut -f1 -d.`
SFILE="${BASENAME}.s"

./compile.py $PYFILE
gcc -o "$BASENAME" "$SFILE" -lm *.c -pg -m32
