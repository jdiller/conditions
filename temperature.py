# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify
from dht import Sensor
import logging
import pigpio
import redis
import time
import ast
import os
from collections import namedtuple

app = Flask(__name__)
app.debug=True
r = redis.StrictRedis(host='localhost', port=6379, db=0)
Conditions = namedtuple('Conditions', 'temperature humidity message')
logging.basicConfig(level=logging.DEBUG)

@app.route("/")
def home():
    return render_template('main.html')

@app.route("/current")
def conditions():
    pi = pigpio.pi()
    last_reading_str = r.get('last_reading')
    if last_reading_str:
        try:
            last_reading = ast.literal_eval(last_reading_str)
        except:
            logging.warn("Last info from redis was bad. Ignoring and discarding")
            last_reading = None
            r.delete('last_reading')
    else:
        last_reading = None
    if not last_reading or time.time() - last_reading[3] > 5:
        logging.debug("Getting new readings")
        sensor = Sensor(pi, 25)
        sensor.read()
        time.sleep(0.2)
        r.set('last_reading', (sensor.temperature, sensor.humidity, sensor.message, time.time()))
        conditions = Conditions(sensor.temperature, sensor.humidity, sensor.message)
    else:
        logging.debug("Using cached readings")
        conditions = Conditions(last_reading[0], last_reading[1], last_reading[2])
    d = {'temperature': str(round(conditions.temperature, 1)),
         'humidity': str(round(conditions.humidity, 1)),
         'message': conditions.message}

    return jsonify(d)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
