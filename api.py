# TODO manage error messages for managerXray api, write tests for centraleRischiXray

import os, re
import sys
from flask import Flask, request, make_response, jsonify, render_template, send_from_directory, session, url_for, redirect
from flask_restful import Resource, Api
from werkzeug.utils import secure_filename
import json 
from time import sleep
import pandas

from libs.flightAnalyser import analyseFlight

# configure Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('flights')
app.config["ALLOWED_EXTENSIONS"] = ["csv"]
app.config['EXPLAIN_TEMPLATE_LOADING'] = False
app.secret_key = b'\xef<\xf0\xd6KE\x82\x11\xa1\x99-\x9b\xf0\x1a(\xe6-\xff\x7f[\xff\xc0k\xe9'
app.config["DEBUG"] = True #Must be False in prod
api = Api(app)

class home(Resource):
    def get(self):
        return("got nothing")
    
class favicon(Resource):
    def get(self):
        return send_from_directory(os.path.join(app.root_path, 'static'),
                            'favicon.ico',mimetype='image/vnd.microsoft.icon')

class uploadFlight(Resource):
    def allowedFiles(self, filename): 
    #use this RegEx to grab the file extension and see if it is allowed
        if re.search(r'([^.]*)$', filename).group().upper() in app.config['ALLOWED_EXTENSIONS']:
            return True
        else:
            return False

    def get(self):
        headers = {'Content-Type': 'text/html; charset=utf-8'}
        return make_response(render_template('uploadFlight.html'), 200, headers)

    def post(self):
        csv = request.files['csv']
        takeOffWeight = float(request.form['takeOffWeight'])
        takeOffMethod = request.form['takeOffMethod']
        if csv.filename == '':
            print('No filename')
            return("No filename")
        if self.allowedFiles(csv.filename) : 
            print("I'm allowed")
            filename = secure_filename(csv.filename)
            csv.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            csvFileName = os.path.join('flights', filename)
            flightAnalysis = analyseFlight(takeOffWeight,takeOffMethod, csvFileName)
            headers = {'Content-Type': 'text/html; charset=utf-8'}
            # return make_response(render_template('flightResuts.html', meta=flightAnalysis['meta'], tables=[table.to_html(classes= 'mystyle') for table in flightAnalysis['tables']], titles =['Take Off', 'Climb', 'Cruise', 'Approach']), 200, headers)
            return("got that far")
        else:
            print("file's bad")
            return("Invalid file; only CSVs are accepted")
       
api.add_resource(home, '/')
api.add_resource(favicon, '/favicon.ico')
api.add_resource(uploadFlight, '/uploadFlight')

if __name__ == '__main__':    
    app.run(threaded=True, host='0.0.0.0', port=os.environ.get("PORT", 5000))
