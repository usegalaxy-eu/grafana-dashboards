#!/bin/bash
rm -f *.json

sqlite3 --csv -separator "$(printf '\t')" /var/lib/grafana/grafana.db 'select title,data from dashboard;' | awk -F'\t' '{gsub("\"", "", $1); print $2 > $1".json" }'

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

Name | Live Version | JSON
--- | --- | ---
EOF

sqlite3 --csv -separator "$(printf '\t')" /var/lib/grafana/grafana.db 'select title,uid,title from dashboard;' | awk -F'\t' '{gsub("\"", "", $1); gsub(" ", "%20", $3); print $1" | [Live](https://stats.galaxyproject.eu/d/"$2") | [File](./"$3".json)"}' >> README.md

cat >> README.md <<-EOF

## License

GPLv3 I guess? Can your really license some json files with queries in them?
EOF


if [[ $1 != "--no-commit" ]]; then
	git add *.json README.md
	git commit -a -m "Automated commit for $(date)"
	git push --quiet
fi
