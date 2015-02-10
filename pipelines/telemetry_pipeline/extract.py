import transform
from os import path
from datetime import datetime as dt, timedelta

_PIPELINE_PATH = path.dirname(path.realpath(__file__))+'/'

startdate = dt.strptime("20141014", "%Y%m%d")
enddate = dt.strptime("20141230", "%Y%m%d")

week = startdate
while week <= enddate:
   week_string = week.strftime("%Y-%m-%d")
   transform.run(week_string, "release", _PIPELINE_PATH+"/data/week_of_"+week_string.translate(None, '-')+"_aurora.csv")
   week += timedelta(days=7)
