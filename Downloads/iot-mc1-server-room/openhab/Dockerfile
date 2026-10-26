FROM openhab/openhab:4.3.3-debian
USER root
# Власний CA додається до стандартного truststore Java; перевірка TLS не вимикається.
COPY .runtime/certs/ca.crt /tmp/iot-ca.crt
RUN keytool -importcert -noprompt -trustcacerts -alias iot-mc1-ca \
    -file /tmp/iot-ca.crt -cacerts -storepass changeit \
    && rm /tmp/iot-ca.crt
