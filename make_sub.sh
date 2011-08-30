#!/bin/bash

zip -j $1-compile.zip $1/compile.py $1/*.c $1/*.h
zip -j $1-test.zip $1/tests/*
