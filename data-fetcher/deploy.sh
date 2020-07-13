echo "Installing Tools"
pip3 install wheel
pip3 install setuptools

#FILE_TO_BE_DEPLOYED=$1

while (( "$#" )); do
  FILE_TO_BE_DEPLOYED=$1
  mkdir "tmp_deploy"
  mkdir "tmp_deploy/${FILE_TO_BE_DEPLOYED}"
  cp DWConfigs.py "tmp_deploy/${FILE_TO_BE_DEPLOYED}"
  cp KafkaConnector.py "tmp_deploy/${FILE_TO_BE_DEPLOYED}"
  cp ErrorTypes.py "tmp_deploy/${FILE_TO_BE_DEPLOYED}"
  cp setup.py tmp_deploy/
  SCRIPT_FILE="${FILE_TO_BE_DEPLOYED}"
  SCRIPT_FILE+="DataFetcher.py"
  cp "${SCRIPT_FILE}" "tmp_deploy/${FILE_TO_BE_DEPLOYED}"
  cd tmp_deploy
  touch README.md
  touch __init__.py
  cat <<EOT >> __init__.py
import ${FILE_TO_BE_DEPLOYED}DataFetcher
def main():
  ${FILE_TO_BE_DEPLOYED}DataFetcher()
EOT
  cp __init__.py "${FILE_TO_BE_DEPLOYED}"

  sed -i '' "s/FETCHER_NAME/$FILE_TO_BE_DEPLOYED/g" setup.py
  python3 setup.py sdist bdist_wheel

  cd dist
  DIST="uniliwue.datafetchers"
  DIST+="${FILE_TO_BE_DEPLOYED}"
  DIST+="-0.0.1"
  FOLDER_NAME="${DIST}"
  DIST+=".tar.gz"

  echo "Insert password for VM to copy:"
  scp -P 64526 "${DIST}" pjs@wrzh020.rzhousing.uni-wuerzburg.de:/home/pjs/python_fetchers

  echo "Insert password for VM to install:"
  ssh -p 64526 pjs@wrzh020.rzhousing.uni-wuerzburg.de /bin/bash << EOF
    ps ax | grep "${DIST}" | grep -v grep | awk '{print $1}' | xargs kill
    cd python_fetchers
    tar -xvzf "${DIST}"
    cd "${FOLDER_NAME}"
    echo $DIST
    cd "${FILE_TO_BE_DEPLOYED}"
    bash -c "exec -a ${DIST} python3 ${FILE_TO_BE_DEPLOYED}DataFetcher.py"

EOF

  cd ../..
  rm -r tmp_deploy
shift
done

exit