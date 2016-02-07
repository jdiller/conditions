# -*- coding: utf-8 -*-
from flask import Flask, render_template
from dht import DHT11
import pigpio

app = Flask(__name__)

@app.route("/")
def hello():
    pi = pigpio.pi()
    sensor = DHT11(pi, 25)
    sensor.read()
    return render_template('main.html', sensor=sensor)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
