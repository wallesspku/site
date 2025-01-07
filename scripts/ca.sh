#!/sbin/bash

set -a
source $WALLESS_ROOT/envs

if [ ! -d acme.sh ]; then
    git clone https://github.com/acmesh-official/acme.sh.git
fi
git -C acme.sh pull
if [ ! -d ca ]; then
    git clone https://$GHPAT@github.com/wallesspku/ca
fi
git -C ca pull

cd acme.sh
./acme.sh --register-account -m $CF_Email
export IFS=" "
for DOM in $CA_DOMAINS; do
    WILDCARDS=" -d $DOM -d *.$DOM -d *.speedtest.ooklaserver.$DOM"
    echo working on $DOM $WILDCARDS
    ./acme.sh --issue --dns dns_cf $WILDCARDS
    ./acme.sh --install-cert --ecc -d $DOM --key-file ../ca/$DOM.key --fullchain-file ../ca/$DOM.cer
    cat ../ca/$DOM.cer ../ca/$DOM.key > ../ca/pem/$DOM.pem
done
cd -

wget $DOM_PULL_URL/$DOM1.cer -O /tmp/$DOM2.cer1 && \
    wget $DOM_PULL_URL/$DOM1.key -O /tmp/$DOM2.key1 && \
    mv /tmp/$DOM2.cer1 ca/$DOM2.cer && \
    mv /tmp/$DOM2.key1 ca/$DOM2.key && \
    cat ca/$DOM2.cer ca/$DOM2.key > ca/pem/$DOM2.pem

cd ca
git add .
git commit -m 'update ca'
git push
cd ..

