# Changelog

Two version numbers live in this project and they mean different things. Read
[the README](README.md#two-numbers-and-they-are-not-the-same-number) before
assuming a bump here moved a value.

    pipeline_version        the DATA contract, stamped into every output CSV
    spacecost.__version__   the PACKAGE release

**The rule is one-directional: changing any row means bumping
`pipeline_version`, and bumping it is NOT evidence that a row changed.** Nothing
may read a version as proof that a number moved.

## Package releases

### Unreleased

**Tests only; no name, table or number moved, so no release is cut for it.**
`tests/test_consumer_contract.py` now lists what economicspace actually reads,
as of its master v1.36.0. It had mirrored that repo's Stage 3 adapter, which
re-exported most of `__all__`; the adapter now re-exports only what something
there reads, and the list follows it:

- **dropped**, because nothing in economicspace reaches them: `LITRES_PER_GAL`,
  `LITRES_PER_BBL`, `COMMODITY_DENSITY_KG_PER_L`, `load_storage`,
  `propellant_mass_for_dv`, `cost_per_dv_usd_per_kg`,
  `build_transportation_summary`, `cheapest_launch_to`,
  `mission_cost_breakdown`. They stay public here; they are simply no longer a
  promise to that consumer.
- **added**, because economicspace's Stage 2 reads them and the list had missed
  them since v0.4.0: `LEO_LAUNCH_VEHICLE`, `delivery_mass_ratio`,
  `delivery_hardware_usd_per_kg`, and `ENVIRONMENTS_REFERENCE`.
- **new**, `SUBMODULE_SURFACE`: four names reached through a submodule, which
  neither `__all__` nor the wheel check can see (`delivery`'s three hardware
  rates, read by the worked calculation, and `prices.merge_propellant_prices`,
  read by `verify_stage3.py`).

### 0.4.0 - 2026-09-23

**The launch table, re-audited and more than doubled: 36 rows to 76, every
figure given a stated range with the headline at its centre, and a new
delivered-price model built on it.** Data contract **1.15.0 → 1.16.0**, and
VALUES moved, so this is the direction of the rule that obliges the bump.
`operational_costs` gains one row (below). The other four tables are
value-for-value identical apart from their `catalog_date` and
`pipeline_version` stamps.

🚨  **This release re-prices economicspace in BOTH Stage 2 and Stage 3.**
Stage 2: every in-space price comes from `delivered_cost_usd_per_kg`, and that
model changed (next section). Stage 3: the launch CSV, the cross-join summary
(39,852 → 84,132 rows) and every $/kg a Module 4 ranking reads have moved. The
20-cell campaign and its frozen `campaign/stage2/` prices were measured under
0.3.x, so nothing measured there compares across this release until it is
re-run. `delivered_cost_usd_per_kg(dest, 4253.0, stage_hardware=False)`
reproduces every 0.3.x delivered price bit for bit, which is what re-deriving
an old result needs. `downleg_cost_usd_per_kg` did not move.

#### Delivered prices: a new model, chosen for today's market

`delivered_cost_usd_per_kg` is the launch cost a kilogram already in space
avoids, and it is the miner's REVENUE. Two things were wrong with it. Both are
fixed against **today's** market, reading the same central figures as the
rest of the package: each launch row's headline and each cost row's `value`.

- **The LEO price was Falcon 9 (reusable) at $4,253/kg, chosen as "the
  cheapest operational figure", which it never was.** It is now whatever a
  stated rule selects: operational, `open`, priced by the launcher itself
  (`published` or `contract`), lowest headline `usd_per_kg_to_leo`. That is
  **Falcon Heavy (expendable), $2,414/kg**, SpaceX's $150-159M for 63.8 t. New
  Glenn's $1,922 is excluded because the bottom of its range is a rival's
  estimate; Starship because it does not fly. The rule is asserted at import, so a table edit
  that changes the winner fails loudly instead of re-pricing every
  destination. New exports: `LEO_LAUNCH_VEHICLE`, `leo_anchor_candidates()`.
- **Every stage a chain expends was charged for its launch and never for
  being built.** `delivery_hardware_usd_per_kg()` now charges tug dry mass at
  the new `Expendable upper stage recurring cost` row, lander dry mass at
  `Surface lander recurring cost`, what an entry discards at the TPS rate, and
  the propellant at the hydrolox price, each at its row's `value`.

| destination | 0.3.x | 0.4.0 | of which hardware |
|---|---:|---:|---:|
| `leo` | 4,253 | 2,414 | 0 |
| `geo` | 12,526 | 8,046 | 937 |
| `cislunar` | 10,810 | 6,878 | 742 |
| `mars_orbit` | 13,496 | 8,706 | 1,046 |
| `lunar_surface` | 21,210 | 42,635 | 30,597 |
| `mars_surface` | 45,105 | 184,811 | 159,209 |

Orbital destinations fall about a third; the two surfaces rise steeply,
because a lander ($200k/kg) and an aeroshell ($50k/kg) were being thrown away
for free. Two new tests hold the result
against the market: GEO may not exceed buying GTO directly and flying only the
apogee burn, and cislunar may not exceed the cheapest direct escape launch.
`delivered_cost_usd_per_kg` gains `stage_hardware=True`; with it `False` the
function is linear in `leo_usd_per_kg` again, as before.

⚠️  **Still a lower bound, and meant to be.** No NRE, no programme overhead,
and a hydrolox tug nobody sells as a product yet. Lunar surface at $42,635/kg
sits against real CLPS delivery at roughly $1M/kg.

New `operational_costs` row **`Expendable upper stage recurring cost`**,
$4,800/kg of stage dry mass: the geometric centre of a range from $1,750
(Falcon 9's mass-produced kerolox stage, $7-10M on ~4 t) to $13,400 (Centaur
III, the hydrolox stage the chains actually fly, built at a low rate).

**Falcon Heavy (reusable)'s optimistic 57 t LEO is removed.** It had no
source, and a headline centred on an unsourced end would carry the error into
every figure derived from it. Its band collapses onto 30 t.

#### Errors fixed in existing rows

These were wrong rather than stale. Each row's `notes` now says what it used
to carry.

- **SLS Block 1B** was `operational`; it never flew, and NASA cancelled it
  with the Exploration Upper Stage in Feb 2026. Now `concept`. Its $4.1B
  was NASA OIG's per-Artemis-flight figure *including Orion*; it now carries
  the launch-only $2.5-2.8B. Its 41 t GTO had been scaled, not published, and
  is gone. **SLS Block 1**, which has flown twice, is added.
- **Zhuque-3** carried 21 t / 18.3 t LEO, which are the figures for the
  enlarged ZQ-3E. The ZQ-3 that flies lifts 8 t reusable (11.8 t expendable).
  Promoted to `operational` after two successful orbital flights.
- **Terran R** paired its 33.5 t *expendable* LEO with a reusable price; now
  23.5 t. **Nova** carried 5 t as fully reusable; the figure is 3 t.
- **Vulcan VC6** was priced at $110M, which is ULA's *starting* price for the
  smallest configuration. Its 7,200 kg "escape" was the GEO payload. And it
  has never flown (every Vulcan to date was VC2S or VC4S), so it drops from
  TRL 9 to 8 while staying `operational` as a configuration of a flying
  vehicle.
- **PSLV-XL** carried 1,100 kg to escape. Chandrayaan-1 and the Mars Orbiter
  Mission were both put into Earth orbit and raised themselves; now 0.
- **H3 (24L)** cited the ¥5B target, which is for the H3-30.
- **Soyuz-2.1b** GTO was the Kourou figure; Soyuz has not flown from Kourou
  since 2022.
- **Atlas V** is still `operational` but ULA stopped selling it in 2021; it is
  now marked `sold_out`.
- Prose: LVM3 was called human-rated (Gaganyaan has not flown crew); H-IIA was
  "49 flights" (50); New Glenn's "3 successful flights" omitted that NG-3 left
  its payload in the wrong orbit.

#### Every figure is a range, and the headline is its centre

Where a source gave a range, the row used whichever end was to hand, which for
New Glenn was the LOW price. Every row now states either one figure, where the
source gives one, or the low and high ends of a credible range, and a ranged
headline price and payload are DERIVED as the range's geometric centre,
`sqrt(low x high)` to three significant figures (`vehicles.band_centre`). A
narrow range barely moves; a wide one lands in the middle rather than at an
end. Geometric rather than arithmetic, because launch prices are uncertain by
factors: the Shuttle's $450M-$2.1B centres at $972M, not $1.28B.

The ranges themselves lean conservative, and that is where the conservatism
now lives: a target (anything not yet flying) is always the optimistic end,
never the headline. The largest LEO moves: Zhuque-3 $1,429 → $4,425/kg,
Starship $900 → $1,603 (a 35-100 t range, from what Block 2 delivered to the V3
target), Falcon Heavy reusable $1,702 → $3,333 (30 t, since SpaceX publishes no
LEO figure for that mode), Vega C $11,212 → $16,581, New Glenn $1,511 → $1,922.
Starship's `tanker_flights_for_escape` stays at 12, the centre of the 8-16
quoted. The full value-by-value list is recoverable with a `git diff` of
`reference/launch_vehicles.csv`.

#### 40 new rows

Configurations people actually price: Falcon 9 and Falcon Heavy expendable,
Vulcan VC2 and VC4, H3-30. Flying vehicles that were missing: SLS Block 1,
Minotaur IV, Soyuz-2.1a, Angara A5, Proton-M, Spectrum, GSLV Mk II, SSLV, Nuri,
Long March 2C, 2D, 3B/E, 4C, 6A, 8A, 10B and 12, Kuaizhou-1A and -11, Ceres-1,
Gravity-1, Kinetica-1 and -2, Jielong-3, Zhuque-2E, Pallas-1. In development:
New Glenn 9x4, Soyuz-5, Epsilon S, Hyperbola-3. Retired, for the historical
figures a reader will meet: Pegasus XL, Ariane 5 ECA, Vega, Space Shuttle,
Saturn V.

**Deliberately not added**, for want of a price or payload worth citing:
Angara-1.2, Antares 330, Long March 11, 12A and 12B, Hyperbola-1, Ceres-2,
RFA One, Astra Rocket 4, and the Iranian and North Korean launchers, which are
not a market.

#### Schema: 20 new columns on `launch_vehicles.csv`

Appended after the existing 18, so no existing column moved position.

- `country`, `availability` (`open` / `restricted` / `government_only` /
  `sold_out` / `unavailable`), `reusability`, `core_propellant`,
  `first_flight_year`, `price_basis`.
- `list_price_usd_low` / `_high` and `payload_{leo,gto,escape}_kg_low` /
  `_high`.
- `usd_per_kg_to_{leo,gto,escape}_low` / `_high`, derived.

⚠️  **`usd_per_kg_to_*` is now DERIVED at import, not typed.** A row that
types one raises. So does a headline outside its own band, a vocabulary typo,
an unknown key, or a row that does not state `availability`.

⚠️  **`payload_gto_kg` and `payload_escape_kg` are now float columns.** A
payload of NaN means "no figure published", which is not the same as 0, "does
not go there", and a column holding NaN cannot be int64. The CSV writes
`5500.0` where it wrote `5500`. `first_flight_year` is nullable `Int64`, so it
writes `2010`, or nothing for a vehicle that has not flown.

#### API

- `cheapest_launch_to(..., purchasable_only=False)` and `spacecost launch
  --open-only`: keep only `availability == "open"`. Off by default.
- `validate` holds the launch price and payload bands to the same
  inside-its-own-range rule as `operational_costs`.
- `tests/test_delivery.py` pinned `DATA_VERSION == "1.15.0"` as a stand-in for
  "delivery is not an output". It now checks that directly.

### 0.3.2 - 2026-09-22

**A test fix, and it is a fix to the CONTRACT rather than to a number.** No
package code changed, no value moved, the data contract stays 1.15.0.

#### 🚨 0.3.1's tests claimed a cross-platform guarantee this package declines to make

`tests/test_delivery.py` asserted `==` on every platform. CI went red on the
first push, on `lunar_surface` and nothing else: Linux returns
`21209.958393766807` where Windows returns `21209.9583937668`. One ULP.

That was not a defect in `delivery.py`. It was the wrong contract, and this
package already had the right one written down. [The output is a
contract](README.md#the-output-is-a-contract) says the six reference tables
are byte identical on every platform BECAUSE they pass values through, and the
composite summary is promised only "the same values, to a few ULP" BECAUSE it
runs through `exp()` -- the platform libm, which IEEE 754 does not require to
be correctly rounded. **Every number in `delivery.py` is a mass ratio, so
every number in it is `exp()`.** The tests were written to the consumer's
bit-identity standard and imported it into a package that says, in its own
README, that it cannot promise that here.

⚠️  **`lunar_surface` failing ALONE is the tell.** It is the only chain with
two burns at different dry-mass fractions, so it compounds the most rounding;
the single-burn chains happened to land on the same float. A cross-platform
claim that holds for six of seven cases is a claim that has not been tested.

✅  **Fixed with `test_parity.py`'s own pattern rather than a new one**: exact
on the platform `reference/summary_meta.json` was recorded on, and a 1e-12
relative tolerance elsewhere. Not a relaxation -- on the recording platform it
is the same exact comparison, and the tolerance only applies where an exact
one would assert something `exp()` cannot deliver.

⚠️  **The tolerance was chosen against the smallest REAL change this module
could suffer, not by eye.** Deriving `TUG_ISP_S` is the smallest at **2.96%**;
1e-12 sits nine orders of magnitude below that and four above the observed
libm spread. Proved by feeding the checker the actual value CI returned (it
passes), the value the Isp swap would give (it fails), a 1e-9 drift (fails)
and a 1e-15 one (passes) -- and by confirming the exact comparison still bites
on the reference platform.

⚠️  **economicspace is unaffected and does not have to move for this.** It
runs on the reference platform, its own bit-identity is unchanged and
independently verified, and it does not run this package's test suite. The
repin to 0.3.2 is so the tag it pins has a green suite, not because anything
it computes changed.

### 0.3.1 - 2026-09-21

Data contract unchanged at **1.15.0**, no value moved, every `delivery` output
bit-identical to 0.3.0. An audit of what the module DERIVES against what it
merely states.

#### Four more lookups

The downleg departure burns were all typed at 0.3.0 on the argument that two
of six had no row. Four of them do, so four of them are lookups now:
`cislunar` off `TLI -> NRHO insertion`, `mars_orbit` off `1-sol Mars orbit ->
Earth (TEI)`, `mars_surface` off the ascent-plus-TEI pair, and the 1,870 m/s
ascent component of `lunar_surface` off the descent row it is symmetric with.

**Deriving what agrees and typing what does not is right; typing all six
because two could not be derived was not.** That is the sharper version of the
0.3.0 note, and the correction is worth having: a blanket exception is how a
register stops being a decision.

#### 🚨 `TUG_ISP_S` is 465 s and this package's hydrolox row says 452

The chains fly a **465 s** cryogenic upper stage. `PROPELLANTS_REFERENCE`
carries hydrolox at **452 s**, the RS-25 / RL-10 datasheet figure. 465 is the
top of the 450-465 s band an upper STAGE is quoted over, which is the right
figure for a tug and is what the consumer's published in-space prices were
computed with.

⚠️  **Deriving it is a model change, not a refactor.** Measured: swapping 465
for 452 moves the delivered price **+2.96% cislunar, +3.29% geo, +3.63%
mars_orbit, +3.65% mars_surface, +5.21% lunar_surface**. Those are published
downstream. Left as it is; **the discrepancy is asserted at import instead**,
so the row cannot move under the comment that describes it.

The same treatment is now applied to the GEO deorbit burn, which is 1,490 m/s
against a row of 1,488: typed, and pinned to the row it disagrees with.

#### A register, because a derivation claim decays one literal at a time

`tests/test_delivery.py` reads the module's **source** and requires every
numeric literal to be either algebra (`0` and `1`) or a row on `TYPED` saying
which table cannot supply it. No test of the outputs can catch this: a
hardcoded 3,600 and a looked-up 3,600 give identical numbers and identical
hashes right up until the row moves and only one follows.

⚠️  **Both halves are findings.** A literal with no row is a value that
stopped being derived; a row with no literal is a permission still granted for
a number that has gone. Proved by planting one of each, and by planting a
literal that changes no value at all -- the case the import assertions cannot
reach.

### 0.3.0 - 2026-09-21

Data contract `pipeline_version` **unchanged at 1.15.0**, and that is the
headline rather than a footnote: `build_catalog()` writes the same seven CSVs
byte for byte, `reference/` needed no regeneration, and **economicspace does
not have to re-run Stage 3 for this.** A repin is enough. The rule is
one-directional and this release is the other direction: new code, no new data.

#### A seventh module: `delivery`, the staged leg chains

Moved out of economicspace's `modules/mineral_value.py` (Stage 2), where it had
lived since that module's v1.2.0. It answers two questions:

- `delivered_cost_usd_per_kg(dest)` — the launch cost a kilogram already in
  space avoids, walked backwards through a chain of real stages.
- `downleg_cost_usd_per_kg(dest)` — capsule, TPS, a share of the recovery
  campaign, and the departure burn that has to carry all three.

plus `delivery_mass_ratio` and `stage_mass_ratio`, and the constants behind
them: `DELIVERY_CHAINS`, `DOWNLEG_DEPARTURE_DV_M_S`, `LEO_LAUNCH_USD_PER_KG`,
`MARS_LANDED_MASS_FRACTION`.

**Why here.** The block it came from opened by admitting what it was: *"Constants
below are cross-referenced to Module 3. They are duplicated rather than
imported because Module 2 runs BEFORE Module 3 in the pipeline order … If you
change one of these, change it in Module 3 too."* Nine numbers retyped by hand
under a manual-sync instruction. That justification was concatenation order,
and it stopped applying the moment Stage 3 became this package: a pip-installed
package has no position in a pipeline. Nothing in the block knows what an
asteroid is.

**Every chain delta-v is now a lookup, not a literal.** `DELTA_V_REFERENCE` is
the single authority for all nine, and `tests/test_delivery.py` fails if a
literal creeps back in.

⚠️  **The downleg delta-v are typed, and that is deliberate.** Four of six
agree with a row exactly; a LEO deorbit burn has no row at all, and the GEO
figure disagrees with `GEO -> Earth (deorbit to entry)` by 2 m/s. Deriving all
six uniformly would have moved two published prices under a release that claims
to move none. They stay as literals with the mismatch tabulated beside them.
**Reconciling those two is a real question and a separate release**, because it
changes what a kilogram of platinum is worth at GEO and in LEO.

⚠️  **`math.exp`, not `np.exp`.** `rocket.py` is the vectorised entry point and
this is the scalar one, and they are not interchangeable: the consumer argues
its releases from bit-identity and the two libraries may round the last bit
differently. Do not unify them.

**Pinned bit-exact.** `tests/test_delivery.py` holds all fourteen headline
values to full `repr` precision, captured by running the original
implementation before a line was edited — not a regression net taken
afterwards. An exact `==`, because a tolerance would defeat the purpose.
Proved able to fail by perturbing the arithmetic, typing a literal into a chain,
and collapsing the `None`/`[]` distinction.

⚠️  **CONSUMER SURFACE WIDENED, and it is a new shape.** Four names joined
`tests/test_consumer_contract.py`, and they are imported by economicspace's
**Stage 2**, not its Stage 3 adapter. Stage 2 is the first stage to reach this
package, so a name dropped here now fails a pricing stage that runs before the
adapter does, and the traceback will not mention Stage 3.

⚠️  **REPIN economicspace**, in the FIVE places it now types the tag:
`requirements.txt`, `_MASTER_PIP_SPEC` in `build_master.py`, `_PIP_SPEC` in
`modules/transportation.py`, the same in `modules/mineral_value.py` (new with
this release), and the README sentence naming it.

### 0.2.0 - 2026-09-17

Data contract `pipeline_version` **1.14.0 → 1.15.0**. A sixth reference table
was added, so **every output CSV changed**: the stamp is a column and it moved
on all of them. No pre-existing VALUE moved — the five inherited tables are
byte identical to the 1.14.0 build once the two provenance columns are
stripped.

⚠️  **REPIN economicspace.** It installs this package from a pinned tag in
`requirements.txt` and `_MASTER_REQUIRED`, and until that tag moves it keeps
building against 1.14.0. See [Changing a row](README.md#changing-a-row).

⚠️  **The recorded reference platform for the summary hash moved**, from Python
3.14 / numpy 2.5.2 / pandas 3.0.5 to Python 3.13 / numpy 2.2.6 / pandas 2.3.3,
because that is the machine this release was cut on.
`transportation_summary.csv` runs through `exp()`, so its byte hash belongs to
a host, and `test_summary_hash_on_the_reference_platform` skips anywhere else.
To record it on the older environment instead, run `python
tools/refresh_reference.py` there before tagging. It does not affect the six
reference tables, which are byte identical on every platform and checked on
every CI leg.

#### A sixth table: `environments`, 23 destinations

Solar flux, array mass factor, blackbody temperature, cycle period, eclipse
fraction, dark period, mass, mean radius, surface gravity, escape velocity,
conjunction range and one-way light time, from Mercury orbit at 0.387 AU to the
Jupiter Trojans at 5.204. Ten rows are named bodies rather than classes, and
eight of those have had a spacecraft at them.

The argument for it: the other five tables price a kilogram and none of them
knows WHERE, while three rows already sitting in `operational_costs` are
functions of heliocentric distance alone.

- "Power system specific mass" is 60 W/kg and its unit string is careful to say
  *at 1 AU*. What it could not say is what to do about it.
  `solar_array_mass_factor` is r², so 7.3x at the main belt.
- The eclipse FRACTION was already tabulated; what sizes a battery is the dark
  PERIOD, and the two barely move together. 38% of a 93-minute LEO orbit is a
  35-minute battery; 50% of a lunar synodic day is a 354-hour one — a third
  more of the cycle, 604 times the stored energy, 341 kg of battery at this
  dataset's own 104 usable Wh/kg.
- "Autonomous mining control & AI (NRE)" is a $200M line that exists because
  teleoperation stops working past a light-second. `one_way_light_time_min`
  says where that is: 1.3 s at the Moon, 22 min at Mars, 35 at the belt.

Every column that can be derived is derived, from the values a mission actually
measures — a distance, a mass, a radius, a rotation period, an illumination
fraction — so a row cannot disagree with itself.

⚠️  **The derivations use only multiply, divide and `sqrt`**, which IEEE 754
requires to be correctly rounded. That is what puts `environments.csv` in the
byte-identical-everywhere contract rather than in the summary's few-ULP one,
and `tests/test_schema.py` parses the module and fails on an `exp`, a `pow` or
a `**`. Add a transcendental here and the file changes contract silently while
still looking correct on the machine that wrote it.

#### `validate` can now be heard, and can now fail

It returns its findings as a list, `strict=True` raises `ValidationError`, and
every finding carries a level: `WARN` for a row that looks wrong, `NOTE` for
one that is merely unusual. `spacecost validate --strict` is the gate, and CI
runs it.

⚠️  **No band changed.** What changed is that anything reads them. Every
finding went to `say()`, which is silent unless a caller sets verbose, and
`build_catalog` calls the validator on every build — so the default path ran
every check and threw the answer away. `build_catalog` still discards them
deliberately, because a build must not die over a speculative row; the gate is
the CLI and CI.

The strict flag ignores NOTEs on purpose. The g-load line fires on the
committed tables every single run, and a gate that fails on it is a gate
somebody switches off.

**New checks**, all for failures that produce no error at all: duplicated keys
(a duplicate name turns `.set_index(...).loc[...]` from a row into a frame, and
`mission_cost_breakdown` does exactly that lookup twice), the environment
bands, and a NOTE when a `reference_year` is more than three years old.

#### `tests/test_schema.py`, new

That every row of a table carries the same keys, that keys are unique and
unpadded, that `_LIVE_BLENDS`, `_THRUSTER_SYSTEMS` and every `yfinance_proxy`
still name rows that exist, that the environment derivations recompute, and
that the committed tables trip no WARN.

The key-set check is the one to keep. `pd.DataFrame(list_of_dicts)` takes the
UNION of the keys, so one row spelling a column differently gets NaN in the
real column and a new column nobody reads — silently — and then falls out of
every band that filters on the real one. The row most likely to carry a typo is
the one somebody just added.

#### The query helpers stop reading the rocket equation literally

BEHAVIOUR CHANGE, and it moves the top of the ranking. The propellant table
carries two columns whose whole purpose is to stop the arithmetic being
believed, and `cheapest_propellant_for` read neither.

**Propellantless rows are excluded by default.** A sail has no propellant, so
its Isp is infinite, so the mass ratio is 1, so any Δv costs exactly $0.00 —
and the three sail and tether rows swept the top three places of every ranking
this package has ever returned, including the one `spacecost propellant 6500`
printed. `PROPELLANTS_REFERENCE` says at the flag itself that a sail's
characteristic acceleration is ~0.1 mm/s² and that sizing one needs a
thrust-limited model this package does not have; `validate` already excluded
them from its bands for the same reason. `include_propellantless=True` brings
them back.

**The low-thrust Δv penalty is applied.** `dv_penalty_factor` is 1.5 on every
electric row because a milli-newton stage spirals rather than burns, and a
spiral costs strictly more Δv — LEO escape is ~3.2 km/s impulsive and ~7
spiralling. It is worth real places rather than a rounding: 17 of 38 ranked
rows move at 6,500 m/s, 25 at the main-belt 10,500, where it costs VASIMR first
place outright.

The penalised value is RETURNED, in `effective_dv_m_per_s`, not applied out of
sight. Silently costing a different Δv from the one the caller named would be
its own quiet defect.

`mission_cost_breakdown` takes the same penalty, and returns
`dv_penalty_factor` with both effective Δv values. Every default it ships with
is chemical and carries 1.0, so **the worked example does not move**; a test
asserts that the two paths return identical dicts for methalox.

⚠️  **`build_transportation_summary` does NEITHER, and must not start.** It is a
raw cross-join, and economicspace's Stage 4 applies the penalty itself when it
reads it — applying it in both places charges 1.5x twice, which is 2.25x, with
nothing raising. If your caller already applies it, pass
`apply_dv_penalty=False`. `tests/test_query.py` asserts the asymmetry from both
ends so it cannot drift shut.

#### Each table is now held against itself

Three relationships the data has always had and nothing has ever checked. All
of them are clean today, which is exactly when to write a check down.

- `usd_per_kg_to_leo` restates `list_price_usd / payload_leo_kg`, and all three
  sit on one very long row twelve columns apart — which is what makes raising a
  price and forgetting the $/kg beside it the single most likely way that table
  goes wrong. All 36 rows agree to within a rounding. WARN band, 1% tolerance
  because the stated $/kg are whole dollars.
- `operational_costs` and `storage_systems` both carry a `value` with a
  `range_low` and `range_high` around it, and nothing checked the point
  estimate against its own bracket. A value outside its own range is not a wide
  estimate, it is a stale edit or a swapped pair — and a swapped bracket prints
  as a perfectly ordinary row. 64 bracketed rows, all consistent.
- `exhaust_vel_m_per_s` restates `isp_vac_s * g0`, and `ref_cost_usd_per_L`
  restates `ref_cost_usd_per_kg * density_kg_per_L`. Source invariants, held in
  `tests/test_schema.py`.

The mass driver is the instructive exception on the second of those: it is
stated the other way round, from a 3,000 m/s muzzle velocity, with its Isp
derived and rounded to a whole second. So that check carries a rounding
tolerance rather than a float epsilon, and the reason is written down beside
it.

`validate` gained a `storage_df` parameter for the range check. It is
positional and optional, after `environments_df`; `strict` became **keyword
only** in the same edit, so that a frame can be appended to the positional list
later without turning somebody's `True` into a DataFrame argument.

#### `tests/test_prices.py`, new: the live path, offline

The `--live` path had no test at all. It is off by default, every committed
file is an offline build, and `fetch_yfinance_fuel_prices` catches every
per-ticker exception and returns an empty frame — so a renamed ticker, a
changed quote unit or a broken conversion degrades to "reference prices" with
no error anywhere.

The weekly canary answers whether Yahoo still serves the tickers, and it cannot
run on a pull request. This file is the half that can: a stubbed `yfinance` in
`sys.modules`, quotes chosen as round numbers so an expected value is worked
out in the assertion rather than copied from a previous run, and coverage of
the three unit conversions, the latest-close selection, the mixture weighting,
a single dead ticker, and the extra not being installed at all.

`LITRES_PER_BBL` is checked against `42 * LITRES_PER_GAL`, because they are
separate constants under separate helpers and nothing held them to the same
world.

#### A reference row was reading a mutable config singleton

`OPERATIONAL_COSTS_REFERENCE`'s "Contingency reserve" row was literally
`CONFIG.contingency_fraction * 100`, evaluated at import against the
module-level dataclass instance. Two consequences, and neither raised:

- A build with `SpacecostConfig(contingency_fraction=0.45)` charged 45% in
  `mission_cost_breakdown` and wrote **20.0** into this row of the CSV beside
  it, so the catalog reported a contingency the build had not used.
- `CONFIG` is mutable, so assigning to it after import moved the dial without
  moving the table.

The two are different things and the fix is to stop pretending otherwise. The
row is now the literal **20.0** — it is a cited industry-standard figure sitting
in its own 15-50% band, the same kind of datum as every other row in that
table. `contingency_fraction` is a dial on one mission's arithmetic. They agree
at the default, and `validate` now emits a NOTE when a caller's config makes
them disagree: `validate(..., config=cfg)`, which `build_catalog` passes
automatically.

NOTE and not WARN, because a first-of-kind mission at 45% is legitimate. The
caller is just not entitled to be surprised by it later.

**No output byte moved**: `0.20 * 100` is exactly `20.0`, which is precisely
why nothing noticed. `tests/test_schema.py` therefore checks the SOURCE — no
reference table may read `CONFIG` at all — rather than the value.

#### Three figures were restated in two files

`storage_systems` and `operational_costs` overlap by design: the first is the
taxonomy and the citations, the second is what economicspace's Stage 4 actually
reads, and `load_storage` tells you to add a figure to both. Three were obeying
that instruction by being typed twice — RTG specific power, the eclipse
fraction, and the volatile containment mass — each a literal value AND a
literal range in two files, agreeing only because nobody had edited one yet.

CITATIONS.md states the principle at the top of the file: two copies of one
measurement is a defect waiting to happen, because one of them gets updated.

`storage.py` now reads all three from the ops rows through `_mirrors_ops`.
Direction matters: ops is what Stage 4 consumes, so ops is the authority and
storage mirrors. Renaming an ops category raises a `KeyError` at import rather
than silently unlinking the two, which is the whole point of doing it by lookup
instead of by comment. The `unit` strings still differ between the tables —
that is presentation, and only the numbers are shared.

**No output byte moved**; the values were already equal.

And the half that is not tautological: a test now flags any ops/storage pair
that shares a value AND both range bounds without being declared as a mirror.
That catches the fourth one, copy-pasted in some future edit. It matches on all
three numbers because a bare value collision is ordinary — several unrelated
rows happen to be 5, or 0.5, or 100 — while three agreeing is a copy.

#### Dead imports, one of which argued against its own module

`tables.py` imported numpy and never called it, which reads as though the
module does array work. It deliberately does not: the summary loop stays scalar
because `np.exp` dispatches a different SIMD kernel for an array, and
`summary_meta.json` records a scalar-path hash. An unused import there argued
the opposite of the comment three lines below it.

Removed, along with `os` in `cli.py` and `Dict` in `propellants.py`. Two tests
in `tests/test_quiet.py` keep them out: a general unused-import scan, and a
specific one asserting that `tables.py` reaches for no array library at all —
which is the shortest way to state the vectorisation decision.

#### Smaller

`validate` gained a keyword-only `config` parameter for the contingency check.
`load_storage`'s docstring now says to mirror rather than to retype.
`fuel_mass_fraction` and `_blend` are held to the same answer for every blend
that has both, since they are two implementations of `1/(1+O/F)` over one
shared `_OF_RATIOS`.

#### Fixes

**`isru_return_propellant` was documented backwards.** The comment said the
propellant's $/kg "drops to" the on-site processing cost. It does not: $50/kg
on site is two hundred times what methalox costs on Earth, so the propellant
line goes UP. What ISRU saves is the LAUNCH — return propellant made at the
destination is not dead mass on the outbound leg, so it is neither lifted nor
pushed through the outbound burn. On the worked example that halves launched
mass, 36.5 t to 17.2 t, and the total falls despite the propellant line rising
two hundredfold. Anyone reading the old sentence would have expected the
propellant line to fall and gone looking for a bug when it did not. The model
was right; the sentence beside it was not, and the test now asserts the
counter-intuitive direction on purpose.

**The worked example printed a 1.5x penalty as "2".** One `,.0f` formatted
every float in the breakdown, which was right while every value was dollars or
kilograms and wrong the moment one of them became a RATIO. Values below 100 now
print to two decimals.

**`.gitattributes` named `reference/SUMMARY_SHA256`**, which `summary_meta.json`
replaced. A rule for a path that does not exist is not inert — it reads as if
something is pinned when nothing is. Replaced with `*.json text eol=lf`, which
is what that directory's JSON actually wants.

**`cheapest_launch_to` no longer ranks vehicles that cannot reach the
destination.** BEHAVIOUR CHANGE. Electron, Vega C and Alpha carry nothing
beyond LEO, so their `payload_gto_kg` is 0 and their `usd_per_kg_to_gto` is
NaN; the filter was `payload >= min_payload_kg`, which at the default 0 is
`0 >= 0`. All three were ranked in "cheapest to GTO", sorted last because
pandas puts NaN last, and so invisible until somebody asked for more rows than
there were real answers. A price of "not at any price" must not sort against a
price.

**One mixture ratio per blend, not two.** `prices.py` reconstructed the kerolox
and methalox fuel fractions from its own copies of 2.30 and 3.60, which
`propellants.py` also holds. Retuning a blend would have left the live path
pricing the OLD mixture — in a `--live` build only, with both numbers
plausible, and nothing saying so. Both now read `_OF_RATIOS`.

**A live quote that matches no reference row now warns** instead of being
skipped in silence. The symptom otherwise is `price_basis` reading "reference"
on a row the caller asked to be live, which is exactly what an offline build
looks like.

**The summary cross-join is 4x faster**, 2.9 s to 0.7 s, by unpacking the
segment and propellant frames once instead of calling `iterrows()` three deep —
47,232 Series rebuilt to perform 39,852 multiplications.

⚠️  **The arithmetic was deliberately NOT vectorised.** One numpy call would be
faster still and would change the output bytes: `propellant_mass_for_dv`
reaches `np.exp`, and numpy dispatches a SIMD kernel for an array that is not
the scalar path. The committed hash is a scalar-path hash. Verified byte
identical against the pre-change build.

#### Automation

**`tools/refresh_reference.py`**, new: regenerates `reference/` and writes
`summary_meta.json` including the platform block, which until now was
hand-maintained. A stale platform block does not fail —
`test_summary_hash_on_the_reference_platform` SKIPS when it does not match the
running host, so a wrong block turns the strictest test in the suite into a
no-op, silently, on every machine.

`--check` reports drift and is a CI step. It compares the portable half (the
six tables, the sample, the row count and stride) and reports the platform
block as information rather than as staleness — otherwise it would fail on
every CI leg but one and be switched off within a week.

**CI gains a strict validation gate and a weekly live-price canary.** The
`--live` path is exercised by nothing on a normal run: it is off by default and
every committed file is an offline build, and `fetch_yfinance_fuel_prices`
catches every exception per ticker and returns an empty frame, so a renamed
ticker or a changed quote unit degrades to "reference prices" in silence. The
canary fetches for real on a schedule and fails if a quote is missing or lands
outside $0.05-$50/kg, which is a unit error rather than a market move.
Scheduled and manual only, so a third-party outage can never block a merge —
and NOT `continue-on-error`, because a canary that cannot go red is a cron job.

### 0.1.1 - 2026-09-07

Data contract `pipeline_version` **1.14.0**, unchanged. No table row moved and
no output byte moved.

**Adds `validate_tables`, a second name for `validate`.** Both are the same
function; prefer the longer one anywhere your build rewrites source.

The reason is concrete. economicspace concatenates its four stage modules into
a single file and resolves name collisions with a whole-word regex over the
entire text -- comments and string literals included. Module 2 there also
defines a `validate`, so `from spacecost import validate as _v` had the
IMPORTED name rewritten and then failed against a package with no such
attribute. Aliasing the local name does not help: the imported name is still a
bare word. The fix has to be a name that does not collide.

⚠️  **Found by installing the pinned tag into a clean virtualenv**, not by the
test suite, which imports the working tree and so could not see that `v0.1.0`
predated the fix. A tag is what consumers actually get; test that, not only the
tree.

### 0.1.0 - 2026-09-07

First release. Data contract `pipeline_version` **1.14.0**, unchanged.

Extracted from Module 3 of
[economicspace](https://github.com/loggger101/economicspace) at commit
`b0b18b2`. The extraction sliced source line ranges rather than re-typing
anything, so every reference row and every citation crossed over byte for byte,
and `tests/test_parity.py` is the evidence: all six output CSVs are byte
identical to the ones that module produces, hashes included.

**No table row changed. No output byte changed.** What changed is packaging:

- the package no longer prints on import, and no longer creates a directory on
  import. Every `print` became `say`, which is silent unless
  `set_verbose(True)` or the CLI asks otherwise
- `use_yfinance` now defaults to **False**. A build is deterministic and
  offline unless the caller asks for the network, and `yfinance` moved to an
  optional extra. This is a **default flip**, and the only behavioural
  difference in the release: a configure-nothing build now resolves all 41
  propellants to reference prices, where upstream three of them would be live
- output defaults to `./spacecost_data`, reading `SPACECOST_OUTPUT_DIR`, where
  upstream defaulted to a Colab path and read `ASTEROID_PIPELINE_OUTPUT_DIR`
- `build_transportation_catalog` is now `build_catalog`, and takes a
  `catalog_date` argument that pins the provenance stamp so two builds can be
  compared without midnight reading as a defect. The old name is kept as an
  alias
- added: a CLI (`spacecost build`, `show`, `propellant`), a test suite, and
  `reference/`, the five tables as committed CSVs for anyone who wants the data
  without running Python

**A portability finding, from CI on the first push.** The five reference
tables are byte-identical on Linux and Windows across Python 3.9, 3.12 and
3.14. The composite summary is not, and cannot be: three of its columns are
rocket equation, so they run through `exp()`, which is the platform libm and
numpy's per-architecture SIMD kernels, and neither is required by IEEE 754 to
be correctly rounded. Linux 3.9 and 3.12 agreed with each other while 3.14
differed, which is a numpy version picking different kernels rather than an OS
difference.

That is a property of floating point, not a defect, and it is not filed as one.
The contract is stated at the strength each file can actually carry: the tables
are compared byte for byte everywhere, the summary is compared by VALUE to
within 1e-12 relative, and its byte hash is recorded together with the platform
it was taken on and checked only there.

The composite summary is 7.4 MB and is not committed.
`reference/summary_sample.csv` is a 411-row stride sample at full precision and
`reference/summary_meta.json` carries the row count, the hash and that
platform.

## Where the rest of the history lives

The section below is the **table-level** record: what changed in which stamp,
which config fields and output columns each added. It is complete, all 21
stamps, and it is the authority for what a given `pipeline_version` contains.

⚠️  **It is not the whole story, and the rest is deliberately not copied here.**
Seven of these releases shipped jointly with the model that consumed the
tables, and those release notes carry the *measurements that motivated the
table change* -- what moved, by how much, and on what population. Those are
measurements of that model, not facts about these tables, so they stay where
they were made. Naming one authority is the alternative to having two that
drift.

Read them at
[economicspace/versions.md](https://github.com/loggger101/economicspace/blob/main/versions.md):

| this stamp | the release note that explains why |
|---|---|
| `1.9.0` | `calc v1.11.0 / transportation v1.9.0` -- tankage is only ~0.7% of launch mass and still changes which propellant wins |
| `1.10.0` | `calc v1.12.0 / transportation v1.10.0` -- why the thruster device is separate from the propellant, and what a COPV costs at 22.9% tankage |
| `1.11.0` | `calc v1.14.0 / transportation v1.11.0` -- the storage figures behind the eclipse power term |
| `1.12.0` | `calc v1.15.0 / transportation v1.12.0` |
| `1.12.1` | `calc v1.17.7 / transportation v1.12.1` -- the `.astype(bool)` flag fix, which lives in a function Stage 4 never calls |
| `1.13.0` | `calc v1.18.0 / transportation v1.13.0` -- three reference rows for a Mars-orbit depot |
| `1.14.0` | `calc v1.19.0 / transportation v1.14.0` -- four reference rows for a geostationary depot |

## Data contract history

Every `pipeline_version` stamp these tables have carried, from `1.2.0` to
`1.15.0`. It is the measurement record: what changed in which release, what
each number used to be, and which release added which output column.

**This is the only copy.** The entries below were written while the tables were
Module 3 of [economicspace](https://github.com/loggger101/economicspace), and
that repo held them until 2026-09-07; it now points here, because two copies of
one measurement record is a bug and the tables are this package's. Nothing was
altered in the move, and nothing was dropped -- checked token by token with
that project's `verify_docs.py --before`, 874 distinctive numbers, none lost.

⚠️  **Read them as history, not as instructions.** They describe
`modules/transportation.py`, so file paths and cross-references in them point
into that project. The numbering is continuous across the move: a catalog on
disk stamped `transportation 1.9.0` was written by the tables this package
versions as data contract `1.9.0`.

⚠️  **The schema half is the part with no other home.** Which release added
`tank_kg_per_L` and which added the thruster columns is what tells you whether
an archived CSV can answer the question you are asking of it.

**`1.2.0`  initial release.**

**`1.2.1`  May 2026 source audit.** Launch prices re-cited; hydrazine
$700 → $75/kg, xenon $1.5k → $10k/kg, argon $1 → $10/kg, H3 LEO 6.5 → 16.5 t,
SLS $2.5B → $4.1B, Falcon 9 $70 → $74M, and every `notes` field source-tagged.

**`1.2.2`  second-pass sanity sweep.** SLS LEO 42 t → 105 t (42 was the TLI
figure) with the $/kg recalculated; Falcon Heavy LEO 63.8 t → 57 t, to match
the partial-reuse $97M price; xenon density 5.4 → 2.0 g/cm³, 5.4 being
physically impossible; a caveat on Starship's 27 t escape figure, which assumes
orbital refuelling; and citations added to the crew and mining-payload-recurring
rows.

**`1.2.3`  third-pass deep audit.** Falcon 9 GTO 8.3 t → 5.5 t (8.3 was
expendable and the row is reusable) and escape 4.0 t → 2.5 t (4.0 was
Mars-transfer, not C3=0 reusable); a rocket-equation bug fixed in
`mission_cost_breakdown`, where outbound propellant now correctly includes
return-propellant dead mass when ISRU is off, having understated launch mass by
~110% in the worked example; an unused `Optional` import removed; and the blend
maths hand-verified: rho_kerolox 1.015, rho_hydrolox 0.361, rho_methalox
**0.833**, rho_MMH/NTO **1.159** kg/L, all consistent.

**`1.2.4`  uncrewed autonomous-only mission model.** The
`Crew (if crewed mission)` row ($400M per crew-year) is replaced by
`Autonomous mining control & AI (NRE)` at $200M per programme, so every
downstream Stage 4 cost cascade is uncrewed by design with no life-support or
crew-habitat mass anywhere.

**`1.2.5`  portability, no change to any number produced.** `output_dir`
defaults via `_default_output_dir()` instead of a hardcoded
`/content/asteroid_pipeline`, which on Windows silently resolved to
`C:\content`; stdout and stderr forced to UTF-8 before the first print, the
emoji progress output having crashed cp1252 consoles instantly; and the
`RUN & PREVIEW` block moved under a main-guard so importing the module no longer
triggers a full run.

**`1.3.0`  realism audit.** Two additions, both consumed by calc v1.4.0.

- New `dv_penalty_factor` column on `PROPELLANTS_REFERENCE`. The rocket equation
  does not care about thrust, but trajectories do: a milli-newton electric stage
  cannot fly the impulsive burns `DELTA_V_REFERENCE` assumes, and spiralling out
  of LEO costs ~7 km/s against ~3.2 impulsive. Chemical systems carry 1.0,
  electric 1.5. Without it, Isp 3,000 s wins the payload cascade on a Δv budget
  it cannot achieve.
- New `OPERATIONAL_COSTS` row `Return capsule recurring cost` at $150k/kg.
  Stage 4 was billing the return capsule at the $300k/kg mining-payload rate,
  pricing a parachute-and-heat-shield can as regolith-contact machinery.

New output column on `propellants.csv`: `dv_penalty_factor`.

**`1.4.0`  IN-SPACE DELIVERY ARCHITECTURE.** Reference data for selling the
mined material at an in-space destination instead of flying it down. Paired with
mineral_value v1.3.0 and calc v1.5.0. Additive, so every number a v1.3.0
`earth_surface` run produced is unchanged.

- Six new `DELTA_V_REFERENCE` segments: the delivery ladder above LEO (TLI
  **3,150** / NRHO insertion 450 / LEO to NRHO 3,600 m/s) and the three asteroid
  return legs quoted at v_inf = 3 km/s (LEO propulsive **3,626**, cislunar
  Oberth capture 944, LEO aerobraked 100 m/s). The LEO-to-NRHO figure is what
  Stage 2 integrates to price material sold at a cislunar depot.
- Three new `OPERATIONAL_COSTS` rows: `Berthing adapter recurring cost`
  ($60k/kg, replacing the re-entry capsule for in-space delivery),
  `Depot berthing & handover operations` ($2M, replacing the $15M Earth recovery
  campaign) and `FAA Part 450 licensing (launch only)` ($1.2M, no re-entry
  licence).

The headline physical result these encode: cislunar is BOTH cheaper to reach
from an asteroid than LEO (960 against **3,590** m/s, because capture can take
the Oberth benefit and NRHO is barely bound) AND worth more per kg on arrival.
Earth's surface is the cheapest to reach and worth the least.

**`1.5.0`  SURFACE DESTINATIONS.** Reference data for delivering to a lunar or
Mars surface base. Paired with mineral_value v1.4.0 and calc v1.6.0. Additive
again; no existing number changed.

- Eight new `DELTA_V_REFERENCE` segments: the lunar descent chain (TLI to LOI
  900, NRHO to LLO 730, LLO to surface 1,870, and the LEO-to-lunar-surface total
  of 5,920 m/s) and the Mars chain (TMI 3,600, entry to surface retropropulsion
  800, plus the surface-to-LMO **4,100** and LMO-to-Earth 2,100 return legs).
- One new `OPERATIONAL_COSTS` row, `Surface lander recurring cost` at $200k/kg:
  a lander is active where a re-entry capsule is passive, so it sits above the
  $150k/kg capsule and below the $300k/kg mining rig.

The Moon is the awkward case these numbers expose: it is the CLOSEST destination
and among the most expensive to land on, because there is no atmosphere and
every metre per second of the 5,920 m/s from LEO is paid propulsively. Mars is
four times further in Δv terms from Earth and gets most of its arrival braking
free from an atmosphere.

**`1.6.0`  data for the modelling gaps calc v1.7.0 closes.** Additive; no
existing number changed.

- `Electric thruster + PPU specific mass` 8 kg/kW and
  `Electric propulsion efficiency` 0.60. Together with the existing
  power-system row these make low-thrust TRIP TIME computable:
  T = 2·eta·P/(Isp·g0), and a burn lasting m_prop·(Isp·g0)²/(2·eta·P). Until now
  electric propulsion paid a Δv penalty but flew instantly and drew no power.
- `Water liberation energy (bound water)` 2,500 Wh/kg. C-type water is bound in
  phyllosilicates and has to be baked out; the pipeline was extracting it for
  free.

**`1.7.0`  data for calc v1.8.0's rig terminal value, in-space manufacturing,
reliability and boil-off models.** Additive.

- New `boiloff_pct_per_day` column on `PROPELLANTS_REFERENCE`. Hydrolox at
  0.05%/day is the one that bites: over a 5-year mission that is 2.5× the return
  propellant, which is exactly why no flown mission has ever done a deep-space
  arrival burn on hydrolox after a multi-year cruise. Storables and the
  electrics are 0.
- Six new `OPERATIONAL_COSTS` rows: launch reliability 0.97, spacecraft MTBF
  30 yr, first-of-kind mining success 0.75, rig service life 15 yr, rig salvage
  fraction 0.50, and in-space plant throughput 100 kg/yr per kg of plant.

**`1.8.0`  two rows for calc v1.9.0's reliability-growth model.**
`Mining reliability growth exponent` 0.30, the Duane alpha at the bottom of
MIL-HDBK-189's active-growth band, appropriate for hardware that flies once
every few years with no test fleet; and
`Mining system mature success probability` 0.95, the asymptotic ceiling, mature
spacecraft mechanisms running 97-99% while a continuously-operating excavator is
harder than a one-shot deployment.

**`1.8.1`  first-of-kind mining success recalibrated 0.75 → 0.85.** The v1.7.0
note cited three failures and none of the successes; the full regolith-contact
record is 11/13. The notes now list the whole tally, both ways of counting
Hayabusa, and why sustained-operation risk is not double-counted here.

**`1.8.2`  the electric stage was flying on hardware nobody had to buy.** New
ops row `Electric propulsion system recurring cost`, $1.5M per kW of thruster
plus PPU, NEXT-C anchored, range $0.5-3M/kW. calc v1.7.0 put the electric
stage's array and thruster into the ROCKET EQUATION and never into any cost
line, so a 309 kW / 14-tonne EP system was free, and once calc v1.10.0 stopped
selecting missions by "cheapest", electric propulsion won everywhere. The array
is priced off the existing $800/W power-system row; this row covers only the
propulsion train. Adds one category, to 35.

**`1.9.0`  CATALOG COMPLETENESS AUDIT.** Full write-up:
[calc v1.11.0 / transportation v1.9.0](https://github.com/loggger101/economicspace/blob/main/versions.md#calc-v1110--transportation-v190). The
three reference tables held what somebody happened to list rather than what
exists, and the omissions all ran in the same direction. Propellants 7 → 40
(sixteen additions that have flown and were simply absent, seven in development,
nine concepts); tank mass DERIVED rather than ignored, via new `storage_class`
and `tank_kg_per_L` columns; new `status` / `trl` / `restartable` /
`propellantless` / `isru_feed_kg_per_kg` / `isru_feed_material` / `first_flight`
columns; launch vehicles 12 → 36, including eight non-rocket concepts; new
`launch_type` / `origin` / `trl` / `max_accel_g` / `tanker_flights_for_escape`
columns; a new `STORAGE_REFERENCE` table of 20 systems exported as
`storage_systems.csv`; and a new ops row `RTG specific power` at 5.0 W/kg, which
finally gives the RTG cost row (present since v1.2.0 and never read by anything)
a consumer in Stage 4.

⚠️  `STORAGE_REFERENCE` is the table calc v1.14.0 later had to move into
`OPERATIONAL_COSTS` wholesale, because Stage 4 does not load
`storage_systems.csv` and the whole thing was documentation. See v1.11.0 below.

**`1.10.0`  realism audit of the v1.9.0 tables.** Full write-up:
[calc v1.12.0 / transportation v1.10.0](https://github.com/loggger101/economicspace/blob/main/versions.md#calc-v1120--transportation-v1100).
Three changes, two of which move every number: a `_THRUSTER_SYSTEMS` block
supplying `thruster_kg_per_n`, `thruster_efficiency` and `thrust_scaling` per
technology, so the DEVICE is modelled and not only the propellant; a new ops row
`Power processing unit specific mass` at 4.7 kg/kW, splitting the lumped
8 kg/kW figure, because a per-kW number cannot express a per-newton constraint;
argon split into `ArgonSC` and `ArgonLIQ`, the row having carried a cryogenic
liquid's density with an ambient gas's zero boil-off and its own two comments
contradicting each other three lines apart; and a new ops row
`Propellant tank recurring cost` at $6,000/kg, Centaur-derived, tank MASS having
existed since v1.9.0 with nothing ever buying one.

Propellants 40 → 41 (23 operational, 8 development).

**`1.11.0`  the reference DATA was right and unreachable.** Full write-up:
[calc v1.14.0 / transportation v1.11.0](https://github.com/loggger101/economicspace/blob/main/versions.md#calc-v1140--transportation-v1110). Four
new `OPERATIONAL_COSTS` rows, not one of them a new measurement: every figure
already existed in `STORAGE_REFERENCE`, where it had sat behind a
"Not modelled in Module 4" note since v1.9.0, and Stage 4 loads
`operational_costs.csv` and does NOT load `storage_systems.csv`. The rows are
`Eclipse / night-side dark fraction` 0.50,
`Energy storage usable specific energy` 104 Wh/kg,
`Power-system row baseline dark period` 0.58 h and
`Volatile cargo containment` 0.05 kg/kg.

No propellant, vehicle or Δv figure moved. Every number Stage 4 produces does,
because it can now read these.

**`1.12.0`  the rig had a calendar life and no duty-cycle limit.** Full
write-up:
[calc v1.15.0 / transportation v1.12.0](https://github.com/loggger101/economicspace/blob/main/versions.md#calc-v1150--transportation-v1120). One
new `OPERATIONAL_COSTS` row, `Mining rig maximum trips` 5 (range 2-12), the
missing half of a bound the table has carried since v1.7.0.
`Mining rig service life` is 15 YEARS and Stage 4 turned that into a mission
count by dividing by the stay, so at the ~1.25 yr stay the winning cislunar
mission actually flies, one rig served 12 consecutive campaigns. ⚠️  **A
judgement, and the row says so at length**: nothing has ever mined an asteroid
twice, so it is bracketed between terrestrial mining plant and the flight record
for regolith-contact mechanisms, and 5 is the optimistic reading of both.

No propellant, vehicle, Δv or storage figure moved.

**`1.12.1`  one line in `validate()`, and no table row moved at all.** Full
write-up:
[calc v1.17.7 / transportation v1.12.1](https://github.com/loggger101/economicspace/blob/main/versions.md#calc-v1177--transportation-v1121). The
two propellant sanity bands selected their rows with
`~propellant_df["propellantless"].astype(bool)`, correct today ONLY because
every one of the 41 rows states the flag, so pandas infers dtype `bool`. Add a
row that omits it and the column comes back `object` with a NaN, which
`.astype(bool)` reads as **True**: the new row would be silently classed as a
sail and dropped from both bands, i.e. the two checks would stop covering
exactly the row most likely to be new and wrong. Now `.ne(True)`, resolved once
and read twice.

⚠️  Changes no exported column and no CSV, so **Stage 3 does not need re-running
for this, and should not be**: a Stage 3 run re-fetches live yfinance prices,
which moves `cost_usd_per_kg` and with it every Stage 4 baseline. The on-disk
`propellants.csv` keeps `1.12.0` until Stage 3 is next run for its own reasons.
Same call, and the same reason, as catalog v1.1.1.

**`1.13.0`  three Δv segments for a Mars-orbit depot.** Full write-up:
[calc v1.18.0 / mineral_value v1.8.0 / transportation v1.13.0](https://github.com/loggger101/economicspace/blob/main/versions.md#calc-v1180--mineral_value-v180--transportation-v1130).
`DELTA_V_REFERENCE` gains "Mars arrival → 1-sol orbit (MOI)" at **900 m/s**,
"LEO → Mars 1-sol orbit depot" at **4,500**, and "1-sol Mars orbit → Earth
(TEI)" at **900**. No column, no field, and no existing row changes.

These exist because Module 2's `_DELIVERY_LEGS` states the invariant that every
Δv it charges appears in this table. Module 4 reads none of them; it derives its
Δv from orbital elements, and this table is the citation home and the
cross-check. The cross-check earns its keep: computing capture into a 200-km
orbit from the same geometry gives **2.10 km/s**, reproducing the
independently-sourced "Low Mars orbit → Earth (TEI)" row of 2,100 m/s that has
been in this table since v1.5.0.

⚠️  The three rows do not reach `delta_v_segments.csv` until Stage 3 is next
run, and Stage 3 should **not** be run for this: it re-fetches live yfinance
prices and moves every Stage 4 baseline. Nothing downstream reads the table, so
nothing is waiting on it. Same call, and the same reason, as v1.12.1 above.

**`1.14.0`  four Δv segments for a geostationary depot.** Full write-up:
[calc v1.19.0 / mineral_value v1.9.0 / transportation v1.14.0](https://github.com/loggger101/economicspace/blob/main/versions.md#calc-v1190--mineral_value-v190--transportation-v1140).
`DELTA_V_REFERENCE` gains "LEO → GTO (perigee burn)" at **2,455 m/s**,
"GTO → GEO (circularise + plane change)" at **1,836**, "LEO → GEO depot" at
**4,291**, and "GEO → Earth (deorbit to entry)" at **1,488**. No column, no
field, and no existing row changes.

The 1,836 is the row to read the notes on. It is one burn doing two jobs, and
the plane change is bought by the law of cosines rather than added: coplanar it
would be 1,478, so **358 m/s of the GEO price is the latitude of the launch
site**. Module 4 carries a different figure, 1,730, for the same burn on an
arriving asteroid, which comes in near the ecliptic at 23.44 deg rather than
off a 28.5 deg parking orbit. They are not meant to agree.

⚠️  Does not reach `delta_v_segments.csv` until Stage 3 is next run, and Stage 3
should not be run for it. Same call, and the same reason, as v1.13.0 above.

**`1.15.0`  a sixth table, `environments`.** The first entry in this record
written here rather than inherited: 23 destinations carrying solar flux, array
mass factor, blackbody temperature, cycle period, eclipse fraction, dark period,
mass, mean radius, surface gravity, escape velocity, conjunction range and
one-way light time, 0.387 AU to 5.204 AU. New file `environments.csv`.

**No existing row changed and no existing column moved.** What moved on the
other five files is the `pipeline_version` stamp, which is a column on every
one of them, so their bytes differ from 1.14.0 and their VALUES do not.

⚠️  **Its derived columns are byte-portable and that is load-bearing.** Every
derivation is a multiply, a divide or a `sqrt`, the three operations IEEE 754
requires to be correctly rounded, so `environments.csv` joins the five
inherited tables in the byte-identical-on-every-platform contract instead of
joining the summary in the few-ULP one. Adding an `exp`, a `pow` or a `**` to
`environments.py` would move it to the weaker contract with no visible symptom
on the machine that wrote the file; `tests/test_schema.py` parses the module
and refuses.

The schema half, which is the part with no other home: an archived CSV stamped
`1.15.0` or later is the first one that can tell you what the sun, the night
and the light lag were like where the kilogram was.

**`1.16.0`  the launch table re-audited, 36 → 76 rows.** Full write-up under
package release 0.4.0 above. Every launch figure is now one number or a
stated range, and a ranged headline is the range's geometric centre. Errors
fixed: SLS Block 1B `operational` → `concept` and $4.1B → $2.65B launch-only
(centre of $2.5-2.8B); Zhuque-3 LEO 21 t → 8 t (the old figure was the
ZQ-3E); Terran R 33.5 → 23.5 t; Nova 5 → 3 t; Vulcan VC6 $110M → $128M (centre
of $110-150M); PSLV-XL escape 1,100 kg → 0.
Falcon 9 (reusable) is unchanged at $4,253/kg; it is no longer what the
delivery prices read.

`operational_costs` gains `Expendable upper stage recurring cost` ($4,800/kg,
range $1,750-$13,400), read by the delivery chains, and
Falcon Heavy (reusable) loses its unsourced 57 t optimistic LEO payload.

The schema half: 20 columns appended to `launch_vehicles.csv`, and
`usd_per_kg_to_*` is derived rather than typed. An archived CSV stamped
`1.16.0` or later is the first that can say whether a launcher could be BOUGHT
(`availability`), how far to trust its price (`price_basis`), and how wide its
uncertainty is. `payload_gto_kg` and `payload_escape_kg` are float from here
on, NaN meaning unpublished.
