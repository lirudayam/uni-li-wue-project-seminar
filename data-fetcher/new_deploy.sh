#!/bin/bash

rm all_deploy.sh
touch all_deploy.sh

while (("$#")); do
  FILE_TO_BE_DEPLOYED=$1
  IMGNAME=$(echo "$FILE_TO_BE_DEPLOYED" | tr '[:upper:]' '[:lower:]')
  ./build.sh ${FILE_TO_BE_DEPLOYED}

  echo "" >>all_deploy.sh
  echo "# -- ${IMGNAME}" >>all_deploy.sh
  echo "sudo docker stop ${IMGNAME}" >>all_deploy.sh
  echo "sudo docker rm ${IMGNAME}" >>all_deploy.sh
  echo "sudo docker pull uniliwuedockerepo/"${IMGNAME}"-fetcher" >>all_deploy.sh
  echo "sudo docker run -d --name ${IMGNAME} --env-file ./docker-cfg uniliwuedockerepo/"${IMGNAME}"-fetcher" >>all_deploy.sh
  echo "sudo docker update --restart on-failure ${IMGNAME}" >>all_deploy.sh
  shift
done

exit
