from flask import Flask
from flask import Response
from flask import request
import json
import requests
from requests_ntlm import HttpNtlmAuth
import time

app = Flask(__name__)

@app.route("/trigger_robot", methods=['POST'])
def trigger_robot():

    """ Trigger UiPath robot from twilio to get Invoice Status """

    # Read http request data

    input_prm = request.json['InputParameter']

    # Orchestrator User & Pwd

    User= 'bgalina@rpa'
    Pwd= 'Bgm-01021996'

    # Start Job

    URL_StartJob = 'https://orchdevrpa.joltag.com/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs'
    StartJob_header = {'X-UIPATH-OrganizationUnitId': "18"}
    StartJob_body = {
        "startInfo": {
        "ReleaseKey": "76a7d825-e038-45eb-9b7b-03f179655742",
        "Strategy": "ModernJobsCount",
        "JobsCount": 1,
        "InputArguments": "{\"ClientInfo\":\"" + input_prm + "\"}"
     }
    }

    # Get Response - Job Id
    response = requests.post(URL_StartJob,auth=HttpNtlmAuth(User,Pwd), headers=StartJob_header, json=StartJob_body)
    JobId  = response.json()['value'][0]['Id']

    Twilio_Message = {
        "JobId" : JobId
    }

    Twilio_Message_Json = json.dumps(Twilio_Message)
    
    # Reply to Twilio http request
    
    return Response(Twilio_Message_Json,mimetype='application/json')


@app.route("/job_status", methods=['GET'])
def job_status():

    """ Get the output of the process Using Job Id """

    # Read http request data

    JobId = request.args['JobId']

    # Orchestrator User & Pwd

    User= 'bgalina@rpa'
    Pwd= 'Bgm-01021996'

    URL_JobStatus = f'https://orchdevrpa.joltag.com/odata/Jobs?$filter=Id eq {JobId}'
    JobStatus_header = {'X-UIPATH-OrganizationUnitId': "18"}

    response = requests.get(URL_JobStatus,auth=HttpNtlmAuth(User,Pwd), headers=JobStatus_header)

    # Wait for the job to complete

    JobStatus = response.json()['value'][0]['Info']
    InvoiceInfo = 'Default'

    if JobStatus != "Job completed":
        time.sleep(3)
        InvoiceInfo = ''
    else:
        InvoiceInfo = json.loads(response.json()['value'][0]['OutputArguments'])['InvoiceInfo']

    Twilio_Message = {
        "JobStatus" : JobStatus,
        "InvoiceInfo" : InvoiceInfo
    }

    Twilio_Message_Json = json.dumps(Twilio_Message)

    return Response(Twilio_Message_Json,mimetype='application/json')


if __name__ == '__main__':
    app.run()