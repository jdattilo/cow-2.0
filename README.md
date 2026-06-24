# Cow

Live monitoring dashboard for the Cattle Suite. Shows running builds, cluster status, and active test activity in real time. Integrates with Jenkins/Bamboo and the AE2 test execution engines.

**What it does:**
- Displays live build and run activity across the cluster
- Integrates with Bamboo/Jenkins for CI build state
- Connects to AE2 test runners (bicyclops, butterjunk) for live test status
- Shows enqueued work and cluster health
- Provides log viewing for active and completed runs

**Stack:** Python, Django, JavaScript

---

## Cattle Suite

The Cattle Suite is a custom test automation and performance tracking platform built for Dell's proprietary server caching hardware. It managed builds, test runs, log collection, and performance reporting across physical server clusters. Dell open-sourced the full codebase when they shut down the division.

Suite components: [cattle](https://github.com/jdattilo/cattle-2.0) · [cow](https://github.com/jdattilo/cow-2.0) · [cowtracks](https://github.com/jdattilo/cowtracks-1.0) · [b2eb](https://github.com/jdattilo/b2eb-1.0) · [bicyclops](https://github.com/jdattilo/awesome-express-bicyclops) · [butterjunk](https://github.com/jdattilo/awesome-express-butterjunk)
