FROM python:3.7-slim
MAINTAINER burkasaurusrex
VOLUME /config
COPY *.py /app/
COPY requirements.txt /app/
COPY config.yml.template /config/config.yml.template
RUN \
	echo "**** install system packages ****" && \
		apt-get update && \
		apt-get upgrade -y && \
		apt-get install -y tzdata git && \
	echo "**** install python packages ****" && \
		pip3 install --upgrade --requirement /app/requirements.txt && \
	echo "**** install Plex-Auto-Collections ****" && \
		chmod +x /app/plex_auto_collections.py && \
		mkdir /config/images && \
		# Symbolic link '/app/images/ to '/config/images' until supported in config
		ln -s /config/images /app/images && \
	echo "**** cleanup ****" && \
		apt-get remove --purge -y git && \
		apt-get autoremove -y && \
		apt-get clean && \
		rm -rf \
			/app/requirements.txt \
			/tmp/* \
			/var/tmp/* \
			/var/lib/apt/lists/*
WORKDIR /app
ENTRYPOINT ["python3", "plex_auto_collections.py", "--config_path", "/config/config.yml", "--update"]