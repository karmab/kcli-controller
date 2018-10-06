FROM karmab/kcli
MAINTAINER Karim Boumedhel <karimboumedhel@gmail.com>

ADD controller.py /tmp
ADD machine.yml /tmp

ENTRYPOINT  ["python3", "-u", "/tmp/controller.py"]
