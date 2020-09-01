# SignMyProfile
Source Code for SignMyProfile

# How to Use

You can get a custom badge for your GitHub README from shields.io that displays how many people have signed your profile. You also get to see who has on the SignMyProfile homepage!

[Visit the SignMyProfile homepage here](https://smp.maxbridgland.com)

How the badge works:

Example

[![](https://smp.maxbridgland.com/badge?target=34947910)](https://smp.maxbridgland.com/sign/34947910)

```
[![](https://smp.maxbridgland.com/badge?target=GITHUB USER ID)](https://smp.maxbridgland.com/sign/GITHUB USER ID)
```

You can go to https://smp.maxbridgland.com/ to get your badge!

This uses Login with Github to get your Username, Avatar, and Display Name. It will use GitHub to authenticate and an OAuth2 token with **ONLY** user:read scope is generated. The tokens generated from SMP cannot modify/delete any data on your profile!

# Development

- Python 3.6+
- Flask
- MongoDB

Requires a `config.json` file in the root directory:

```json
{
    "MONGO_URI": "",
    "GH_CLIENT_ID": "",
    "GH_SECRET_KEY": ""
}
```

Self-explainatory

