SLUG=AIS_2024_05_05.zip

curl https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2024/$SLUG --output $SLUG
unzip $SLUG
rm $SLUG