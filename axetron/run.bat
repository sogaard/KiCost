kicost -c config.yaml --debug 0 -n 1 -f AXPN AXID --group_fields AXID --split_extra_fields AXID -w -i ..\..\dms\data\active.csv   --json
kicost -c config.yaml --debug 0 -n 1 -f AXPN AXID --group_fields AXID --split_extra_fields AXID -w -i ..\..\dms\data\inactive.csv --json
kicost -c config.yaml --debug 0 -n 1 -f AXPN AXID --group_fields AXID --split_extra_fields AXID -w -i ..\..\dms\data\ignored.csv  