#!/bin/bash
rm $1*.zip
( cd $1 && zip -r ../$1.zip *.py *.c *.h ply/ )
zip -j $1-tests.zip $1/tests/*
