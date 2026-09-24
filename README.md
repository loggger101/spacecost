# spacecost

Cited reference tables for space-mission cost and mass estimation. Six tables,
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
spacecost show vehicles -n 10      # or propellants, deltav, operations,
                                   #    storage, environments
spacecost propellant 6500          # rank propellants by fuel cost for a delta-v
spacecost launch leo --min-payload-kg 5000 --open-only
spacecost environment 2.7          # the power/thermal/comms penalty at 2.7 AU
spacecost validate --strict        # run the sanity bands; non-zero on a WARN
spacecost example                  # a worked mission cost breakdown, end to end
spacecost build -o ./out           # write all seven CSVs
```

## Contents

- [What is in it](#what-is-in-it)
- [Launch prices are the centre of a stated range](#launch-prices-are-the-centre-of-a-stated-range)
- [The three things it does that a spreadsheet of prices does not](#the-three-things-it-does-that-a-spreadsheet-of-prices-does-not)
- [Where the kilogram is, not just what it costs](#where-the-kilogram-is-not-just-what-it-costs)
- [Getting a kilogram there, and getting one back](#getting-a-kilogram-there-and-getting-one-back)
- [The API](#the-api)
- [The rocket equation, read literally, is wrong twice](#the-rocket-equation-read-literally-is-wrong-twice)
- [The tables check themselves](#the-tables-check-themselves)
- [Two numbers, and they are not the same number](#two-numbers-and-they-are-not-the-same-number)
- [The output is a contract](#the-output-is-a-contract)
- [Live prices are opt-in](#live-prices-are-opt-in)
- [Changing a row](#changing-a-row)
- [Layout](#layout)
- [Reading the tables without Python](#reading-the-tables-without-python)
- [Provenance](#provenance)
- [What it does not do](#what-it-does-not-do)
- [Citations and licence](#citations-and-licence)

## What is in it

| table | rows | holds |
|---|---|---|
| `launch_vehicles` | 76 | $/kg to LEO, GTO and escape with a low/high band, payload masses, list price, status, who can buy it |
| `propellants` | 41 | vacuum Isp, bulk density, $/kg and $/L, storage class, derived tankage, thruster device |
| `delta_v_segments` | 33 | m/s and trip duration per trajectory leg, 100 to 10,500 m/s |
| `operational_costs` | 45 | $/mission-year and $/kg-payload lines, with low/high bands |
| `storage_systems` | 20 | how a kilogram is held, across the cargo, depot, propellant and energy domains |
| `environments` | 23 | where it is being priced: solar flux, dark period, gravity, light time |

The launch table spans **48 operational** vehicles, 12 in development, 9
concepts and 7 retired, across the US, Europe, Russia, China, Japan, India and
South Korea, from a lunar mass driver at a notional $10/kg to LEO up to Pegasus
XL at $89,686/kg. The cheapest operational row you can actually book is New
Glenn at $1,922/kg, on a 45 t payload it has not yet flown. The propellant
table spans 15 propulsion types, from cold gas at 70 s to speculative concepts
at 10^5 s, across 8 storage classes.

The environment table holds 23 destinations spanning 0.39 to 5.20 AU, from
Mercury orbit to the Jupiter Trojans. Ten rows are named bodies rather than
classes, and eight of those have had a spacecraft at them; Psyche arrives in
2029 and nothing has yet landed on Phobos.

Concept and retired rows are present **and marked**. Filter on `status` if you
want only things that fly; the speculative rows are there so a study can say
what it excluded rather than silently not having it.

## Launch prices are the centre of a stated range

A launch row states either one figure, where the source gives one, or the low
and high ends of a credible range. With a range, the headline price and payload
are **derived as the geometric centre** of it, `sqrt(low x high)` to three
significant figures, so a wide range lands in the middle rather than at
whichever end was to hand:

| column | holds |
|---|---|
| `list_price_usd_low` / `_high`, `payload_*_kg_low` / `_high` | the range, as stated |
| `list_price_usd`, `payload_*_kg` | its geometric centre, derived |
| `usd_per_kg_to_*` | the headline price over the headline payload |
| `usd_per_kg_to_*_low` / `_high` | low price over high payload, and the reverse |
| `price_basis` | `published`, `contract`, `reported`, `estimate` or `target` |

Geometric rather than arithmetic, because launch prices are uncertain by
factors: the Space Shuttle's $450M-$2.1B per flight centres at $972M, where a
plain midpoint would say $1.28B. Narrow ranges barely move; wide ones move a
lot, which is the point. And because price and payload are both geometric
centres, the headline $/kg is the centre of its own $/kg range too.

The ranges are conservative even though the headline is not at an end. Where
the source is a target (anything not yet flying), the target is the
**optimistic** end, never the headline, because launch-vehicle targets are
optimistic by construction. `tests/test_schema.py` asserts the rule for every
row, and import raises if a row states a headline beside a range. Every
`usd_per_kg_*` column is derived at import; none is typed.

⚠️  **`status` says whether it flies. `availability` says whether you can buy
it.** 28 of the 48 operational rows fly for somebody else: Atlas V and Proton
are sold out, SLS and Minotaur IV fly government missions only, and every
Chinese and Russian row is `restricted`, by export control or sanctions.
`cheapest_launch_to(..., purchasable_only=True)` and `spacecost launch
--open-only` keep only `open` rows. Both are off by default, so existing
rankings don't move.

⚠️  **A payload of `0` and a payload of NaN are different.** `0` means the
vehicle does not go there (Electron to GTO). NaN means it could, but nobody has
published a figure, and this table will not invent one. The ranking drops both,
since neither is a price.

`payload_escape_kg` is C3 ≈ 0 where that is published, otherwise trans-lunar
injection (slightly easier) or Mars transfer (harder). Each row's `notes` says
which, and names its source.

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

## Where the kilogram is, not just what it costs

The other five tables price a kilogram and none of them knows **where**. Three
first-order cost drivers already in this dataset are functions of heliocentric
distance alone, and until `environments` there was nowhere to read the distance
from:

| the row that needed it | what it says | what `environments` adds |
|---|---|---|
| `Power system specific mass` | 60 W/kg, *at 1 AU* | `solar_array_mass_factor`: r², so **7.3x** at the main belt |
| `Energy storage usable specific energy` | 104 usable Wh/kg | `dark_period_hr`: the hours you multiply by watts |
| `Autonomous mining control & AI (NRE)` | $200M, because you cannot teleoperate | `one_way_light_time_min`: 1.3 s at the Moon, 22 min at Mars, 35 at the belt |

The eclipse **fraction** was already in the tables; what sizes a battery is the
dark **period**, and the two barely move together. A 38% eclipse on a 93-minute
LEO orbit is a 35-minute battery. A 50% night on the lunar equator is **354
hours** — a third more of the cycle, and **604 times** the stored energy. At
100 W and the 104 usable Wh/kg this dataset quotes, that is 341 kg of battery
to keep one 100 W load alive through one lunar night, which is the whole reason
lunar surface power reaches for fission instead.

```bash
spacecost environment 2.7     # any distance, not only the 23 tabulated rows
```

A row asserts what a mission measures — a distance, a mass, a radius, a
rotation period, an illumination fraction — and every column that follows is
derived from those rather than typed in, so a row cannot disagree with itself.

⚠️  **The derivations use only multiply, divide and `sqrt`**, and that is a
contract rather than a style. IEEE 754 requires those three to be correctly
rounded, which is what lets `environments.csv` sit in the byte-identical
promise below instead of the few-ULP one. `tests/test_schema.py` parses the
module and fails on an `exp`, a `pow` or a `**`.

⚠️  `au_mean` is a semi-major axis, not where a body is on the day you ask.
Perihelion and aphelion are both columns; for Didymos they are a factor of 5 in
available power. Size for `au_max`.

## Getting a kilogram there, and getting one back

The five cost tables price the pieces. `delivery.py` composes them into the two
questions somebody costing a mission actually asks:

```python
>>> import spacecost
>>> spacecost.delivered_cost_usd_per_kg("lunar_surface")
26813.641828225067
>>> spacecost.delivery_mass_ratio("lunar_surface")
4.987... # kg that must reach LEO per kg landed
>>> spacecost.downleg_cost_usd_per_kg("cislunar")
27316.958591940387
```

**Staging is modelled leg by leg, and that is the whole point.** A destination
is a SEQUENCE of burns flown by real stages, and the mass ratios chain. Collapse
the lunar chain into the single 5,920 m/s figure this dataset also carries and
the answer roughly doubles — **10.96 kg in LEO per kg landed against 4.99** —
because a one-stage lander carries its descent structure all the way from LEO.
Delta-v alone does not tell you what a delivery costs.

An `edl` leg divides instead of multiplying: surviving 30% of Mars entry mass
means arriving with 3.33 kg for every kg that lands. That fraction is measured,
not assumed — MSL 27.6%, Perseverance 29.8%.

| | |
|---|---|
| every delta-v in a chain | **looked up in `DELTA_V_REFERENCE`**, so the table is the one authority |
| the launch price | `LAUNCH_VEHICLES_REFERENCE`: the cheapest vehicle a buyer can book today, by a stated rule, at the **low** end of its band |
| building the stages each chain throws away | `OPERATIONAL_COSTS_REFERENCE` values |
| the capsule, TPS and recovery lines | `OPERATIONAL_COSTS_REFERENCE` |
| the downleg departure delta-v | **typed**, and the comment says why |

⚠️  **The downleg delta-v are the exception, deliberately.** Four of the six
agree with a table row exactly; two do not — a LEO deorbit burn is not
tabulated at all, and the GEO figure disagrees with its row by 2 m/s. Deriving
all six uniformly would have moved two published prices under a change that
claims to move none, so they stay as literals with the mismatch written down
beside them. Reconciling them is a real question and a separate release.

### What a delivered price reads

A delivered price is what a kilogram already in space is **worth**: the launch
the buyer no longer has to buy. It is the miner's revenue, so an input read at
a high end would flatter the business case and one read at a low end would
understate it. `delivery.py` reads the same central figure the rest of the
package does: each launch row's headline, and each cost row's `value`.

**The LEO price is the buyer's cheapest real alternative today.** The rule is
stated in code and asserted at import: operational, on the open market, priced
by the launcher itself (`published` or `contract`), lowest headline
`usd_per_kg_to_leo`. That is **Falcon Heavy (expendable), $2,414/kg**: SpaceX's
$150M (2017) to $159M (carried to 2026) for 63.8 t. `leo_anchor_candidates()`
returns the ranked list. New Glenn is cheaper on paper at $1,922/kg, but the
bottom of its price range is a rival's estimate rather than a Blue Origin
quote. Starship is cheaper still, and does not fly. If a table edit ever makes
a different row win, import fails rather than re-pricing every destination
quietly.

**The stages a chain throws away are paid for.** Until v0.4.0 every expended
tug and lander was charged only for being launched, never for being built.
`delivery_hardware_usd_per_kg()` now charges each stage's dry mass at its
recurring cost, the propellant at its price, and the aeroshell an entry
discards at the TPS rate:

| destination | before (Falcon 9, no hardware) | v0.4.0 | of which hardware |
|---|---:|---:|---:|
| `leo` | 4,253 | 2,414 | 0 |
| `geo` | 12,526 | 8,046 | 937 |
| `cislunar` | 10,810 | 6,878 | 742 |
| `mars_orbit` | 13,496 | 8,706 | 1,046 |
| `lunar_surface` | 21,210 | 42,635 | 30,597 |
| `mars_surface` | 45,105 | 184,811 | 159,209 |

Orbital destinations fall by about a third, because the anchor is cheaper.
The two surfaces rise steeply, because a lander ($200k/kg) and an aeroshell
($50k/kg) are expensive things to throw away, and until now they were free. Two tests hold the result against
the market: GEO must not cost more than buying GTO directly and flying only
the last burn, and cislunar must not cost more than the cheapest direct
escape launch. Either way round, a buyer would take the cheaper route, and a
chain above it would overstate what a kilogram is worth.

`delivered_cost_usd_per_kg(dest, 4253.0, stage_hardware=False)` reproduces
every pre-v0.4.0 figure bit for bit, so a result measured before this release
can be re-derived rather than guessed.

⚠️  **`None` and `[]` are different.** `earth_surface` has no chain and avoids
no launch, so it costs 0 $/kg; `leo` has an EMPTY chain and avoids the whole
launch price. `if legs:` reads them as the same thing and prices LEO at zero,
which is a defect that has actually shipped downstream. Test `is None`.

## The API

| call | gives you |
|---|---|
| `load_launch_vehicles()` and the five other `load_*` | one reference table as a DataFrame |
| `LAUNCH_VEHICLES_REFERENCE` and the five other `*_REFERENCE` | the same data as plain dicts, no pandas needed to read it |
| `propellant_mass_for_dv(payload_kg, dv, isp)` | Tsiolkovsky, vectorised over arrays |
| `cost_per_dv_usd_per_kg(cost, isp, dv)` | the headline normalised metric: USD of propellant to move 1 kg through a delta-v |
| `cheapest_launch_to(catalog, "leo", min_payload_kg=..., purchasable_only=False)` | the launch table filtered and ranked; `purchasable_only` drops what you cannot buy |
| `cheapest_propellant_for(catalog, dv)` | the propellant table ranked by fuel cost at that delta-v, with the low-thrust penalty applied and sails excluded |
| `mission_cost_breakdown(catalog, ...)` | launch + propellant + hardware + ops + contingency, itemised |
| `build_transportation_summary(...)` | the vehicle x segment x propellant cross-join |
| `delivered_cost_usd_per_kg(dest)` | launch cost avoided: what it costs to put 1 kg at a destination, through its staged leg chain |
| `delivery_hardware_usd_per_kg(dest)` | the part of that which is building the stages the chain throws away |
| `leo_anchor_candidates()` | the launch rows the delivery LEO price is chosen from, cheapest first; `LEO_LAUNCH_VEHICLE` is the winner |
| `delivery_mass_ratio(dest)` | the same answer as kilograms in LEO per kilogram delivered |
| `downleg_cost_usd_per_kg(dest)` | and the other direction: capsule, TPS, recovery and the departure burn |
| `stage_mass_ratio(dv, isp, dry_frac)` | one propulsive leg's initial mass per kg of payload; `inf` when the tank cannot close |
| `solar_flux_w_per_m2(au)`, `solar_array_mass_factor(au)` | the 1/r² power penalty, at any distance |
| `blackbody_temp_k(au)`, `one_way_light_time_min(range_au)` | the thermal and comms consequences of the same number |
| `validate_tables(...)` (alias `validate`) | sanity bands over the loaded tables; returns the findings, and raises under `strict=True` |
| `build_catalog(config, catalog_date=None)` | everything, written to CSV |
| `set_verbose(True)` | turn on the progress output, which is off by default |

⚠️  **Prefer `validate_tables` over `validate` if your build rewrites source.**
Both are the same function. economicspace concatenates its four stage modules
into one file and resolves name collisions with a whole-word regex, so
`from spacecost import validate as _v` gets rewritten there and then fails to
import. Anything vendored, concatenated or code-generated wants the unambiguous
name.

⚠️  The query helpers read `cost_usd_per_kg`, the **resolved** price. That column
is produced by `merge_propellant_prices`, not by `load_propellants`, whose
column is `ref_cost_usd_per_kg`. `build_catalog` does this for you; if you are
assembling a catalog dict by hand, pass the propellant frame through
`merge_propellant_prices(load_propellants(), pd.DataFrame())` for an offline
resolve.

## The rocket equation, read literally, is wrong twice

Two columns in the propellant table exist only to stop you believing the
arithmetic. Until v0.2.0 the query helpers believed it anyway, and the answer
`spacecost propellant 6500` gave was:

```
                                 name  isp_vac_s  cost_usd_per_kg  usd_per_kg_payload_for_dv
               Solar sail  (photonic)        inf         0.000000                   0.000000
        Magnetic sail / electric sail        inf         0.000000                   0.000000
             Momentum-exchange tether        inf         0.000000                   0.000000
