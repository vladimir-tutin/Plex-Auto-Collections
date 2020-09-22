FROM python:3.8-slim
VOLUME /config
COPY /app/. /app
COPY /config/. /config
COPY /requirements.txt /requirements.txt
RUN \
	echo "**** install system packages ****" && \
		apt-get update && \
		apt-get upgrade -y --no-install-recommends && \
		apt-get install -y tzdata --no-install-recommends && \
	echo "**** install python packages ****" && \
		pip3 install --no-cache-dir --upgrade --requirement /requirements.txt && \
	echo "**** install Plex-Auto-Collections ****" && \
		chmod +x /app/plex_auto_collections.py && \
	echo "**** cleanup ****" && \
		apt-get autoremove -y && \
		apt-get clean && \
		rm -rf \
			/requirements.txt \
			/tmp/* \
			/var/tmp/* \
			/var/lib/apt/lists/*
WORKDIR /app
ENTRYPOINT ["python3", "plex_auto_collections.py", "--config_path", "/config/config.yml", "--update"]