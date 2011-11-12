#!/bin/bash
rm $1*.zip
( cd compiler && zip -r ../$1.zip *.cfg *.py *.c *.h ply/ )
zip -j $1-tests.zip compiler/our_hw6_tests/*
