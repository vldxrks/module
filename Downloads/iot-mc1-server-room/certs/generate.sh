#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
dest=.runtime/certs
mkdir -p "$dest" .runtime/private
umask 077
if [ -s "$dest/server.key" ] && [ -s "$dest/server.crt" ] && [ -s "$dest/ca.crt" ]; then
    echo "Сертифікати вже є. Повторно не генеруються."
    exit 0
fi
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out .runtime/private/ca.key
openssl req -x509 -new -sha256 -days 3650 -key .runtime/private/ca.key \
    -subj '/CN=IoT MC1 Local CA/O=Student Lab' \
    -addext 'basicConstraints=critical,CA:TRUE' \
    -addext 'keyUsage=critical,keyCertSign,cRLSign' -out "$dest/ca.crt"
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$dest/server.key"
openssl req -new -key "$dest/server.key" -subj '/CN=mosquitto/O=Student Lab' \
    -out .runtime/private/server.csr
cat > .runtime/private/server.ext <<'EOF'
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:mosquitto,DNS:localhost,IP:127.0.0.1
EOF
openssl x509 -req -sha256 -days 365 -in .runtime/private/server.csr \
    -CA "$dest/ca.crt" -CAkey .runtime/private/ca.key \
    -CAcreateserial -CAserial .runtime/private/ca.srl \
    -extfile .runtime/private/server.ext -out "$dest/server.crt"
chmod 644 "$dest/ca.crt" "$dest/server.crt"
chmod 640 "$dest/server.key"
echo "CA і серверний сертифікат створено (SAN: mosquitto, localhost, 127.0.0.1)."
