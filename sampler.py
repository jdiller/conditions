import redis
import datetime
import time
import itertools
import re
import logging
import ast

r = redis.StrictRedis(host='localhost', port=6379, db=0)

start = time.time()
output = []
it = r.scan_iter(match='*')
slice_start = time.time()
it = itertools.islice(it, 0, None, 100)
slice_finish = time.time()
print "Slice time: {}".format(slice_finish - slice_start)

read_time = 0
fuckery_time = 0
scan_time = 0
scan_start = time.time()
for key in it:
    if re.match(r'\d{10}', key):
        try:
            scan_finish = time.time()
            scan_time += (scan_finish - scan_start)
            get_start = time.time()
            last_reading_str = r.get(key)
            get_stop = time.time()
            read_time += (get_stop - get_start)
            fuckery_start = time.time()
            last_reading = ast.literal_eval(last_reading_str)
            timestamp = datetime.datetime.fromtimestamp(int(key))
            output.append( { 'datetime': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                             'temperature': last_reading['temperature'],
                             'humidity': last_reading['humidity']
                          })
            fuckery_finish = time.time()
            fuckery_time = fuckery_finish - fuckery_start
            scan_start = time.time()
        except:
            print "Last info from redis was bad. Ignoring and discarding"
            last_reading = None

finish = time.time()
elapsed = finish - start
print str(len(output)) + " samples taken"
print "Total time: {}".format(elapsed)
print "Time spend reading from redis: {}".format(read_time)
print "Time spent in python fuckery: {}".format(fuckery_time)
print "Time spend scanning records: {}".format(scan_time)
r.hmset('tempsamples', {'samples':output} )

