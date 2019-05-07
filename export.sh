#!/bin/bash
rm -f *.json

sqlite3 --csv -separator "$(printf '\t')" /var/lib/grafana/grafana.db 'select title,uid,data from dashboard;' | awk -F'\t' '{print $3 > $1"-"$2".json" }'

for i in *.json; do
	q=$(mktemp)
	cat "$i" | sed 's/^"//;s/"$//g;s/""/"/g' | jq -S . > $q
	mv $q "$i";
done;

git add *.json
git commit -a -m "Automated commit for $(date)"

