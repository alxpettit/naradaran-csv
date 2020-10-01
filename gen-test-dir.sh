#!/usr/bin/env bash

rsync -Pax example/Before/ test/ --delete --backup-dir=/home/a/.rsync-backup/ --backup
