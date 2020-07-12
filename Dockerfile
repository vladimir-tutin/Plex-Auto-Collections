FROM python:3.7-slim
MAINTAINER burkasaurusrex
VOLUME /config
COPY /app/. /app
COPY /config/. /config
RUN \
	echo "**** install system packages ****" && \
		apt-get update && \
		apt-get upgrade -y && \
		apt-get install -y tzdata && \
	echo "**** install python packages ****" && \
		pip3 install --upgrade --requirement /app/requirements.txt && \
	echo "**** install Plex-Auto-Collections ****" && \
		chmod +x /app/plex_auto_collections.py && \
	echo "**** cleanup ****" && \
		apt-get autoremove -y && \
		apt-get clean && \
		rm -rf \
			/app/requirements.txt \
			/tmp/* \
			/var/tmp/* \
			/var/lib/apt/lists/*
WORKDIR /app
ENTRYPOINT ["python3", "plex_auto_collections.py", "--config_path", "/config/config.yml", "--update"]