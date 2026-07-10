# COW

COW is the cluster-side agent of the Cattle Suite, the distributed test harness I built at Dell for the Fluid Cache team. Every test cluster got its own COW: a Django app that registers the cluster's member nodes, watches their health, queues test jobs, installs the AE2 execution engine, drives runs against the hardware, and reports everything it sees back up the chain. Its dashboard panels say it plainly — Cluster Monitoring, AE2/Automation Management, Monitor Testing (the templates literally title themselves "COW AGENT"). If CATTLE was the ledger of record, COW was the ranch hand actually out with the herd.

## The Cattle Suite

The suite ran the test floor for Dell Fluid Cache: real builds, on real server clusters, with real hardware failures to catch. Six repos cover the five components:

| Component | Repo | Role |
|---|---|---|
| CATTLE | [cattle-2.0](https://github.com/jdattilo/cattle-2.0) | central dashboard — branches, commits, builds, runs, sitreps |
| COW | this repo | per-cluster agent — cluster registry and health, job queue, AE2 orchestration |
| COWTRACKS | [cowtracks-1.0](https://github.com/jdattilo/cowtracks-1.0) | distributed log collection and viewing |
| B2EB | [b2eb-1.0](https://github.com/jdattilo/b2eb-1.0) | datacenter hardware inventory and cluster registry |
| AE2 | [awesome-express-bicyclops](https://github.com/jdattilo/awesome-express-bicyclops) / [awesome-express-butterjunk](https://github.com/jdattilo/awesome-express-butterjunk) | test-execution engine (Dell shipped both lab variants in one archive) |

## Provenance

I built this at Dell between 2014 and 2016 as a Senior Software Engineer on the Fluid Cache team, and I wrote essentially every line of it — years before AI coding assistants existed, so nobody has to wonder about that part. When the Dell–EMC merger wound the division down, I drove the legal process to get the suite released to the public. On May 12, 2016, Dell published it officially as **OpenPastures** (yes, the team's cow jokes made it all the way into the release name):

- <https://opensource.dell.com/releases/openpastures/> — `AE2.zip`, `b2eb.zip`, `cattle.zip`, `cow.zip`, `cowtracks.zip`, all stamped 2016-05-12
- <https://opensource.dell.com/releases/FluidCache/> — Dell open-sourced Fluid Cache itself as well

### Verify it yourself

Why trust a README when the receipts sit on Dell's own server? Download Dell's archive and diff it against this repo:

```bash
curl -LO https://opensource.dell.com/releases/openpastures/cow.zip
unzip cow.zip -d openpastures
git clone https://github.com/jdattilo/cow-2.0 && cd cow-2.0
diff -rw --strip-trailing-cr --exclude=.git --exclude=README.md ../openpastures/cow .
```

What you should see: the same apps, models, views, and URLs, with differences confined to mechanical PEP8 reformatting — long lines re-wrapped, imports split one per line, a `test_pep8` static-analysis hook added in `settings.py`. This mirror came from my working copy, which carries an automated PEP8 cleanup pass that Dell's snapshot does not (the code underneath is the same code). Dell's zip also captured some runtime debris this repo skips — a `logs/` directory plus `static/env_files/` and `static/suite_files/` working folders. If you want a byte-for-byte anchor, the two AE2 repos match Dell's archive exactly.

## Author

Joseph Dattilo — [josephdattilo.com](https://josephdattilo.com/) · [open-source portfolio](https://josephdattilo.com/open-source/) · [github.com/jdattilo](https://github.com/jdattilo)

## License

GPL-3.0. The `LICENSE.txt` in this repo is byte-identical to the one Dell shipped in every OpenPastures archive — run `md5sum LICENSE.txt ../openpastures/LICENSE.txt` and compare; both come out `9c25e1cdc3b5122842a6a70fab49a522`.
