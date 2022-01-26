import os, json, re, time

###########
#LOAD HUMIO LICENSE
print("LOADING HUMIO LICENSE")
command = '\'TOKEN=`cat /data/humio-data/local-admin-token.txt`; \
LICENSE_KEY=eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzUxMiJ9.eyJpc09lbSI6ZmFsc2UsImF1ZCI6Ikh1bWlvLWxpY2Vuc2UtY2hlY2siLCJzdWIiOiJhbmRyZXcubGF0aGFtQGNyb3dkc3RyaWtlLmNvbSIsInVpZCI6ImdYRk9jTVp5WUNDSldtaGIiLCJtYXhVc2VycyI6NSwiYWxsb3dTQUFTIjpmYWxzZSwibWF4Q29yZXMiOjEwMCwidmFsaWRVbnRpbCI6MTY2MzMxNTA1NiwiZXhwIjoxNzI2ODE5MDU2LCJpc1RyaWFsIjpmYWxzZSwiaWF0IjoxNjMyMjExMDU2LCJtYXhJbmdlc3RHYlBlckRheSI6MTB9.ASi8WxG6U9Uy7b2Q9EUnSTOa6z_ADQbpXyBkCEbjj98ALrfDSbCrbRd2SD169XvI9NvbeOI5tJQUXiwTLtzWFl3IADqOOvSdtfBp8n97Qys24piwxJzfZOxn3GC2Z2zafsBzgEP7mzrTGzUShMSM2VzkPnp-DnloB9b95xRVEDLg_I7r; \
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{ \\"query\\": \\"mutation { updateLicenseKey(license: \\\\\\\"$LICENSE_KEY\\\\\\\") { expiresAt } }\\" }" \
 http://localhost:8080/graphql\''
command = "docker exec humio bash -c " + command
stream = os.popen(command)
output = stream.read()

if output.find("errorCode") != -1:
     print("FAILED TO LOAD HUMIO LICENSE")
else:
     print("- HUMIO LICENSE LOADED")

############
#CREATE KAFKA TOPIC
print("CREATING KAFKA QUEUE")
command = 'kafka-topics --bootstrap-server broker:9092 \
             --create \
             --topic ForwardedEventsTopic'
command = "docker exec broker " + command
stream = os.popen(command)
output = stream.read()

if output.find("Created") != -1:
     print("- KAFKA QUEUE CREATED")
else:
     print("ERROR")

############
#CREATE HUMIO REPOSITORY
print("CREATING HUMIO REPOSITORY")
command = '\'TOKEN=`cat /data/humio-data/local-admin-token.txt`; \
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\\"query\\":\\"mutation{createRepository(name:\\\\\\\"forwardedEventsRepo\\\\\\\") {repository {name}}}\\"}" \
 http://localhost:8080/graphql\''

command = "docker exec humio bash -c " + command
stream = os.popen(command)
output = stream.read()

if output.find("errorCode") != -1:
     print("FAILED TO CREATE REPOSITORY")
else:
     print("- HUMIO REPOSITORY CREATED")

############
#CREATE HUMIO PARSER
print("CREATING HUMIO PARSER")
command = '\'TOKEN=`cat /data/humio-data/local-admin-token.txt`; \
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\\"query\\":\\"mutation{createParser(input:{name:\\\\\\\"eventForwarderParser\\\\\\\",testData:[],repositoryName:\\\\\\\"forwardedEventsRepo\\\\\\\",tagFields:[],sourceCode:\\\\\\\"parseJson() | findTimestamp(field=timestamp)\\\\\\\",force:false}) { parser{id,name}}}\\"}" \
 http://localhost:8080/graphql\''

command = "docker exec humio bash -c " + command
stream = os.popen(command)
output = stream.read()

parserID = ""
if output.find("errorCode") != -1:
    print("FAILED TO CREATE PARSER")
else:
    jsonResponse = json.loads(output)
    parserID=jsonResponse['data']['createParser']['parser']['id']
    print("- HUMIO PARSER CREATED: ", parserID)


