

Start the application using:

POP3 Server Only
```
python3 bin/genaipot.py --pop3
```

SMTP Server Only
```
python3 bin/genaipot.py --smtp
```

Both protocols
```
python3 bin/genaipot.py --all
```

## Docker

you can download the latest docker image or you can build yourself, to build yourself use,
the docker image will first run the config wizard and afterwards starts both protocols

```
docker build . -t genaipot
docker run -p25:25 110:110 genaipot
```

