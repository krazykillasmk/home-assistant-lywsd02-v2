# Home Assistant - LYWSD02 Sync

## Overview

This is a fork of ```ashald/home-assistant-lywsd02```. In v2 version different method of synchronization was added (bleak-retry-connector), detailed logging and HA notifications after successful / failed synchronization. 

Original description: 

This integration allows to configure LYWSD02 e-Ink clocks via HomeAssistant bluetooth integration.
This means that you can leverage all your ESPHome Bluetooth proxies for best coverage.

See [./info.md](./info.md) for usage details.

## Installation

### With HACS
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)

You can use HACS to manage the installation and provide update notifications.

1. Add this repo as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories/):

```text
https://github.com/krazykillasmk/home-assistant-lywsd02-v2
```

2. Install the integration using the appropriate button on the HACS Integrations page. Search for "home-assistant-lywsd02".
