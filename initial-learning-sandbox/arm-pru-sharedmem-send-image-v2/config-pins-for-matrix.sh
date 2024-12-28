#!/bin/bash


gpiopins="P2.02 P2.04 P2.06 P2.08 P2.20 P2.22"
prupins="P2.28 P1.33 P1.31 P1.29 P2.30 P2.32 P2.34"

for pin in $prupins
do
    echo $pin
    config-pin $pin pruout
    config-pin -q $pin
done

for pin in $gpiopins
do
    echo $pin
    config-pin $pin gpio
    config-pin $pin out
    config-pin -q $pin
done
