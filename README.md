# Make it so.

A deployment orchestrator for GitHub-hosted projects.

<img src="https://upload.wikimedia.org/wikipedia/commons/2/2e/Jean-Luc_Picard_2.jpg?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=original" alt="drawing" width="500"/>

## Login

Users log in with GitHub, and only active members of one GitHub team are let in. Set the team with `GITHUB_ORG` and `GITHUB_TEAM` (the team's slug from its URL, not its display name). If either is missing, nobody can log in.

Membership is checked once at login, so someone removed from the team keeps access until their session ends.

## Database setup & migrations

`make create_db && make upgrade_db` should be all that's needed to get started. Those two commands will create the database if it does not exist and run the migrations.

If any changes or additions are made in the `models` directory, run `make migrate ARGS='-m "<migration_title>"'` to create a new migration and then `make upgrade_db` to apply the migration to the database.

## Release

`make release` to follow conventional commits and semver
`yarn install && yarn release-it <the-version>` to set a specific version
