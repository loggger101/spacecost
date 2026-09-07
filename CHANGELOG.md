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

## Data contract history, inherited

Every `pipeline_version` stamp these tables carried while they were Module 3
of economicspace, copied across unaltered. It is the measurement record: what
changed in which release, and what each number used to be.

> These entries describe `modules/transportation.py`. File paths and
> cross-references in them point into that project, not this one.

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
[calc v1.11.0 / transportation v1.9.0](#calc-v1110--transportation-v190). The
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
[calc v1.12.0 / transportation v1.10.0](#calc-v1120--transportation-v1100).
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
[calc v1.14.0 / transportation v1.11.0](#calc-v1140--transportation-v1110). Four
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
[calc v1.15.0 / transportation v1.12.0](#calc-v1150--transportation-v1120). One
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
[calc v1.17.7 / transportation v1.12.1](#calc-v1177--transportation-v1121). The
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
[calc v1.18.0 / mineral_value v1.8.0 / transportation v1.13.0](#calc-v1180--mineral_value-v180--transportation-v1130).
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
[calc v1.19.0 / mineral_value v1.9.0 / transportation v1.14.0](#calc-v1190--mineral_value-v190--transportation-v1140).
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
