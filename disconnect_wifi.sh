wifi_conn=$(LANG=C nmcli d)
echo $wifi_conn
if [[ $wifi_conn != "" ]];  
then sudo kill $wpa_conn
else echo "wifi disconnected"
fi