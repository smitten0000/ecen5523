#!/bin/bash
rm $1*.zip
rm $1/*.pyc
rm $1/tests/*.s
rm $1/tests/*.pyc
zip -j $1.zip $1/*.py $1/*.c $1/*.h
zip -j $1-tests.zip $1/tests/*