```

**A sail carries no propellant, so its Isp is infinite, so the mass ratio is 1,
so every Δv costs exactly $0.00.** Three of them swept the top of every ranking
this package returned. They are not free — characteristic acceleration is
around 0.1 mm/s², fine for a 6 kg cubesat and meaningless for a hold full of
ore — and sizing one honestly needs a thrust-limited trajectory model that is
not here. They are now excluded by default; `include_propellantless=True`
brings them back, and the $0.00 means "the rocket equation does not apply".

**An electric stage cannot fly an impulsive Δv budget.** With milli-newton
thrust it spirals, and a spiral costs strictly more than the equivalent burn:
escaping LEO impulsively is ~3.2 km/s, spiralling out is ~7. That is what
`dv_penalty_factor` is for, 1.5 on every electric row, and ranking electric
propulsion without it is the specific error the column was added to prevent. It
is worth real places — 17 of 38 rows move at 6,500 m/s, 25 at the main-belt
10,500, where it costs VASIMR first place outright.

The penalty is applied and then **reported**, in `effective_dv_m_per_s`, because
silently costing a different Δv from the one you asked about would be its own
quiet defect:

```
                                 name  isp_vac_s  cost_usd_per_kg  dv_penalty_factor  effective_dv_m_per_s  usd_per_kg_payload_for_dv
