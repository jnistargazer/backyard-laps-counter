FROM nginx:latest
USER root
RUN useradd -ms /bin/bash webmaster && usermod -aG root webmaster && usermod -aG sudo webmaster && echo "webmaster:webmaster" | chpasswd
RUN mkdir /var/www && chown webmaster.root /var/www
RUN apt-get update && apt-get install -y procps curl python3 python3-pip python3-opencv apt-utils net-tools vim sudo tree npm && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.2/install.sh | bash
RUN pip3 install imutils 
ADD laps-counter.conf /etc/nginx/conf.d/defaul.conf
#USER webmaster
ADD cv-motion-detect.py /root/motion-detection/
WORKDIR /var/www
ADD index.html .
ADD Cheer.wav media/
