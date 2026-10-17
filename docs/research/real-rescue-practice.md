# How volunteer flood rescue actually works, and what it means for ReachPoint

Research date: 11 Oct 2026. Sources are listed at the end. Where a source didn't cover something, that's marked "not found" instead of being guessed.

## 1. What really happened in Hat Yai (Nov 2025)

- **About 13 separate help-request channels** existed: jitasa.care, Traffy Fondue (LINE), Hatyaitongrod, koothai.co, SouthAid, Army and PSU forms, and others. Each had its own fields, and only one had a clear status scheme: red = critical, yellow = urgent, green = can wait, DONE = helped (Rocket Media Lab).
- **jitasa.care (Mirror Foundation) became the main shared database** for rescue teams and the Army disaster unit (มทบ.42). It reached over 9,000 cases.
  - Volunteers called people back to confirm their status.
  - A back-office team closed cases, and it was understaffed.
  - Problems seen:
    - duplicate cases
    - **rescuers arriving at addresses where people had already been moved**
    - shelters not sharing data
    - chaotic handoffs between teams, until a push toward "Single Command" (MGR Online)
- **One citizen tool showed each rescuer the 3 nearest cases**, and the rescuer accepted one. That is a pull model with distance built in (Spring News, describing ThaiRod). I couldn't confirm the details in a second source.
- **The government white paper on the failure** (ThaiPublica, May 2026) found:
  - Over 20,000 requests came in on 23–29 Nov.
  - There was no unified command and no single action plan.
  - Intake forms were often missing a callback number and GPS location.
  - **There was no database of boats or vehicles.**
  - **Nobody tracked where food and water had already gone.**
  - Vulnerable people were poorly defined and household counts were inaccurate.
  - Its recommendations: a shared resource database, aid-distribution tracking, better intake forms (callback number and GPS), one shared data system, and village health volunteers (อสม.) built into the response.

## 2. How other experienced groups do it

- **Cajun Navy (US):**
  - Requests were collected into a shared Google Sheet.
  - **One person entered each request and a second person vetted it by calling back.**
  - A dispatcher then sent the **nearest boat** over Zello radio.
  - Before this system, boats "had no way to define which areas had been rescued and which were still in need." That is a push model with live dispatch.
- **Crisis Cleanup (US, recovery work):**
  - Organizations **claim** work orders on a shared map (pull model).
  - When finished, they close each one as **"Closed, completed"** or **"Closed, needs more help"**, which sends it back to the clearinghouse.
  - I did not find an official "unclaim" procedure.
- **Incident Command System (ICS), the standard for professional responders:**
  - Every resource is **Available, Assigned or Out of service**.
  - Out of service records **the reason and an estimated time of return**.
  - Status updates come by radio and are written down by one unit.
- **Family unity (humanitarian guidance from UNICEF and Better Care Network):** take every measure to keep children with their families or caregivers during evacuation. Separation usually happens by accident in the chaos.
- **Triage:** agencies put life-threatening calls first. Some only attend "risk to life" calls during floods. Mis-categorised calls caused deaths in Washington DC. I found **no standard numbered flood-priority scheme**, but red/yellow/green is already familiar to Thai teams.

## 3. What ReachPoint already gets right

| Real practice | ReachPoint (already decided) |
|---|---|
| A shared list of cases that teams pick from (jitasa, ThaiRod, Crisis Cleanup) | The pull model (21A): first team to accept wins |
| A dispatcher can still send a specific boat (Cajun Navy) | Coordinator's direct "Can you take this?" (D2) |
| Available / Assigned / Out of service (ICS) | Available / Busy / Off duty, with age shown (D4) |
| Life-threatening calls first | Urgent-first tiers, with medical first (D2, D3) |
| A second person vets each request (Cajun Navy) | Coordinator reviews every AI-proposed fact before it's published |
| No boat database or aid tracking (the Hat Yai failure) | Resource ledger with daily allowance and supply allocations (D24) |
| Inaccurate household counts | Reviewed people counts; corrections tracked |

## 4. Gaps the research shows (these update the Codex findings)

1. **Keep households together by default.** Real guidance is to keep families together. So a household from one call is one "together" group unless the coordinator splits it. Splitting happens **between** groups at a pickup point (for example, 12 people from 4 families at the temple, and a boat takes 2 families), not inside a family.
2. **People move before the boat arrives.** This was a common Hat Yai problem. Fixes:
   - Each case shows "last confirmed HH:MM".
   - The team can ask the desk to re-confirm before leaving.
   - A claim fails if the case changed since the team looked (the revision check).
