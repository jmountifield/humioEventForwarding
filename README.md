# Humio Data Lake - Co-Existance with Splunk

## Requirements:
- Docker Compose (Comes with Docker desktop on Mac, may need to be added to Linux)
- Python 3
- 8GB RAM allocated to Docker

## Setup:
1. git clone https://github.com/nthnthcandrew/humioEventForwarding.git
2. cd humioEventForwarding
4. docker-compose up
5. docker ps
6. Update configure.py with your LICENSE FILE
7. python3 configure.py
   
   This will setup the environment and run some tests. You can log into Humio and Spunk to validate the config and the Event Forwarding rule worked. The script will output the URLs and credentials to use.

## Shutdown:
This is not setup as a persistent configuration. When you stop it it will remove your containers and start again. To shut it down run:
1. docker-compose down
