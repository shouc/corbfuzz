### Building (Docker)

Make sure docker has been installed on your computer and you are running as root. This would take ~10 minutes on [our computer](https://github.com/shouc/corbfuzz/blob/master/REQUIREMENTS.md#our-computer) (P.S. to optimize performance, you can update line 51 in `build.sh` `make -j30` to `make -j{how many processors you have}`).

Notice that you **must** add `--shm-size=6g` so that there is enough memory for the fuzzer. 

```bash
docker build . -t corbfuzz
docker run  --shm-size=6g --name corbfuzz1 -ti corbfuzz # tapping into docker container
```

If you instead want to use our [pre-built docker image](https://hub.docker.com/repository/docker/shouc/corbfuzz), you can instead replace previous procedure with 
```bash
docker run  --shm-size=6g --name corbfuzz1 -ti shouc/corbfuzz:latest
```

### Building (Ubuntu)

The setup script has been tested on Ubuntu 20.10, make sure you are running as root.

If you don't have Chromium & chromedriver on your computer, following script downloads Chromium and setup it up:
```bash
./install_chrome.sh
```

Following script installs all dependency required by the fuzzer, build the instrumented PHP, and setup the environment.
```bash
./build.sh
```