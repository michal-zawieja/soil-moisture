FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye

# install usbutils and clean up afterwards to reduce image size
RUN apt-get update \
    && apt-get -y install usbutils udev \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*