file=`readlink -f $1`
tail -n +2 $file \
| dos2unix \
| gawk -F, -v f=$file \
'BEGIN { OFS = "|"}
 { t1 = gensub(/[-:]/," ","g",$2);
   t2 = gensub(/[-:]/," ","g",$3);
   d1=mktime(t1);
   d2=mktime(t2);
   if( $9=="Y" ) sf="true";
   else sf="false";
   dist_fmt=sprintf("%g", $5)
   if ( $6 != "0" && $7 != "0" && $10 != "0" && $11 != "0" )
      print $2 "-04:00", d2-d1, "SRID=4326;LINESTRING("$6 " " $7" 0," $10 " " $11 " " d2-d1 ")", f, \
         "{"\
         "\"extra\":" $14 \
         ",\"mta_tax\":" $15 \
         ",\"vendorid\":" $1 \
         ",\"ratecodeid\":" $8 \
         ",\"tip_amount\":" $16 \
         ",\"fare_amount\":" $13 \
         ",\"payment_type\":" $12 \
         ",\"tolls_amount\":" $17 \
         ",\"total_amount\":" $19 \
         ",\"trip_distance\":" dist_fmt \
         ",\"passenger_count\":" $4 \
         ",\"store_and_fwd_flag\":" sf \
         ",\"improvement_surcharge\":" $18 \
         "}" }'

