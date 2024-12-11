```
pip install -r requirements.txt
```

```
flask run -p 8080
```

```
docker run -d --name jaeger -e COLLECTOR_ZIPKIN_HTTP_PORT=9411 -p 5775:5775 -p 6831:6831/udp -p 6832:6832/udp -p 5778:5778 -p 16686:16686 -p 14268:14268 -p 14250:14250 -p 14255:14255 -p 4317:4317 -p 4318:4318 jaegertracing/all-in-one:latest     
```