# spacecost

Cited reference tables for space-mission cost and mass estimation. Five tables,
every row carrying an inline citation and a `reference_year`, plus the
derivations that turn them into the numbers a trade study actually needs.

```bash
pip install git+https://github.com/loggger101/spacecost
```

```python
import spacecost

v = spacecost.load_launch_vehicles()
v.sort_values("usd_per_kg_to_leo")[["name", "usd_per_kg_to_leo"]].head()

# What does it cost in propellant to move 1 kg of payload through 6,500 m/s?
spacecost.cost_per_dv_usd_per_kg(
    propellant_cost_usd_per_kg=20.0, isp_s=452, delta_v_m_per_s=6_500)
```

```bash
spacecost show vehicles -n 10
spacecost propellant 6500          # rank propellants by fuel cost for a delta-v
spacecost build -o ./out           # write all six CSVs
```

## What is in it

| table | rows | holds |
|---|---|---|
| `launch_vehicles` | 36 | $/kg to LEO, GTO and escape, payload masses, fairing volume, list price, status |
| `propellants` | 41 | vacuum Isp, bulk density, $/kg and $/L, storage class, derived tankage, thruster device |
| `delta_v_segments` | 33 | m/s and trip duration per trajectory leg, 100 to 10,500 m/s |
| `operational_costs` | 44 | $/mission-year and $/kg-payload lines, with low/high bands |
| `storage_systems` | 20 | how a kilogram is held, across the cargo, depot, propellant and energy domains |

The launch table spans **17 operational** vehicles, 9 in development, 8 concepts
and 2 retired, from a lunar mass driver at a notional $10/kg to LEO up to SLS
Block 1B at $39,048/kg. The propellant table spans 15 propulsion types, from
cold gas at 70 s to speculative concepts at 10^5 s, across 8 storage classes.

Concept and retired rows are present **and marked**. Filter on `status` if you
want only things that fly; the speculative rows are there so a study can say
what it excluded rather than silently not having it.

## The three things it does that a spreadsheet of prices does not

**Tank mass is derived, not asserted.** A tank scales with the VOLUME it
encloses, not the propellant mass inside it, which is why LH2 at 0.0708 kg/L
costs fourteen times the tank per kilogram burnt that kerolox at 1.015 does.
`_tank_kg_per_L` derives kg of tank per litre per storage class from a
thin-walled pressure vessel, anchored on flight articles (Shuttle ET at 0.0129
kg/L, Falcon 9 second stage at 0.033, Centaur III at 0.035), with COPVs sized
off a burst performance factor instead. Hydrolox lands at 9.7% of propellant
mass against Centaur's measured ~9.7%. An unknown storage class **raises**
rather than defaulting, because a silent default is how a new propellant gets a
free ride.

**The thruster is separate from the propellant.** A propellant row carries Isp;
a *device* row carries kg per newton, efficiency, and whether thrust scales
`continuous` (one bigger thruster) or `replicated` (n thrusters, so mass grows
linearly with thrust). Fourteen electric rows are continuous and three are
replicated. Sizing a micronewton device as a ten-newton cargo tug is the
specific failure that separation prevents, so `load_propellants` raises on an
electric row with no device entry rather than defaulting.

**Bipropellants are blended, not tabulated.** Isp, density, cost and tankage for
a mixture are computed from the components at the stage O/F ratio, with fuel and
oxidiser tankage summed over their own volumes rather than averaged. That is the
whole reason methalox is treated better than hydrolox: LOX and LCH4 share a
thermal class, LOX and LH2 do not.

## Two numbers, and they are not the same number

| | what it is | when it moves |
|---|---|---|
| `SpacecostConfig.pipeline_version` | the **data contract**, stamped into every CSV | any row changes |
| `spacecost.__version__` | the **package release** | a loader fix, a new helper, a docs pass |

A package release can leave the data contract alone. A change to any row must
move it. **The rule is one-directional**: moving `pipeline_version` is not
evidence that a number changed. Pin against `pipeline_version` when you care
about reproducing a result; pin against `__version__` when you care about an
API. `CHANGELOG.md` is the record for both.

## The output is a contract

`build_catalog()` writes six CSVs, and the guarantee is not the same for all
six. Which one applies depends on whether a file contains a computed float:

| | contract | why |
|---|---|---|
| the five reference tables | **byte identical, every platform** | no arithmetic; every value is a table entry passed through |
| the composite summary | **the same values, to a few ULP** | three columns of rocket equation, so `exp()` is involved |