3. **Every job needs a clear ending.** Following Crisis Cleanup, a job closes as one of:
   - **Done**
   - **Already left / helped by others**
   - **Not found**
   - **Needs more help**, which returns only the remaining people or items to the list
4. **Distance matters, as well as priority.** ThaiRod showed the nearest cases, and the Cajun Navy sent the nearest boat. Within the same priority colour, the list should put the nearest case first for that team.
5. **Busy / Off duty can carry a reason and an estimated return** (ICS). This is shown for information only, never as a timer.
6. **Use red/yellow/green as the visible priority colours**, since Thai teams already know them. The internal tiers stay as they are.
7. **Supplies:** track what was delivered and where, so the same street isn't served twice while another gets nothing.

## 5. Locations, headcounts and satellite vs ground (research 2026-10-12, D25–D29)

**Locating people**
- The Hat Yai help sites asked for a map pin, a shared GPS location or a Google Maps link, plus the number of people:
  - jitasa.care, Traffy Fondue, กู้ไทย and thaihelp worked this way;
  - thaihelp used RED/YELLOW/GREEN/DONE;
  - rescue.sync had a "reporting on behalf of someone else" checkbox.

  ([Rocket Media Lab](https://rocketmedialab.co/flood-relief-system/), [The Matter](https://thematter.co/brief/252791/252791))
- Several sites showed every pin publicly. One promised to delete its data within 2 weeks after the water went down.
- A volunteer's Google Form of rescued names let teams **remove pins** once people were safe ([Nation Thailand](https://www.nationthailand.com/news/general/40058824)).
- Thai addresses geocode poorly at house level: Google matched over 90% of addresses, but often not to the right house ([EASR 2019](https://ph01.tci-thaijo.org/index.php/easr/article/view/140887)). **Pinpoint** ([pin-point.co](https://pin-point.co/en/)) is a Thai geocoding API.
- **For us:** store an exact point with its source and precision. Show it only to the coordinator and the team that took the job.

**Many callers, the same people**
- **Kerala 2018:** about **25% of portal entries were duplicates**.
  - Volunteers checked the database before filing a new case, then followed up by phone until the rescue was done.
  - A later cleanup treated the same phone number within one hour, plus the same location or requester, as one request. It also caught some genuine follow-ups, so the rule is imperfect.

  ([Social sensing study](https://www.sciencedirect.com/science/article/pii/S2212420922001273), [volunteer account](https://medium.com/@jaydeepborkar/volunteering-for-kerala-flood-search-and-rescue-team-kerala-floods-2018-5129d339b33b))
- **Emergency dispatch practice:**
  - Possible duplicates are flagged and **linked, not deleted**.
  - Matching uses phone number, address within about 500 ft and time.
  - Each caller is treated as a witness, because a "duplicate" may report a new incident.

  ([Prepared](https://www.prepared911.com/blog/related-incidents-launch-calltaker-dispatcher-911), [Sacramento directive](https://cityofsacramento.gov/content/dam/portal/police/Transparency/policy/commcenterdirectives/CD%20410.02%20-%20Telephone%20Answering_Redacted.pdf), [Garda](https://www.garda.ie/en/about-us/our-departments/office-of-corporate-communications/news-media/cad-incident-lifecycle-29-july-21.pdf))
- **Hurricane Helene 2024:**
  - Requests to check on someone went on a **welfare-check list**. People were not counted as missing until someone had tried to contact them.
  - Separate agency lists were merged into one "so there are no duplicated cases".
  - About 600 were reported missing at first; the count fell below 10, mostly as people were reached.

  ([Mountaineer](https://www.themountaineer.com/news/four-fatalities-confirmed-in-haywood-from-helene-flooding/article_3763ea24-8035-11ef-8853-13c292bd35a1.html), [WLOS](https://www.wlos.com/news/local/asheville-police-buncombe-county-sheriff-resume-normal-operations-missing-persons-welfare-checks-helene-search-rescue-recovery-register-of-deeds))
- **Harvey 2017:** requests listed a location, the number of people and special needs. Volunteers vetted each one by phone before dispatching a boat ([Harvard Data-Smart](https://datasmart.hks.harvard.edu/solutions/houstonmiami-harvey-rescue-site)).
- **No source adds up neighbours' headcounts. Teams count on arrival.**
- **For us:** three report kinds (my household, someone else's, what I can see), one place per building, "at least N" from the largest single report, link but never delete, and the team confirms the count.

**Satellite vs ground**
- Copernicus Global Flood Monitoring uses an **exclusion mask**: urban and other hard-to-see areas are "no data", not dry ([NHESS 2024](https://nhess.copernicus.org/articles/24/2817/2024/nhess-24-2817-2024.html)).
- GISTDA labels its maps "not yet validated through field inspection" ([Thairath](https://en.thairath.co.th/scoop/infographic/2897818)).
- In Jakarta in 2020, NASA's flood map was checked against **verified** crowd reports from PetaBencana ([PetaBencana](https://info.petabencana.id/?p=1044)).
- **For us:** show "no satellite data", never dry. The satellite can raise concern but never lower it, and reviewed caller reports fill the gaps.

**The real Hat Yai flood, for our numbers**
- Rain fell 19–21 Nov, with 335 mm on 21 Nov.
- The city centre flooded on 22–23 Nov, when the U-Tapao canal and Khlong R.1 overflowed.
- The peak was 24–25 Nov, at **2–3 m deep, over 4 m in places** (GISTDA, from Sentinel-1 and HAND).
- GISTDA's 25 Nov figures for Hat Yai district: **52,731 rai flooded, about 150,230 people affected**.
- The water went down over weeks.

([Khaosod](https://www.khaosodenglish.com/featured/2025/11/22/flash-floods-swamp-hat-yais-city-center-stranding-tourists/), [Thai Examiner](https://www.thaiexaminer.com/thai-news-foreigners/2025/11/25/rising-water-of-death-sees-songkhla-and-hat-yai-facing-worst-flooding-in-300-years-say-some-observers/), [Bangkok Post](https://www.bangkokpost.com/thailand/general/3144390/hat-yai-zone-submerged-for-weeks), [Thairath](https://en.thairath.co.th/scoop/infographic/2897818))

**For us:** GISTDA's figures are the sanity check for our estimate. Because the water went down slowly, a zone's needs shift from rescue to supplies over days.

## 6. How teams cut and use zones (research 2026-10-12, D30)

- **Edges a crew can see.** Search planners cut segments along features visible in the field (roads, railways, canals, creeks) so teams need less GPS, and they keep segment edges and IDs fixed for the whole incident ([CalTopo segment training](https://training.caltopo.com/firstresponse/course/segment)). Segments of very different size are a planning problem; size follows the work, not a grid.
- **Use existing lines where they exist.** Segments often follow existing boundaries such as census blocks or fire and police districts.
- **One written assignment per team and shift.** In ICS, each division or group gets an assignment list (ICS 204) with the team, the area, the work and the radio contact for one operational period ([FEMA ICS 204](https://training.fema.gov/EMIWeb/IS/ICSResource/assets/ICS%20Forms//ICS%20Form%20204,%20Assignment%20List%20(v3.1).pdf)).
- **Mark what's done.** US&R teams mark each searched building: a slash on entry, an X on exit, with team, date, hazards and people still inside ([TEEX log book](https://teex.org/wp-content/uploads/WAS_PER213_TEEX-Unit_Log_Book.pdf)). ReachPoint's "Checked · T-S · 4 households" is the digital version.
- **Harvey:** crews searched Houston block by block, each crew on a named neighbourhood ([AP via KTVU](https://www.ktvu.com/news/rescuers-seek-anyone-alive-or-dead-left-in-floodwaters)).
- **Hat Yai already has the lines.** The city municipality divides itself into 4 districts (เขต 1–4) with 103 communities (28/29/25/21), published as a map ([hatyaicity.go.th](https://hatyaicity.go.th/content/cate/259)), and its Nov 2025 flood warnings counted communities per district ([Thansettakij](https://www.thansettakij.com/general-news/646798)). After the flood, academics proposed that the command centre register which group covers which area, to cut duplicated work ([Thai Post](https://www.thaipost.net/general-news/903372/)).
- **Consequence (D30):** city zones follow OSM roads, the railway and canals, sit inside one city district each, and keep generic IDs.

## Sources
- Rocket Media Lab, Hat Yai help-request systems: https://rocketmedialab.co/flood-relief-system/
- ThaiPublica, Hat Yai flood white paper: https://thaipublica.org/2026/05/hatyai-flood-systemic-failure-analysis/
- MGR Online, jitasa.care: https://mgronline.com/live/detail/9680000114332
- Spring News, citizen pin systems: https://www.springnews.co.th/news/hot-issue/860848
- Bangkok Biz News, help channels: https://www.bangkokbiznews.com/news/news-update/1209375
- Nation Thailand, how to seek help: https://www.nationthailand.com/news/general/40058824
- Bangkok Post, Hat Yai calls for help: https://www.bangkokpost.com/thailand/general/3143937/desperate-calls-for-help-echo-in-flooded-hat-yai
- Cajun Navy (Wikipedia): https://en.wikipedia.org/wiki/Cajun_Navy
- Cajun Navy dispatch: http://cajunrelief.org/cajun-navy-texas-navy-coordinated-directed-remotely-citizens/
- Crisis Cleanup: https://p2pfoundation.net/Crisis_Cleanup
- Missouri intake packet (claim/close): https://extension.missouri.edu/media/wysiwyg/Extensiondata/CountyPages/Howell/Docs/MoDisasterAssistanceIntake%20Packet.pdf
- ICS 210 status definitions: https://firemarshal.ks.gov/DocumentCenter/View/299/ICS-210-Instructions-PDF
- Family unity in evacuation: https://bettercarenetwork.org/sites/default/files/2022-06/326.011_en_critical_considerations.pdf
- UNICEF on separated children: https://www.unicef.org/press-releases/statement-unicef-executive-director-henrietta-fore-unaccompanied-and-separated
- Triage examples: https://countypress.co.uk/news/23892830.fire-service-attended-three-isle-wight-flood-callouts , https://www.nbcwashington.com/news/local/what-went-wrong-as-10-dogs-drowned-in-dc-flooding-errors-delayed-dispatch/3408947/?amp=1
- Sentinel Asia, Southern Thailand floods (Hat Yai products, 23 Nov 2025): https://sentinel-asia.org/EO/2025/article20251119TH.html
- Hat Yai flood extent technical report (GISTDA-derived polygons): https://nakmuay.charity/projects/Post_Flood_Hat_Yai_Thailand_2025-12-01/reports/flood-extent-technical
- Google Open Buildings (Thailand covered, v3): https://sites.research.google/gr/open-buildings/
- DOPA registered population (data.go.th): https://data.go.th/en/dataset/dopa-star

## Checked 17 Oct 2026: published evidence used in the README

Each item was opened and its date and wording checked. Figures keep their own scope; don't add them up.

| What | Source |
|---|---|
| A Hat Yai rescue volunteer group (Matchima Rescue Center) had thousands of calls over three days, plus thousands of Facebook appeals | [Reuters via MarketScreener, 25 Nov 2025](https://www.marketscreener.com/news/thailand-to-send-aircraft-carrier-for-flood-relief-as-rains-intensify-ce7d5edddb80f122) |
| A mother on her roof for two days with her 4-year-old: calls answered, nobody came | [ABC News, 30 Nov 2025](https://www.abc.net.au/news/2025-11-30/thailand-floods-death-toll-rises/106082418) |
| Crisis centre merged Traffy Fondue, HatYaiFlood and volunteer-group requests: ~40,000 cases, 77,000 people, ~3,000 urgent; incomplete because names didn't match; four operational zones | [The Nation, 27 Nov 2025 (briefing 26 Nov)](https://www.nationthailand.com/news/general/40058844) |
| False WhatsApp requests cost a rescue team minutes each; it asked for location, number of people and contact in every request | [Bernama, 27 Nov 2025](https://www.bernama.com/en/news.php?id=2496089) |
| Outside volunteers didn't know the small alleys or where vulnerable people were; a proposal for local zone command centres | [Matichon, 24 Nov 2025](https://www.matichon.co.th/politics/news_5472795) |
| Phone and power outages left victims out of contact; elderly and sick people stayed in flooded houses | [Thai PBS, 25 Nov 2025](https://www.thaipbs.or.th/news/content/358821) |
| ThaiRod on LINE showed volunteers the three nearest cases; Jitasa.Care and Traffy Fondue coordinated with military and rescue teams | [Spring News, 25 Nov 2025](https://www.springnews.co.th/news/hot-issue/860848) |
| Jitasa.Care: volunteers and developers used AI to sort ~20,000 social-media messages by need and location | [Thairath English, 25 Nov 2025](https://en.thairath.co.th/news/politic/2897779) |
| GISTDA satellite/HAND estimate: most of Hat Yai district 2–3 m deep; ~150,000 people and ~25,000 homes affected | [GISTDA, 25 Nov 2025](https://old.gistda.or.th/news_view.php?lang=TH&n_id=8951) (page did not load live when checked; indexed copy) |
| 145 deaths in eight provinces, at least 110 in Songkhla (interim) | [AP, 28 Nov 2025](https://apnews.com/article/thailand-south-flood-damage-aa127ba2af6a845dc309cfc2fe99d035) |
| White paper: no system tracked where help had reached and where it was still missing; intake forms lacked callback details and coordinates; 20,000+ cases 23–29 Nov | [ThaiPublica, 21 May 2026](https://thaipublica.org/2026/05/hatyai-flood-systemic-failure-analysis/) |

Not found: a published example of the same family's forwarded posts being counted many times, or a duplicate rate.
The README says only what these sources support.
