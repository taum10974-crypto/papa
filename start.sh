#!/bin/bash
MIN=$1
while true; do
    python3 main.py $MIN --dataset=data.txt --output=result.txt
    sleep 30
done