The tables feed a model whose releases are argued from bit-identity, so what is
promised there is not "the same numbers" but the same bytes, and a tolerance
would hide the drift the check exists to catch. The summary cannot be promised
that by anyone: `exp()` is the platform libm and numpy picks SIMD kernels per
architecture, and neither is required by IEEE 754 to be correctly rounded. CI
demonstrated it on the first push, where Linux 3.9 and 3.12 agreed with each
other and 3.14 did not, which is a numpy version choosing different kernels
rather than an OS difference. Its byte hash is therefore recorded with the
platform it was taken on and checked only there.

`tests/test_parity.py` is both contracts as tests.

```bash
pip install -e ".[test]"
pytest -q
```

Two details of the writer are load-bearing and must not be tidied away:

- **The CRLF line terminator is pinned.** `pandas.to_csv` defaults
  `lineterminator` to `os.linesep`, and the committed hashes are hashes of
  CRLF. Unpin it and a byte-perfect Linux build reports DIFFER on every file
  with every value identical. It reads on Linux like a Windows leftover. It is
  not one.
- **There are TWO provenance columns**, `pipeline_version` and `catalog_date`.
  Strip both before comparing two builds. Stripping only the first and letting
  midnight fall between two runs produces a difference that looks exactly like a
  defect in whatever ran second.

`build_catalog(cfg, catalog_date="2026-09-07")` pins the second one, which is
what makes a comparison a comparison of tables rather than of clocks.

## Live prices are opt-in

Three propellants have a traded commodity analogue: RP-1 via NY heating oil
(`HO=F`), methane via Henry Hub natural gas (`NG=F`), with WTI crude (`CL=F`) as
an upstream cross-check. `spacecost build --live`, or
`SpacecostConfig(use_yfinance=True)`, fetches them and sets `price_basis` to
`live` on those rows.

**It is off by default**, which is a deliberate change from the upstream module
where it was on. A library that reaches for the network when you ask it for a
launch price is a library that is not reproducible, and every committed
reference file here is an offline build. Requires the extra: `pip install
"spacecost[live]"`.

## Provenance

These tables were built over fourteen releases as **Module 3 of
[economicspace](https://github.com/loggger101/economicspace)**, an asteroid
mining profitability pipeline, and extracted at `pipeline_version` 1.14.0
(commit `b0b18b2`). Two thirds of that module was annotated reference data and
nothing in its schema knows what an asteroid is, which is the argument for
splitting it out: a launch price is useful to anyone costing a mission.
economicspace consumes this package as its Stage 3.

The extraction was done by slicing source line ranges rather than re-typing
anything, so every citation survives byte for byte, and the parity test is the
evidence that it changed nothing. What did change, and all it changed:

- the package no longer prints on import, or creates a directory on import
- `use_yfinance` defaults to `False`
- output defaults to `./spacecost_data`, reading `SPACECOST_OUTPUT_DIR`
- `build_transportation_catalog` is now `build_catalog` (the old name is kept
  as an alias)

## Reading the tables without Python

`reference/` holds the five tables as committed CSVs, so `curl` and a
spreadsheet are enough. The sixth file, the composite
`transportation_summary.csv` cross-joining vehicle x segment x propellant, is
7.4 MB and is **not** committed. `reference/summary_sample.csv` is a 411-row
stride sample of it at full precision, and `reference/summary_meta.json` records
its row count, its hash and the platform that hash was taken on. `spacecost
build` rebuilds the whole thing.

## What it does not do

It does not fly a trajectory. `delta_v_segments` holds representative means per
leg; if you need a real transfer you want a Lambert solver and an ephemeris, and
this is the table you price the answer with afterwards.

It does not know today's price. Every row carries `reference_year` precisely so
staleness is visible; most are 2026. Launch pricing in particular moves.

The surface delivery figures are **marginal-transport lower bounds**: no
non-recurring engineering, no programme overhead, no cadence limit. They answer
"what could this cost at industrial scale", not "what would this cost today".
Real CLPS lunar delivery is roughly $1M/kg at ~100 kg scale.

## Citations and licence

MIT, see `LICENSE`. Every source behind every row is listed in
`CITATIONS.md`, and the row's own `notes` field is the authority for its number.
None of the sources feeding these tables imposes a condition of use; the three
that do so upstream in economicspace are all catalog sources, and none of them
is here.
