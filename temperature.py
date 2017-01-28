# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, Response
from dht import Sensor
import logging
import pigpio
import json
import redis
import time
import ast
import os
import re
import itertools
import datetime
from collections import namedtuple

app = Flask(__name__)
app.debug = True
r = redis.StrictRedis(host='localhost', port=6379, db=0)
Conditions = namedtuple('Conditions', 'temperature humidity message')
logging.basicConfig(level=logging.DEBUG)

pi = pigpio.pi()
CACHE_TIME = 5

@app.route("/")
def home():
    return render_template('main.html')

@app.route("/history")
def history():
    cached_json = r.get('history_cache')
    if cached_json:
        return Response(cached_json, mimetype='application/json')

    samples = r.hgetall('tempsamples')
    if samples:
        samples = ast.literal_eval(samples['samples'])
        logging.debug(type(samples))
        samples = sorted(samples, key=lambda item: datetime.datetime.strptime(item['datetime'], '%Y-%m-%d %H:%M:%S'))
        output = {
            'temp' : [{'x' : time.mktime(datetime.datetime.strptime(d['datetime'], '%Y-%m-%d %H:%M:%S').timetuple()), 'y': float(d['temperature'])} for d in samples],
            'humidity' : [{'x': time.mktime(datetime.datetime.strptime(d['datetime'],'%Y-%m-%d %H:%M:%S').timetuple()), 'y': float(d['humidity'])} for d in samples]
        }
        cache_json = json.dumps(output)
        r.set('history_cache', cache_json, ex=500)
        return jsonify(output)
    else:
        return "Data not available"

@app.route("/current")
def conditions():
    last_reading_str = r.get('last_reading')
    if last_reading_str:
        try:
            last_reading = ast.literal_eval(last_reading_str)
        except:
            logging.warn(
                "Last info from redis was bad. Ignoring and discarding")
            last_reading = None
            r.delete('last_reading')
    else:
        last_reading = None
    if not last_reading or time.time() - last_reading[3] > CACHE_TIME:
        logging.debug("Getting new readings")
        sensor = Sensor(pi, 25)
        sensor.read()
        RETRIES = 4
        sleep = 0.1
        time.sleep(sleep)
        times = 0
        while times < RETRIES and sensor.temperature == -999:
            sleep = sleep * 2
            time.sleep(sleep)
            times += 1
        r.set('last_reading', (sensor.temperature,
                               sensor.humidity, sensor.message, time.time()))
        conditions = Conditions(
            sensor.temperature, sensor.humidity, sensor.message)
        sensor.cancel()
    else:
        logging.debug("Using cached readings")
        conditions = Conditions(
            last_reading[0], last_reading[1], last_reading[2])
    d = {'temperature': str(round(conditions.temperature, 1)),
         'humidity': str(round(conditions.humidity, 1)),
         'message': conditions.message}

    return jsonify(d)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
