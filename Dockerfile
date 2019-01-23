FROM karmab/kcli
MAINTAINER Karim Boumedhel <karimboumedhel@gmail.com>
ADD . /kopf
RUN pip install kopf 
ENTRYPOINT ["kopf","run","/kopf/handlers.py", "--verbose"]
