# ERPNext Bench

A development bench for ERPNext on the Frappe Framework. The Frappe and ERPNext source trees are included directly in this repository, so both can be customized and committed here without initializing submodules. See [MODULES.md](MODULES.md) for a module map and [docs/erpnext-modules](docs/erpnext-modules/README.md) for detailed diagrams.

## Clone

Clone this repository:

```bash
git clone https://github.com/vantoan2905/ERA_ERP.git
cd ERA_ERP
```

The `apps/frappe` and `apps/erpnext` directories are versioned as regular project directories in this repository. Edit either app directly and commit your customizations to this repository.

## Requirements and setup

Install the system dependencies and compatible versions of Python, Node.js, Redis, MariaDB, and the Bench CLI using the [official Frappe installation guide](https://docs.frappe.io/framework/user/en/installation). Follow the guide to set up the bench and create a site, then install the ERPNext app on that site.

## Repository contents

```text
ERA_ERP/
├── apps/
│   ├── frappe/                  # Frappe Framework source
│   └── erpnext/                 # ERPNext source
├── docs/erpnext-modules/        # Detailed module diagrams
├── tools/erpnext_seed/          # Demo and performance data generator
├── MODULES.md                   # Module overview
├── Procfile                     # Bench process definitions
└── patches.txt
```

Local sites, credentials, keys, generated assets, logs, process IDs, service configuration, and virtual environments are excluded from this repository. Create and configure a separate site and secrets for each development or production environment.

## Source code and licenses

Frappe Framework and ERPNext are separate projects, each with its own license and Git history. When distributing a combined project or public fork, retain the copyright notices and comply with each component's terms. The repository's [LICENSE](LICENSE) applies to the files in this repository; each submodule retains its own license.
