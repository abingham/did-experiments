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
EXPOSE 4647

CMD ["python3", "server.py"]