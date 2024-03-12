# DBDocker-Hongerlive
Dockerized version of Hongerlive scraper to utilize VPN to it exclusively

## Requirements
Docker, Docker-compose

And of course, VPN providers, too

## How to run it?
### 01. Change the file
#### Docker-compose.yml
in the environment section of gluetun service, you should fill out your VPN account settings. You can check out [**here**](https://github.com/qdm12/gluetun) for more details.
```
environment:
  - VPN_SERVICE_PROVIDER=mullvad
  - VPN_TYPE=wireguard
  - WIREGUARD_PRIVATE_KEY=QXJjYWxpdmUgc3Vja3MhIQ==
  - WIREGUARD_ADDRESSES=127.0.0.1/32
  - VPN_ENDPOINT_PORT=51820
  - SERVER_CITIES=Amsterdam
```

in the volume section of hongerlive service, please replace "YOUR_PATH" to the path where you want to store the result files.
```
/home/User/result:/arcalive
```

#### Dockerfile
Inside CMD, you should point out the name of the DB that would store the data you scrap and the id of the channel(slug) you want to scrap.
```
CMD ["python3", "/app/hongerlive.py", "geunhahaha", "singbung"]
```

### 02. Build & Run
Change the working directory into where the docker-compose file is located and run the following code.
```
docker-compose up -d
```
You may need to restart the hongerlive container as it takes time for gluetun container to connect to VPN server.

## FAQ
### Why no aiohttp or multiprocessing?
- To captcha or not to captcha, that is the question. I'm a n00b so don't know how to overcome it sry :(
