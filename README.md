# AV Perf Analyser
Aviation Performance Checker: automatically check and track you plane's performance vs. book and trend

This is tested on Garmin G500Txi .csv files. 

The plane model is extracted from the engine data. You copy and paste the existing plane in the `models` directory and edit the configuration and performance csv files.

To install locally:

cd $HOME
$ mkdir .opt
$ mkdir .opt/projects
$ cd ~/.opt/projects/ 
$ git clone git@github.com:denopa/AVPerfAnalyser.git
$ cd AVPerfAnalyser
$ virtualenv -p python3 .AVPerfAnalyser-ve
$ source .AVPerfAnalyser-ve/bin/activate

(.AVPerfAnalyser-ve)$ pip install -r requirements.txt

To run locally (from the opt/projects/AVPerfAnalyser directory):
$ virtualenv -p python3 .AVPerfAnalyser-ve
(.AVPerfAnalyser-ve)$ python3 api.py

and go to http://0.0.0.0:5000/uploadFlight on your browser