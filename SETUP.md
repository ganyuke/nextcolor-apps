# Setup

One-time setup for whoever runs this repo.

## Repo key

F-Droid clients remember the key the index is signed with. If the key changes, everyone has to remove the repo and add it again. Back up the key file and its password, and don't commit them.

```bash
keytool -genkeypair -alias repo -keyalg RSA -keysize 4096 -validity 10000 \
  -storetype PKCS12 -keystore nextcolor-repo.p12 -dname "CN=NextColor Apps"
```

Use RSA. With an EC key, `fdroid update` leaves the old index format unsigned and older clients reject the repo.

Add these as Actions secrets:

- `REPO_KEYSTORE_BASE64`: the output of `base64 -w0 nextcolor-repo.p12`
- `REPO_KEYSTORE_PASSWORD`: the password

## GitHub Pages

1. In Settings → Pages, set the source to GitHub Actions.
2. In your account's Settings → Pages, add `apps.nextcolor.org` as a verified domain and add the TXT record it gives you to DNS.
3. Point the `apps` CNAME at `ganyuke.github.io`.
4. In the repo's Settings → Pages, set the custom domain to `apps.nextcolor.org` and enable Enforce HTTPS when it becomes available.

A domain can only be on one repository at a time. Remove it from the old one first.

## Scheduled runs

GitHub disables scheduled workflows after 60 days with no commits and emails you about it. The site stays up but stops updating until you re-enable the workflow from the Actions tab.
