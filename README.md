# Make it so.

A deployment orchestrator for GitHub-hosted projects.

<img src="https://upload.wikimedia.org/wikipedia/commons/2/2e/Jean-Luc_Picard_2.jpg?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=original" alt="drawing" width="500"/>


## Database setup & migrations

`make create_db && make upgrade_db` should be all that's needed to get started. Those two commands will create the database if it does not exist and run the migrations.

If any changes or additions are made in the `models` directory, run `make migrate ARGS='-m "<migration_title>"'` to create a new migration and then `make upgrade_db` to apply the migration to the database.