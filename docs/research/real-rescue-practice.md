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
