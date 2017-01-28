import redis
import time
import requests
import sys

red = redis.StrictRedis(host='localhost', port=6379, db=0)


def poll(update_cache):
    auth = requests.auth.HTTPBasicAuth('jason', 'Langenburg2020')
    r = requests.get('https://apartment.diller.ca/conditions/current', auth=auth)
    conditions = r.json()
    timestamp = int(time.time())
    print conditions
    red.set(str(timestamp), conditions)
    if update_cache:
        print "Updating Cache"
        cache = red.hgetall('tempsamples')
        ts = datetime.datetime.fromtimestamp(timestamp)
        cache['samples'].append( { 'datetime': ts.strftime('%Y-%m-%d %H:%M:%S'),
                         'temperature': conditions['temperature'],
                         'humidity': conditions['humidity']
        })
        red.hmset('tempsamples', cache)
        print "Cache updated"

if __name__ == '__main__':
    err_count = 0
    loop_count = 0
    while True:
        try:
            loop_count += 1
            poll(loop_count % 100 == 0)
            err_count = 0
            if loop_count >= 100:
                loop_count = 0
        except Exception as x:
            err_count += 1
            if err_count >= 100:
                print x
                sys.exit(1)

        time.sleep(5)

