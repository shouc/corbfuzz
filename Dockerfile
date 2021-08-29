FROM ubuntu:20.10
RUN mkdir /corbfuzz
WORKDIR /corbfuzz
COPY . .
RUN ./install_chrome.sh
RUN ./build.sh
