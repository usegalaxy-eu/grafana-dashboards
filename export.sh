#!/bin/bash
rm -f *.json

sqlite3 --csv -separator "$(printf '\t')" /var/lib/grafana/grafana.db 'select title,data from dashboard;' | awk -F'\t' '{print $2 > $1".json" }'

for i in *.json; do
	q=$(mktemp)
	cat "$i" | sed 's/^"//;s/"$//g;s/""/"/g' | jq -S . > $q
	mv $q "$i";

	lines=$(wc -l "$i" | awk '{print $1}')
	if (( lines < 10 )); then
		rm "$i"
	fi
done;


cat > README.md <<-EOF
# Grafana Dashbaords

See the live versions on [stats.galaxyproject.eu](https://stats.galaxyproject.eu):

EOF

sqlite3 --csv -separator "$(printf '\t')" /var/lib/grafana/grafana.db 'select title,uid from dashboard;' | awk -F'\t' '{print "- ["$1"](https://stats.galaxyproject.eu/d/"$2")"}' >> README.md

cat > README.md <<-EOF

## License

GPLv3 I guess? Can your really license some json files with queries in them?
EOF


git add *.json README.md
git commit -a -m "Automated commit for $(date)"

