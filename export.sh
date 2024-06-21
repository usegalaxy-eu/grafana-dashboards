#!/bin/bash
# CONNECTION_STRING is an environment variable containing a PostgreSQL connection string, just like in the
# example below.
#   CONNECTION_STRING=postgresql://user:secret@localhost/mydatabase
# See https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING for more details. Leave
# it blank to use .pgpass or the PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD environment variables.

rm -f *.json
psql "$CONNECTION_STRING" -c '\copy (select title,data from dashboard) TO STDOUT WITH (FORMAT csv, DELIMITER E'\t', HEADER false);' | awk -F'\t' '{gsub("\"", "", $1); print $2 > $1".json" }'

# Clean up JSON files by removing extraneous quotes, sort
# JSON keys using jq, and delete output files with less
# than 10 lines.
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

Name | Tags | Version | Live | JSON
--- | --- | --- | --- | ---
EOF

psql "$CONNECTION_STRING" -c '\copy (SELECT title,uid,title,version,GROUP_CONCAT(dashboard_tag.term) FROM dashboard left outer join dashboard_tag on dashboard.id = dashboard_tag.dashboard_id WHERE dashboard.is_folder = 0 GROUP BY title, uid, title order by title asc) TO STDOUT WITH (FORMAT csv, DELIMITER E'\t', HEADER false);' | \
    awk -F'\t' '{gsub("\"", "", $1); gsub("\"", "", $3); gsub(" ", "%20", $3); print $1" | "$5" | "$4" | [Live](https://stats.galaxyproject.eu/d/"$2") | [File](./"$3".json)"}' >> README.md

cat >> README.md <<-EOF

## License

GPLv3 I guess? Can your really license some json files with queries in them?
EOF


if [[ $1 != "--no-commit" ]]; then
	git add *.json README.md
	git commit -a -m "Automated commit for $(date)"
	git push --quiet
fi