############
#CREATE HUMIO INGEST TOKEN
print("CREATING HUMIO INGEST TOKEN")
command = '\'TOKEN=`cat /data/humio-data/local-admin-token.txt`; \
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\\"query\\":\\"mutation {addIngestTokenV2(input: {name:\\\\\\\"forwardedEventsIngestToken\\\\\\\", repositoryName: \\\\\\\"forwardedEventsRepo\\\\\\\", parserId: \\\\\\\"'+parserID+'\\\\\\\"}) {name,token}}\\"}" \
 http://localhost:8080/graphql\''

command = "docker exec humio bash -c " + command
stream = os.popen(command)
output = stream.read()

ingestToken = ""

if output.find("errorCode") != -1:
     print("FAILED TO CREATE INGEST TOKEN")
else:
    jsonResponse = json.loads(output)
    ingestToken=jsonResponse['data']['addIngestTokenV2']['token']
    print("- HUMIO INGEST TOKEN CREATED: ", ingestToken)

############
#CREATE HUMIO EVENT FORWARDER
print("CREATING HUMIO EVENT FORWARDER")
command = '\'TOKEN=`cat /data/humio-data/local-admin-token.txt`; \
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\\"query\\": \\"mutation { createKafkaEventForwarder(input:{name:\\\\\\\"ForwardEventsToSplunk\\\\\\\",description:\\\\\\\"Description\\\\\\\",topic:\\\\\\\"ForwardedEventsTopic\\\\\\\",properties:\\\\\\\"bootstrap.servers=broker.eventforwarding_default:29092\\\\\\\"}){id}}\\" }" \
 http://localhost:8080/graphql\''

command = "docker exec humio bash -c " + command
stream = os.popen(command)
output = stream.read()
eventForwarder = ""
if output.find("errorCode") != -1:
     print("FAILED TO CREATE EVENT FORWARDER")
else:
    jsonResponse = json.loads(output)
    eventForwarder=jsonResponse['data']['createKafkaEventForwarder']['id']
    print("- HUMIO EVENT FORWARDER CREATED: ", eventForwarder)


############
#CREATE HUMIO EVENT FORWARDER RULE
print("CREATING HUMIO EVENT FORWARDER RULE")
command = '\'TOKEN=`cat /data/humio-data/local-admin-token.txt`; \
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\\"query\\":\\"mutation {createEventForwardingRule(input:{eventForwarderId:\\\\\\\"'+eventForwarder+'\\\\\\\",repoName:\\\\\\\"forwardedEventsRepo\\\\\\\",queryString:\\\\\\\"type = security\\\\\\\"}) {id}}\\"}" \
 http://localhost:8080/graphql\''

command = "docker exec humio bash -c " + command
stream = os.popen(command)
output = stream.read()

if output.find("errorCode") != -1:
     print("FAILED TO CREATE EVENT FORWARDER")
else:
    jsonResponse = json.loads(output)
    eventForwarderRule=jsonResponse['data']['createEventForwardingRule']['id']
    print("- HUMIO EVENT FORWARDER CREATED: ", eventForwarderRule)


############
#CREATE SPLUNK HTTP EVENT COLLECTOR LISTENER
print("CREATING SPLUNK HTTP EVENT COLLECTOR")
command = "curl -s --insecure -u admin:password123 https://localhost:8089/servicesNS/admin/splunk_httpinput/data/inputs/http -d name=humioForwarder index=main"
stream = os.popen(command)
output = stream.read()
splunkIngestToken = ""
if output.find("<s:key name=\"token\">") != -1:
    result = re.search("<s:key name=\"token\">(.*)<\\/s:key>", output)
    splunkIngestToken = result.group(1)
    print("- SPLUNK HTTP EVENT COLLECTOR CREATED: INGEST TOKEN:", splunkIngestToken)
else:
    print("ERROR")


