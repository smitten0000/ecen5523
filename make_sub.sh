#!/bin/bash
rm $1*.zip
( cd compiler && zip -r ../$1.zip *.py *.c *.h ply/ )
zip -j $1-tests.zip compiler/our_tests/*
