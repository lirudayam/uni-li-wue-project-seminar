cd dw-sac-middleware
npm run build:mta
cd ..
cp -R dw-sac-middleware/gen/srv/srv/csn.json dw-kafka-processor/csn.json
cf stop uni-li-wue-dw-kafka-processor
cd dw-sac-middleware 
cf deploy mta_archives/uni-li-wue-dw-cloud_1.0.2.mtar
cd ../dw-kafka-processor
cf push