Mass driver  (regolith reaction mass)      306.0         0.100000                1.0                6500.0                   0.772388
               methalox  (LCH4 / LOX)      380.0         0.243478                1.0                6500.0                   1.149611
        VASIMR  (argon, variable Isp)     4000.0        10.000000                1.5                9750.0                   2.821724
```

⚠️  **`build_transportation_summary` does neither of these things, and must not
start.** That table is a raw cross-join, and economicspace's Stage 4 applies
the penalty itself when it reads it — doing it in both places would charge
1.5x twice. The query helpers have no Stage 4 behind them, so if they do not
apply it, nothing does. The asymmetry is deliberate and `tests/test_query.py`
asserts it from both ends.

⚠️  `mission_cost_breakdown` is still a **floor**. It does not charge tankage
(`tank_kg_per_L` is in the table and nothing bills it to the launcher), does
not model boil-off over the mission duration (`boiloff_pct_per_day` is in the
table too, and three years of it is not small for a cryogen), and does not size
the power plant an electric stage needs. Everything it omits pushes the same
way.

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

`build_catalog()` writes seven CSVs, and the guarantee is not the same for all
seven. Which one applies depends on whether a file contains a **transcendental**:

| | contract | why |
|---|---|---|
| the six reference tables | **byte identical, every platform** | five pass every value through from a table entry; `environments` derives its columns using only multiply, divide and `sqrt`, all of which IEEE 754 requires to be correctly rounded |
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

## The tables check themselves

`validate_tables` holds every loaded table to a sanity band, and it is
reachable from the command line:

```bash
spacecost validate --strict     # exit 1 on a WARN; a NOTE never fails
```

Findings carry a **level**, and the distinction is what makes the gate usable.
`WARN` means a row looks wrong: a launch price outside $100-$100,000/kg, a
propellant with no price, a tank that outweighs its contents, a duplicated key.
`NOTE` means a row is unusual and you should know — three launchers really do
pull over 50 g, and that fires on the committed tables every single run. If a
NOTE failed `--strict`, the only way to keep CI green would be to stop running
it.

⚠️  **Before v0.2.0 none of this could be heard.** Every finding went to
`say()`, `say()` is silent unless somebody calls `set_verbose(True)`, and
`build_catalog` calls the validator on every build. So the default path — a
library import, a quiet CLI build, a consumer's pipeline stage — ran every
check and discarded the result. The bands were right; nothing was reading them.
A check whose output is dropped is not a guardrail, it is a comment that costs
CPU.

`build_catalog` still discards them, deliberately: a build must not die because
a speculative row sits outside a band. The gate is the CLI and CI.

The bands also hold each table against **itself**. `usd_per_kg_to_leo` is
`list_price_usd / payload_leo_kg` and the table carries all three, twelve
columns apart on one very long row; `operational_costs` and `storage_systems`
each carry a `value` with a `range_low` and `range_high` around it. Nothing
checked either relationship until v0.2.0. All 76 launch rows and all 64
bracketed rows are consistent today, which is exactly when to write the check
down. Since v0.4.0 the launch $/kg is derived at import rather than typed, and
the launch price and payload bands get the same inside-its-own-range check, so
on the launch table these now guard the frame a caller edits after loading.

And against **each other**, where they overlap. `storage_systems` is the
taxonomy and the citations; `operational_costs` is what a consumer reads. Three
figures were obeying that split by being typed twice in two files, value and
range both, agreeing only because nobody had edited one yet. They are mirrored
now, and a test flags the fourth one the moment somebody copy-pastes it.

Beside the bands, `tests/test_schema.py` holds the **structure**: that every
row of a table carries the same keys, that keys are unique, and that the
constants two modules share still agree. These catch the failures that produce
no error at all — a key typed `isp_vac_S` on one row of forty-one adds a column
of NaN and quietly drops that row from every band that reads the real one.

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

## Changing a row

A number here is a number in somebody's trade study, so a change is a release,
not a commit.

1. **Edit the row** in `spacecost/`, keeping its `notes` citation and
   `reference_year` truthful.
2. **Bump `pipeline_version`** in `spacecost/config.py` if the change moves any
   value a build produces. That is the DATA contract, and the rule is
   one-directional: changing a number means bumping it, and bumping it is not
   evidence that a number changed.
3. **Regenerate `reference/`** with `python tools/refresh_reference.py`, and
   re-run the tests. `tests/test_parity.py` will fail until you do, which is
   the point. Do it with the tool rather than by hand: it also rewrites
   `summary_meta.json`, whose platform block is the one thing that rots
   invisibly — `test_summary_hash_on_the_reference_platform` SKIPS when that
   block does not match the running host, so a stale block turns the strictest
   test in the suite into a no-op on every machine and never fails.
   `--check` answers "is `reference/` stale" without writing anything.
4. **Run `spacecost validate --strict`**, which exits non-zero on a WARN. A
   NOTE never fails it; see [The tables check
   themselves](#the-tables-check-themselves).
5. **Add a CHANGELOG entry** under Package releases, and say what moved.
6. **Tag it.** `git tag -a vX.Y.Z` and push the tag. Consumers pin tags, so an
   untagged change reaches nobody.

⚠️  **Then repin downstream.** [economicspace](https://github.com/loggger101/economicspace)
installs this package from a pinned tag in `requirements.txt` and
`_MASTER_REQUIRED`. Until that tag moves it keeps building against the old
tables, so the edit silently does not land there.

Three checks over there catch a repin that went wrong, and they catch different
halves of it. `verify_docs.py` check 7 holds those two copies of the tag to each
other, because repinning one and not the other makes `pip install -r` and its
Colab paste install different revisions of these tables with nothing else
moving. `verify_stage3.py` check 6 reads pip's own `direct_url.json` and holds
the INSTALLED revision to the pinned tag, which is also what catches a tag that
has been moved after the fact. Its other checks then compare this package's
output byte for byte. **None of them can tell "not yet repinned" from "never
released", so cutting the tag is still on you.**

⚠️  **Test the TAG, not the working tree.** The test suite imports the source
directory, so it cannot see a packaging gap. `v0.1.0` shipped without
`validate_tables` for exactly this reason, and a clean install of it could not
satisfy economicspace's import. CI now builds a wheel and exercises the public
API from outside the tree; a clean `pip install` of the new tag is still the
last check worth doing by hand.

⚠️  **And the CONSUMER SURFACE is a test now**, `tests/test_consumer_contract.py`.
The wheel step above walks `__all__`, which proves the names this package
currently declares are packaged; it cannot see a name being deleted from the
package and from `__all__` in one commit, which is what happened with
`validate_tables`. That file lists what economicspace actually imports, so
removing one fails here rather than at a consumer's import three steps later.
A failure is not an instruction to put the name back: it says the change is
**breaking**, so it wants a major bump, a CHANGELOG entry, and the matching
edit to `modules/transportation.py` in the same breath.

## Layout

```
spacecost/          the package
    vehicles.py     the six reference tables, one per file, every row cited
    propellants.py    -- propellants.py also carries the tankage derivation,
    deltav.py            the thruster devices and the fuel/oxidiser blender
    operations.py
    storage.py
    environments.py   -- and this one derives every column it does not cite
    config.py       the dials, and the two version numbers
    tables.py       loaders, and the vehicle x segment x propellant summary
    rocket.py       Tsiolkovsky helpers
    prices.py       live commodity fuel prices, and the merge
    validate.py     sanity bands, and the strict gate over them
    build.py        writes the seven CSVs
    query.py        cheapest-X helpers and a worked mission breakdown
    delivery.py     staged delivery chains, and the cost of a kilogram
                    delivered or returned
    cli.py          `python -m spacecost`
