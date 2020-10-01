#!/usr/bin/env bash

rsync -Pax test_template/ test/ --delete --backup-dir="$HOME/.rsync-backup/" --backup
