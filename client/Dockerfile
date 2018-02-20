FROM  docker:latest
LABEL maintainer=austin@sixty-north.com

RUN apk --update --no-cache add \
bash \
python3

WORKDIR /app

COPY . /app
RUN pip3 install -r requirements.txt

# ARG PORT
# EXPOSE ${PORT}
# ENV PORT=${PORT}
# EXPOSE 4647
# ARG DOCKER_HOST
# ENV DOCKER_HOST=$DOCKER_HOST

CMD ["python3", "client.py"]
