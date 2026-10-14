# NextColor Apps

The F-Droid repo at [apps.nextcolor.org](https://apps.nextcolor.org/). Open that page on your phone and tap **Add to F-Droid** to use it.

| App | Author | Source |
| --- | --- | --- |
| SnapCrop | [Vibecoder-jsx](https://github.com/Vibecoder-jsx) | [Vibecoder-jsx/SnapCrop](https://github.com/Vibecoder-jsx/SnapCrop) |
| Trolley Log | [ganyuke](https://github.com/ganyuke) | [ganyuke/TrolleyLog](https://github.com/ganyuke/TrolleyLog) |
| WikiMop | [ganyuke](https://github.com/ganyuke) | [ganyuke/WikiMop](https://github.com/ganyuke/WikiMop) |

The apps are built and signed in their own repositories by their authors. This repo downloads the APKs from their GitHub Releases and builds the F-Droid index from them.

## How it works

A GitHub Actions workflow (Publish) runs once a day and on every push. It first checks whether anything changed since the live version: this repo's app list, scripts, or page, or any app's releases or store listing. If nothing did, it stops there. Otherwise, for each app in `fdroid/metadata/` it:

1. Downloads the APKs from the app's GitHub Releases.
2. Checks each APK's attestation, to make sure it was built by a workflow in that app's repository. APKs without one are skipped with a warning.
3. Grabs the store listing from the app's `fastlane/` folder.
4. Builds the index with `fdroid update` and deploys it to GitHub Pages.

To publish right away, run the workflow by hand from the Actions tab. A run by hand always builds.

## Adding an app

The app's repository needs:

- GitHub Releases with a signed APK, attested with `actions/attest`. Drafts and pre-releases are ignored.
- A store listing in `fastlane/metadata/android/en-US/` with `title.txt`, `short_description.txt`, `full_description.txt`, and `images/icon.png`. Screenshots (`images/phoneScreenshots/`) and changelogs (`changelogs/<versionCode>.txt`) are optional.

Then add `fdroid/metadata/<app id>.yml` here, add the app to the table above, and push:

```yaml
Categories:
  - Internet
AuthorName: Name shown as the author
AuthorWebSite: https://example.org
SourceCode: https://github.com/owner/repo
IssueTracker: https://github.com/owner/repo/issues
Changelog: https://github.com/owner/repo/releases
License: MIT

AutoName: App name
```

`SourceCode` has to be the GitHub repository. That's where the APKs are downloaded from. `AuthorWebSite` and `License` can be left out.

It's fine to add an app that has no releases yet. It appears once it has one.

To remove an app, delete its `.yml` file.
