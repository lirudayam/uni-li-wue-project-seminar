#!/bin/bash

while (("$#")); do
  FILE_TO_BE_DEPLOYED=$1
  IMGNAME=$(echo "$FILE_TO_BE_DEPLOYED" | tr '[:upper:]' '[:lower:]')
  mkdir "tmp_deploy"
  cp BaseFetcher.py "tmp_deploy"
  cp DWConfigs.py "tmp_deploy"
  cp KafkaConnector.py "tmp_deploy"
  cp ErrorTypes.py "tmp_deploy"
  cp HashiVaultCredentialStorage.py "tmp_deploy"
  SCRIPT_FILE="${FILE_TO_BE_DEPLOYED}"
  SCRIPT_FILE+="DataFetcher.py"
  cp "${SCRIPT_FILE}" "tmp_deploy"

  cd tmp_deploy || exit
  pipreqs .
  touch output.log
  touch Dockerfile
  cat <<EOT >>Dockerfile
FROM python:3.6
MAINTAINER uni.li-wue.projekt@protonmail.com
WORKDIR /
COPY . .
RUN pip3 install -r requirements.txt
CMD [ "python3", "${SCRIPT_FILE}" ]
EOT
  docker image rm uniliwuedockerepo/"${IMGNAME}"-fetcher
  docker build -t uniliwuedockerepo/"${IMGNAME}"-fetcher .
  docker push uniliwuedockerepo/"${IMGNAME}"-fetcher

  cd ..
  rm -r tmp_deploy

  shift
done

exit
