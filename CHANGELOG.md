# Changelog

# 1.0.0-alpha (2026-10-07)

### Bug Fixes

* deploy job output ([38c36c2](https://github.com/bcgov/makeitso/commit/38c36c2a8ea05229e900a70f21dfe20330bf46e5))
* pin setup-uv to v10.2.0 in the test workflow ([0e70d81](https://github.com/bcgov/makeitso/commit/0e70d81887c15c60005d3f26633e4d09959be713))
* skip expensive queries for logged-out users on index route ([3992851](https://github.com/bcgov/makeitso/commit/3992851a0c6206e223f3144ca20f5e39ab73c426))

### Features

* add `engage` module for repository configuration parsing ([bab4efc](https://github.com/bcgov/makeitso/commit/bab4efc9097e536c4fe259629b510f2779f0a696))
* add allow_failures field to Stack model ([d1c7265](https://github.com/bcgov/makeitso/commit/d1c7265caf0c786d0386631d0ffba100c99fa025))
* add background job to sync GitHub commits and checks on stack creation ([ffad675](https://github.com/bcgov/makeitso/commit/ffad6750b25008acf895523fdcd57bc7bd451511))
* add background sync tracking with retry limits, manual sync override, and stale sync queuing ([5145f58](https://github.com/bcgov/makeitso/commit/5145f589640461ee550647f7a7fd92ca088cee4f))
* add CANCELLED and INTERRUPTED deploy statuses ([1c4f638](https://github.com/bcgov/makeitso/commit/1c4f638c58f7ba9f8e0e214a1ca2153cdb19a4c0))
* add environment-based configuration handling ([594b21d](https://github.com/bcgov/makeitso/commit/594b21d3e7647bbb82bb3682735ead5546d5cf4d))
* add Flask app skeleton ([d8fb4a6](https://github.com/bcgov/makeitso/commit/d8fb4a6d7dfe1bec598071351d7f5a34df6d2499))
* add GitHub layer for reading commits and check runs ([59f3e53](https://github.com/bcgov/makeitso/commit/59f3e53d963fccf1d997c141c532878a6b2c461a))
* add new deploy page ([7ed8206](https://github.com/bcgov/makeitso/commit/7ed8206b14dc1b618b020bf5a79677e94e796f1c))
* add pytest integration and test database configuration ([632b386](https://github.com/bcgov/makeitso/commit/632b3864d5c959ded71bc45320057537f5ff8872))
* add RQ callbacks to handle deploy success, failure, and stop events ([8373754](https://github.com/bcgov/makeitso/commit/8373754872e73d53389b10b2275fd13ab812b955))
* add separate workers for deploys and syncs ([d56d173](https://github.com/bcgov/makeitso/commit/d56d1737139a66d606ea7b58a2be2b7380025d18))
* add stack details page with commit list and sync button ([af6e607](https://github.com/bcgov/makeitso/commit/af6e607863f27ba7bf7eea08e4d5aeb71a62cc94))
* add stack settings page with lock and environment variable management ([d6af442](https://github.com/bcgov/makeitso/commit/d6af442204746bcdd40cddc197dc87ab4d3f40e4))
* display deployment states on main page with stack-specific details ([d2e7a5c](https://github.com/bcgov/makeitso/commit/d2e7a5cc40ce741c1c9a880ce68093b5fcb32aa4))
* implement stack deletion workflow with modal confirmation and archiving ([72286f6](https://github.com/bcgov/makeitso/commit/72286f6aac14e7d512c6305fe60e26658d4941a8))
* integrate Alpine.js for reactive UI elements ([ed48d93](https://github.com/bcgov/makeitso/commit/ed48d933654420f55659d45ea1998fa847859c06))
* integrate Flask-Bootstrap ([c2d4088](https://github.com/bcgov/makeitso/commit/c2d4088add33e94847af905039df76ba8b0828e9))
* integrate HTMX ([283bd78](https://github.com/bcgov/makeitso/commit/283bd7808c0ccc2311e38a531faa5cc5306fce5c))
* integrate RQ and Redis for background job processing ([fe4d01e](https://github.com/bcgov/makeitso/commit/fe4d01e72cfd4c35f2a6430b3096ccadbf378446))
* new stack form ([cadee12](https://github.com/bcgov/makeitso/commit/cadee1273784fa394264f7629e36a5559a83d35d))
* read engage.<env>.yaml for checklist, timeout and allowed CI failures ([6b9cc38](https://github.com/bcgov/makeitso/commit/6b9cc38ca668a1d34d08a82ce46402c517912175))
* run deploys in RQ workers with a live log saved to the database ([3bab1bc](https://github.com/bcgov/makeitso/commit/3bab1bc12d744a7ac5a309341266dc2c5ad5f483))
* split deploys and syncs into separate queues ([367f49d](https://github.com/bcgov/makeitso/commit/367f49dfa4090623ce6b7e23e2d14fa02edb826c))
* split stack page into deploying, undeployed and previous deploys with emergency mode ([73cc7dc](https://github.com/bcgov/makeitso/commit/73cc7dc9dcd51c6c56531b1b4c2e79019ccc062a))
* store GitHub commit details and check state on commits ([b53f6e7](https://github.com/bcgov/makeitso/commit/b53f6e7eed9e010add572ec0d711bfce8c6e0356))
* validate repository and branch on GitHub when creating a stack ([82d77c0](https://github.com/bcgov/makeitso/commit/82d77c0c1efb9728d7396b826e534afff0a7cd91))
