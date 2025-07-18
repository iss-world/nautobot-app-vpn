# Uninstall the App from Nautobot

Here you will find any steps necessary to cleanly remove the App from your Nautobot environment.

## Database Cleanup

Prior to removing the app from the `nautobot_config.py`, run the following command to roll back any migration specific to this app.

```shell
nautobot-server migrate nautobot_app_vpn zero
```

!!! warning "Developer Note - Remove Me!"
    Any other cleanup operations to ensure the database is clean after the app is removed. Is there anything else that needs cleaning up, such as CFs, relationships, etc. if they're no longer desired?

## Remove App configuration

Remove the configuration you added in `nautobot_config.py` from `PLUGINS` & `PLUGINS_CONFIG`.

## Uninstall the package

```bash
$ pip3 uninstall nautobot_app_vpn
```
