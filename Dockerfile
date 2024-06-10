FROM python:3.12.2-slim

RUN apt-get update && \
apt-get install -y tzdata ca-certificates && \
ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
echo "Asia/Shanghai" > /etc/timezone && \
dpkg-reconfigure -f noninteractive tzdata && \
apt-get clean && \
rm -rf /var/lib/apt/lists/*

COPY ./src/requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --no-cache-dir --upgrade -r requirements.txt -i http://mirrors.cloud.tencent.com/pypi/simple --trusted-host mirrors.cloud.tencent.com

COPY ./src /app

EXPOSE 28085

CMD ["sanic", "app", "--host", "0.0.0.0", "--port", "28085", "--single-process"]