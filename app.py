#!/usr/bin/env python
# coding=utf-8

import os
import random
import time
from flask import Flask, request, render_template, session, flash, redirect, \
    url_for, jsonify
from flask_mail import Mail, Message
from celery import Celery


app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret!'
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'


# Flask-Mail configuration
#app.config['MAIL_SERVER'] = 
#app.config['MAIL_PORT'] = 
#app.config['MAIL_USE_SSL'] = 'True'
#app.config['MAIL_USERNAME'] = 
#app.config['MAIL_PASSWORD'] = 
#app.config['MAIL_DEFAULT_SENDER'] = 
app.config['MAIL_SUPPRESS_SEND'] = 'True'  # 假的发送邮件

# initialize extensions
mail = Mail(app)

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html', email=session.get('email', ''))
    email = request.form['email']
    session['email'] = email

    # send the email
    msg = {}
    msg['subject'] = 'Hello From Flask'
    msg['body'] = 'This is a test email sent from a background Celery task.'
    msg['recipients'] = [request.form['email']]
    if request.form['submit'] == 'Send':
        # send right away
        send_async_email.delay(msg)
        flash('Sending email to {0}'.format(email))
    else:
        # send in one minute
        send_async_email.apply_async(args=[msg], countdown=60)
        flash('An email will be sent to {0} in one minute'.format(email))

    return redirect(url_for('index'))


@app.route('/longtask', methods=['POST'])
def longtask():
    task = long_task.apply_async()
    #task = long_task.delay()
    return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id)}


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = long_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


@celery.task
def send_async_email(msg_data):
    with app.app_context():
        msg = Message(
                subject=msg_data['subject'],
                body=msg_data['body'],
                recipients=msg_data['recipients'])
        mail.send(msg)


@celery.task(bind=True)
def long_task(self):
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'slient', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message}) 

        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


if __name__ == '__main__':
    app.run(debug=True)