############
#CREATE KAFKA-CONNECT SPLUNK SINK
print("CREATING KAFKA-CONNECT SPLUNK SINK")
jsonPayload = {
  "name": "kafka-connect-splunk",
  "config": {
    "name": "kafka-connect-splunk",
    "connector.class": "com.splunk.kafka.connect.SplunkSinkConnector",
    "tasks.max": "3",
    "topics": "ForwardedEventsTopic",
    "splunk.indexes": "main",
    "splunk.hec.uri": "https://splunk:8088",
    "splunk.hec.ssl.validate.certs": "false",
    "splunk.hec.raw": "true",
    "splunk.hec.ack.enabled": "false",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "key.converter": "org.apache.kafka.connect.storage.StringConverter",
    "key.converter.schemas.enable": "false",
    "value.converter.schemas.enable": "false"
  }
}

jsonPayload['config']['splunk.hec.token'] = splunkIngestToken
payload = json.dumps(jsonPayload)
command = 'curl -s localhost:8083/connectors -X POST -H "Content-Type: application/json" -d \''+payload+'\''
stream = os.popen(command)
output = stream.read()
if output.find("error_code") != -1:
    print("ERROR")
else:
    print("- KAFKA-CONNECT SPLUNK SINK CREATED")



print("\nEVENT FORWARDING TO ENVIRONMENT COMPLETED SETUP SUCCESSFULLY")
print("--------------------------------------------------------------")
print("Access Humio at: http://192.168.0.1:8080. Username: developer. Password: Secret123")
print("Access Splunk at: http://192.168.0.1:8000. Username: admin. Password: password123")
print("Humio Ingest Token: "+ingestToken+"\n")
print("Please log in to Humio and Splunk to varify test results\n")
input("Press RETRUN to begin testing.")

############
#TEST EVENT FORWARDING - INVOKE FORWARDING
print("STARTING UNIT TESTS")
jsonPayload = {
    "level":"INFO",
    "type":"security",
    "message":"Info Security Message"
}
jsonPayload['timestamp'] = time.time()
payload = json.dumps(jsonPayload)
command = 'curl -s --location --request POST \'http://localhost:8080/api/v1/ingest/raw\' --header \'Content-Type: application/json\' --header \'Authorization: Bearer '+ingestToken+'\'  -d \''+payload+'\''
print("\nPOSTING: ", command)
stream = os.popen(command)
output = stream.read()

if output != "{}" :
    print("ERROR: ", output)

############
#TEST EVENT FORWARDING - BYPASS FORWARDING
jsonPayload = {
    "level":"INFO",
    "type":"infrastructure",
    "message":"Info Security Message"
}
jsonPayload['timestamp'] = time.time()
payload = json.dumps(jsonPayload)
command = 'curl -s --location --request POST \'http://localhost:8080/api/v1/ingest/raw\' --header \'Content-Type: application/json\' --header \'Authorization: Bearer '+ingestToken+'\'  -d \''+payload+'\''
print("\nPOSTING: ", command)
stream = os.popen(command)
output = stream.read()
if output != "{}" :
    print("ERROR: ", output)
print("\n")

############
#CHECK HUMIO RECEIVED 2 EVENTS
print("TESTING HUMIO RECEIVED 2 EVENTS")
command = '\'TOKEN=`cat /data/humio-data/local-admin-token.txt`; \
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\\"queryString\\": \\"*\\",\\"start\\": \\"24hours\\",\\"end\\": \\"now\\"}" \
 http://localhost:8080/api/v1/repositories/forwardedEventsRepo/query\''
command = "docker exec humio bash -c " + command
stream = os.popen(command)
output = stream.read()
if output.count('\n') == 2:
    print("- PASSED: TESTING HUMIO RECEIVED 2 EVENTS")
else:
    print("- FAILED: TESTING HUMIO RECEIVED 2 EVENTS")

############
#CHECK SPLUNK RECEIVED 1 EVENT
print("TESTING SPLUNK RECEIVED 1 EVENTS")
command = 'curl -s -u admin:password123 -k https://localhost:8089/services/search/jobs -d search="search *"'
stream = os.popen(command)
output = stream.read()
results = re.findall('<sid>(.*)<\\/sid>', output)
if len(results) == 1:
    print("- PASSED: TESTING SPLUNK RECEIVED 1 EVENTS")
else:
    print("- FAILED: TESTING SPLUNK RECEIVED 1 EVENTS")


