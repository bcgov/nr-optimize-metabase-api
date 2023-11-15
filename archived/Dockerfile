FROM node:alpine3.14
WORKDIR /src
COPY ["helloworld.py", "./"]
RUN apk add --no-cache python3 py3-pip
ENTRYPOINT ["python3", "helloworld.py"]