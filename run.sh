#!/bin/bash

# 运行redis服务
#~/redis-stable/src/redis-server ~/redis-stable/redis_daemonize.conf

# 切换环境
#source activate flask_celery_study

# run 
# flask 默认端口为5000
#celery worker -A app.celery --loglevel=info
#python app.py

# 检测logs目录
if [ ! -d "./logs" ]; then
    mkdir ./logs
fi

# 使用supervisor来管理redis celery flask
supervisord -c ./supervisord.conf
