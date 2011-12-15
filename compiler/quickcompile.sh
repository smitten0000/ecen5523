#!/bin/sh
# Quick script to compile a given file with the necessary options

if [ "$#" -ne "1" ] ; then
  echo "Usage: `basename $0` <source-file>"
  exit 1
fi

PYFILE=`basename $1`
BASENAME=`echo "$PYFILE" | cut -f1 -d.`
SFILE="${BASENAME}.s"

echo ./compile.py "$PYFILE"
./compile.py "$PYFILE"

echo gcc -g -o "$BASENAME" "$SFILE" *.c -lm -m32
gcc -g -o "$BASENAME" "$SFILE" *.c -lm -m32