reference/          the six tables as committed CSVs, plus a sample of the
                    seventh and the platform its hash was taken on
tools/              refresh_reference.py, which regenerates all of that
tests/              parity against reference/, table invariants, structural
                    guardrails, output rules, and the surface economicspace
                    imports
```

## Reading the tables without Python

`reference/` holds the six tables as committed CSVs, so `curl` and a
spreadsheet are enough. The seventh file, the composite
`transportation_summary.csv` cross-joining vehicle x segment x propellant, is
15.5 MB and is **not** committed. `reference/summary_sample.csv` is an 868-row
stride sample of it at full precision, and `reference/summary_meta.json` records
its row count, its hash and the platform that hash was taken on. `spacecost
build` rebuilds the whole thing.

## Provenance

These tables were built over fourteen releases as **Module 3 of
[economicspace](https://github.com/loggger101/economicspace)**, an asteroid
mining profitability pipeline, and extracted at `pipeline_version` 1.14.0
(the contract is 1.16.0 as of this release)
(commit `b0b18b2`). Two thirds of that module was annotated reference data and
nothing in its schema knows what an asteroid is, which is the argument for
splitting it out: a launch price is useful to anyone costing a mission.
economicspace consumes this package as its Stage 3.

The peer-reviewed and tiered-authoritative sources behind these rows are
collected in [General_Research](https://github.com/loggger101/General_Research):
full texts where they are legally redistributable, otherwise metadata plus the
extracted key tables, with one CSV of pulled numbers per source and the domains
organised by which table they back.

The extraction was done by slicing source line ranges rather than re-typing
anything, so every citation survives byte for byte, and the parity test is the
evidence that it changed nothing. What did change, and all it changed:

- the package no longer prints on import, or creates a directory on import
- `use_yfinance` defaults to `False`
- output defaults to `./spacecost_data`, reading `SPACECOST_OUTPUT_DIR`
- `build_transportation_catalog` is now `build_catalog` (the old name is kept
  as an alias)

## What it does not do

It does not fly a trajectory. `delta_v_segments` holds representative means per
leg; if you need a real transfer you want a Lambert solver and an ephemeris, and
this is the table you price the answer with afterwards.

It does not know today's price. Every row carries `reference_year` precisely so
staleness is visible; most are 2026. Launch pricing in particular moves.

The delivery figures are **marginal-transport lower bounds**, on purpose. The
launch price is one a buyer can book today, and the stages are paid for, but
there is no non-recurring engineering, no programme overhead and no cadence
limit, and the chain flies an efficient hydrolox tug that nobody sells as a
product yet. They answer "what is the least a kilogram there could be worth",
which is the right question for revenue. Real CLPS lunar delivery is roughly
$1M/kg at ~100 kg scale, against this model's $42,635.

**The operational table assumes an uncrewed spacecraft.** No life support, no
habitat, no crew operations, no return-vehicle uplift for people. The
"Autonomous mining control & AI (NRE)" line is what that design pays instead.
The launch, propellant, delta-v and storage tables are indifferent to crew; the
operational one is not, and costing a crewed mission with it will read low.

## Citations and licence

MIT, see `LICENSE`. Every source behind every row is listed in
`CITATIONS.md`, and the row's own `notes` field is the authority for its number.
None of the sources feeding these tables imposes a condition of use; the three
that do so upstream in economicspace are all catalog sources, and none of them
is here.
