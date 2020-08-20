cd dw-sac-middleware
npm run build:mta
cd ..
cp -R dw-sac-middleware/gen/srv/srv/csn.json dw-kafka-processor/csn.json
cf stop uni-li-wue-dw-kafka-processor
cd dw-sac-middleware 
cf deploy mta_archives/uni-li-wue-dw-cloud_1.6.0.mtar
cd ../dw-kafka-processor
cf push


#cf deploy mta_archives/uni-li-wue-dw-cloud_1.2.0.mtar -m uni-li-wue-dw-cloud-srv -m db -r uni-li-wue-dw-cloud-db
#cf deploy mta_archives/uni-li-wue-dw-cloud_1.2.0.mtar -m haa-java -m haa -r xsahaa-uaa
#npm run build:mta
#cf deploy mta_archives/uni-li-wue-dw-cloud_1.2.0.mtar -m dwconfig
#npm run build:mta
#cf deploy mta_archives/uni-li-wue-dw-cloud_1.2.0.mtar -m uni-li-wue-dw-processor
