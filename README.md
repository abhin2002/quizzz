## Setup


Install requirements:
```
pip install -r fastapi/requirements.txt
pip install -r streamlit/requirements.txt
```

### Backend
```
python fastapi/src/main.py
```

### Frontend
```
python streamlit/src/main.py
```

3. Docker

```
cd fastapi
```

```
docker build -t my-python-app
```

```
docker run -d -p 3000:3000 --name my-running-app my-python-app
```

### Notes:
- This repo is built and tested on python `3.10`.
- Faster Whisper model is being run on CPU with Float32. You can change the config in file `fastapi/src/speech_rec/service.py` (See more config in the [Faster Whisper repo](https://github.com/guillaumekln/faster-whisper)).