#!/bin/bash
rm $1*.zip
zip -j $1.zip $1/compile.py $1/*.c $1/*.h
zip -j $1-tests.zip $1/tests/*
