"""Author static PDF drawings for accepted prototype scope; no application logic."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/pdf/reachpoint-workflow-wireframes-v1.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
W, H = 1440, 1000
c = canvas.Canvas(str(OUT), pagesize=(W,H))
c.setTitle('ReachPoint - volunteer workflow wireframes')
c.setAuthor('ReachPoint product planning')
INK='#262626'; MID='#626262'; BORDER='#B8B8B8'; PALE='#F1F1F1'; WHITE='#FFFFFF'

def box(x,y,w,h,fill=WHITE,stroke=BORDER):
 c.setFillColor(HexColor(fill));c.setStrokeColor(HexColor(stroke));c.setLineWidth(.8);c.rect(x,H-y-h,w,h,stroke=1,fill=1)
def txt(x,y,s,size=16,bold=False,color=INK):
 c.setFillColor(HexColor(color));c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,H-y-size,s)
def rule(x,y,x2,y2,dash=False):
 c.setStrokeColor(HexColor(BORDER));c.setDash(4,3) if dash else c.setDash();c.line(x,H-y,x2,H-y2);c.setDash()
def para(x,y,s,w,size=15,leading=22,bold=False,color=INK):
 yy=y; font='Helvetica-Bold' if bold else 'Helvetica'
 for explicit in s.split('\n'):
  line=''
  for word in explicit.split():
   trial=(line+' '+word).strip()
   if line and stringWidth(trial,font,size)>w:
    txt(x,yy,line,size,bold,color);yy+=leading;line=word
   else:line=trial
  if line:txt(x,yy,line,size,bold,color);yy+=leading
  elif not explicit:yy+=leading
 return yy

def button(x,y,w,s,primary=False):
 box(x,y,w,38,INK if primary else WHITE,INK if primary else BORDER)
 txt(x+12,y+10,s,14,True,WHITE if primary else INK)
def badge(x,y,w,s):
 box(x,y,w,28,PALE)
 # Drawing labels must fit their container; use a smaller font only if needed.
 size=12
 while stringWidth(s,'Helvetica-Bold',size)>w-18 and size>9:size-=.5
 txt(x+9,y+6,s,size,True)
def title(x,y,s,w=800):txt(x,y,s,22,True);rule(x,y+38,x+w,y+38)
def table(x,y,width,heads,data,widths,rowheight=61):
 box(x,y,width,36,PALE);xx=x
 for h,ww in zip(heads,widths):txt(xx+12,y+10,h,13,True);xx+=ww
 yy=y+36
 for row in data:
  xx=x
  for val,ww in zip(row,widths):para(xx+12,yy+12,val,ww-24,14,20);xx+=ww
  rule(x,yy+rowheight-1,x+width,yy+rowheight-1);yy+=rowheight
 return yy

def page(head,sub):
 box(0,0,W,H,WHITE,WHITE)
 txt(40,24,head,27,True);txt(40,65,sub,16,color=MID)
 txt(40,955,'ACCEPTED PRODUCT SCOPE / PROPOSED STATIC LAYOUT | ALL DATA, GEOGRAPHY AND QUALIFIED REVIEW SYNTHETIC',12,True,color=MID)
 txt(1284,955,f'{c.getPageNumber():02d} / 07',12,True,color=MID)
def shell(role,active,clock):
 box(40,110,1360,787)
 box(40,110,1360,59,PALE)
 txt(60,127,'ReachPoint',21,True);txt(280,132,'Fictional Harbor locality',15)
 badge(678,126,178,'SYNTHETIC FIXTURE')
 txt(920,131,role,15,True);txt(1200,132,f'Clock {clock}',14)
 box(40,169,150,728,PALE)
 names=['Area map','My missions'] if 'Team' in role else ['Area map','Missions','Emergency desk']
 for i,name in enumerate(names):
  yy=214+i*57
  if name==active:box(51,yy-8,128,40,'#DDDDDD')
  txt(60,yy,name,15,name==active)
 para(60,770,'Sources\nFixture only\nNo live feeds',111,12,21,color=MID)
def bottom(a,b):
 txt(212,906,a,14,True)
 txt(212,931,b,13,color=MID)
def circle(x,y,r=9):
 c.setFillColor(HexColor(WHITE));c.setStrokeColor(HexColor(INK));c.circle(x,H-y,r,stroke=1,fill=1)

# 1: The team leader starts with needs and their own capability.
page('01  Area map - where can our team help today?', 'Team leader / daily planning | Map, assessed response needs and uncovered contribution.')
shell('Team leader / T-R relief','Area map','10:00')
txt(212,191,'Plan today',28,True)
badge(816,196,559,'T-R: RELIEF | 4 PEOPLE | 80 PACKS IN STOCK | PAYLOAD CHECK PENDING')
txt(212,242,'[x] Flood evidence   [x] Area needs   [x] Existing plans   [ ] Team position reports',15,True)
txt(212,277,'Map [selected] / List   |   Extent observed 09:00   |   Depth reports separate',14,color=MID)
# Large map, fictional cartographic shapes; no imagery or actual coordinates.
box(212,316,789,440,'#FAFAFA')
for yy in [396,514,647]:
 box(227,yy,756,13);rule(228,yy+6,982,yy+6)
for xx in [303,578,903]:
 box(xx,333,12,395);rule(xx+6,333,xx+6,728)
p=c.beginPath();p.moveTo(725,H-332);p.lineTo(760,H-332);p.lineTo(744,H-465);p.lineTo(784,H-635);p.lineTo(756,H-738);p.lineTo(720,H-738);p.lineTo(747,H-635);p.lineTo(710,H-468);p.close()
c.setFillColor(HexColor('#D0D0D0'));c.setStrokeColor(HexColor(BORDER));c.drawPath(p,fill=1,stroke=1)
box(337,371,215,185,PALE,INK)
for row in range(3):
 for col in range(5):box(354+col*36,425+row*29,17,19,'#B9B9B9' if col<3 else WHITE)
txt(352,383,'P-A / support subset A01',15,True)
badge(351,522,187,'30 PACKS UNASSIGNED')
box(797,410,183,168,PALE)
txt(811,427,'P-B / evacuation',15,True)
para(811,466,'24 known needs\n12 scenario places\nMedical needs unassessed',149,13,22)
box(355,607,207,106)
txt(370,619,'P-C / assess first',16,True)
para(370,657,'Exposure 50 (model)\nCurrent needs unknown',175,13,22)
badge(228,329,367,'SCHEMATIC / NO REAL COORDINATES OR ROUTES')
button(950,329,35,'+');button(950,375,35,'-')
txt(787,632,'River',12,True,color=MID)
# Selection panel is about decisions, not satellite counting.
box(1021,316,354,440)
txt(1039,332,'Selected: P-A',22,True)
badge(1039,375,318,'SUPPORT IN PLACE / ASSESSED SUBSET A01')
para(1039,422,'Assessed target today: 80 people\nExposure model: 100 / year 2025\nCurrent occupancy outside A01: Unknown',315,14,23)
rule(1039,501,1357,501)
para(1039,519,'A01 depth reports: 0.4-0.8 m\nSynthetic ground-relative observations\nObserved 09:00 / no area-wide depth\nMode basis: assessment AT-A at 09:30',315,13,22)
para(1039,626,'60 packs remain undelivered.\n30 planned elsewhere; 30 unassigned.\nNot a blanket household safety label.',315,14,22)
button(1039,709,318,'Plan a 30-pack relief trip',True)
table(212,781,1163,['Other attention','Why it stays visible','Relevant contribution'],[
 ('P-B / evacuation','Known gap / medical needs unassessed','Coordinator / qualified teams'),
 ('P-C / no current assessment','No report is not no need','Scoped assessment / local contact')],[305,470,388],rowheight=34)
bottom('Selection opens the same area in map, list and planner.', 'Building symbols and depth/population records are fixtures, not satellite inference or current observations.')
c.showPage()

# 2: Simple target and manifest, explicit proposed state.
page('02  Mission planner - what should we bring?', 'Team leader / P-A | Prepare a specific contribution and expose checks before commitment.')
shell('Team leader / T-R relief','My missions','10:05')
txt(212,191,'P-A / daily relief trip',26,True);badge(1090,196,285,'DRAFT / NOT COMMITTED')
box(212,260,354,557,PALE)
txt(232,279,'Area need and coverage',21,True)
para(232,325,'Scope: assessed subset A01\nPeriod: today\nTarget: 80 people\nAllowance: 1 pack/person/day\nScenario allowance only',310,15,26)
rule(232,469,546,469)
para(232,490,'Required: 80 packs\nReceived / usable: 20\nRemaining: 60\nAccepted other plan: 30\nUnassigned: 30',310,16,28)
para(232,662,'Scope/overlap checked in fixture.\nA commitment is not a delivery.',310,14,22,color=MID)
box(587,260,788,286)
txt(607,279,'Our proposed contribution',21,True)
txt(607,329,'Mission type',14,True);box(760,323,592,37,PALE);txt(774,332,'Relief supplies / A01',15)
txt(607,382,'Food packs',14,True);box(760,376,196,39,PALE);txt(774,384,'30',18,True)
txt(994,384,'Stock 80 / proposed load 30',14)
txt(607,438,'Planned window',14,True);box(760,432,592,39,PALE);txt(774,443,'Proposed 13:00-14:00 / requires acceptance',14)
para(607,490,'After this proposal: 30 still unassigned. After acceptance: 0 unassigned; 60 still undelivered.',737,14,22)
box(587,565,788,252)
txt(607,583,'Readiness and extra capabilities',21,True)
para(607,630,'Relief capability: declared/reviewed fixture / T-R\nPayload/access/staging checks: pending / owner coordinator\nMedical requirements: no reviewed request for A01 in fixture\nNew medical reports go to the desk; absence is not established',731,15,26)
button(607,754,349,'Submit draft for coordinator review',True)
button(979,754,373,'Inspect overlap / compare another area')
bottom('The draft does not reserve resources, assign a team or confirm arrival.', 'Coordinator review / team acceptance establishes planned coverage; receipt still requires its own evidence.')
c.showPage()

# 3: Review and capability matching, no fake immediate clinical AI assessment.
page('03  Emergency desk - validate and allocate', 'Coordinator / C-01 | Source-linked facts, qualified requirements and suitable-team options.')
shell('Coordinator','Emergency desk','10:18')
txt(212,191,'C-01 / reported urgent assistance',26,True)
badge(1060,196,315,'REPORT REVIEWED / NO TEAM ACCEPTED')
box(212,264,308,543,PALE)
txt(230,283,'Incoming reports',20,True)
for yy,head,body in [(332,'CALL-01 / C-01','10:10 / location clarified'),(445,'P-C / assessment gap','No current scoped observation'),(558,'Unlocated report','Keep visible / clarify landmark')]:
 txt(231,yy,head,16,True);para(231,yy+36,body,260,14,23);rule(231,yy+97,500,yy+97)
para(231,715,'Interrupted calls and unknown locations remain review work.',260,14,22,color=MID)
box(540,264,401,543)
txt(558,283,'Evidence and review',20,True)
para(558,330,'Labeled translation:\nOur household is at the community building now. There are three of us; one needs medical help. The neighbor stayed.',361,16,26)
para(558,465,'Original Thai retained in fixture.\nCurrent location: L3 / move time unknown\nPlanned pickup: no accepted plan yet\nShared phone does not identify neighbor',361,14,24)
badge(558,579,361,'3 PEOPLE ALREADY INCLUDED IN P-B 24')
para(558,623,'Q-01 / qualified-review fixture:\nUrgent medical response capability.\nExplicitly synthetic; no real clinical act.\nAttribution/clinical state separate.',361,14,23)
button(558,748,361,'Inspect event decisions / Q-01')
box(961,264,414,543)
txt(979,283,'Response options',20,True)
para(979,329,'T-R relief: capability mismatch\nT-S rescue: available in fixture\nT-M medical: available in fixture\nNo automatic closest-team dispatch',373,15,26)
rule(979,447,1357,447)
para(979,466,'Draft transport: 3 people / L3\nMedical action: separate T-M offer\nOP-01 fictional checks: resource,\naccess and recipient scope reviewed\nTeam acceptance is still pending',373,14,24)
button(979,619,373,'Offer scoped task to T-S',True)
button(979,676,373,'Offer medical action to T-M')
para(979,738,'No arrival window becomes confirmed\nuntil the relevant team accepts.',373,13,21,color=MID)
bottom('Operational report review is distinct from qualified urgency/clinical assessment.', 'Received calls / model proposals / clinical fixtures are design states; no telephony or medical service is running.')
c.showPage()

# 4: Team mobile / desktop own task.
page('04  Team mission - prepare against the current brief', 'Team lead / T-S | Own-task version, preparation, progress and reported timing.')
shell('Team leader / T-S rescue','My missions','10:20')
txt(212,191,'M-01 / C-01 evacuation assistance',26,True);badge(1072,196,303,'ACCEPTED / BRIEF v1 ACKNOWLEDGED')
box(212,264,575,552,PALE)
txt(232,283,'Brief v1 / accepted 10:20',22,True)
para(232,330,'Scope: three people at L3 landmark\nSubset of reviewed P-B demand, not extra people\nPickup L3 / receiving point D1\nWindow: 13:00-14:00, team-provided\nProgress: Preparing / not en route',529,16,29)
rule(232,497,767,497)
para(232,520,'Resource S1 / reviewed scenario capacity\nAccess/recipient checks: OP-01 fixture\nMedical action offered to T-M; not accepted\nNo route or clinical care inferred',529,15,26)
button(232,657,535,'Report progress / estimated window')
button(232,716,535,'Report blocked / unavailable resource')
para(232,776,'A new brief requires a new acknowledgment.',529,13,20,color=MID)
box(807,264,568,552)
txt(827,283,'Preparation and communication',22,True)
para(827,329,'[x] Read acknowledged brief v1\n[ ] Recheck assigned resource/capacity before departure\n[ ] Check equipment per team-authorized plan\n[ ] Confirm staging/recipient coordination\n[ ] Report changes before departure',525,16,30)
rule(827,497,1355,497)
txt(827,520,'Resident information linked to this task',18,True)
para(827,565,'Evacuation: T-S accepted / preparing\nExpected window: 13:00-14:00\nLast update: 10:20\nMedical: no accepted team/window yet',525,16,28)
button(827,707,525,'Submit own-team update for review',True)
para(827,765,'Only necessary assigned details. Report submitted is not an approved outcome.',525,13,20,color=MID)
bottom('Preparation / en route / team completion are distinct from receipt, handover and care.', 'Illustrative locations are named references; actual team position is not plotted or implied.')
c.showPage()

# 5: Resident request and status as separate states on the same supporting surface.
def phone(x,y,w,h):box(x,y,w,h,PALE,INK);box(x+12,y+15,w-24,h-30)
page('05  Resident - request help and know what is confirmed', 'Own request / mobile | Request and accepted-status states, not a public household map.')
phone(119,132,505,756);phone(715,132,600,756)
txt(144,156,'Request assistance',24,True);badge(144,203,455,'SYNTHETIC / PROCESSING PERMISSION')
para(144,252,'Tell us your location and what help you need. A coordinator will review your report.',450,17,26)
for yy,head,val in [(347,'Current landmark','Community building / L3'),(445,'People needing help','3 / household report'),(543,'Requested assistance','Evacuation + medical help')]:
 txt(144,yy,head,14,True);box(144,yy+30,455,45,PALE);txt(157,yy+42,val,16)
button(144,672,455,'Submit request',True)
para(144,733,'Report received does not mean a team has been assigned. Phone/proxy intake follows the same review path.',450,15,24,color=MID)
txt(740,156,'Your help status / C-01',24,True);badge(740,203,550,'OWN REQUEST / UPDATED 10:20')
box(740,252,550,271,PALE)
txt(759,270,'Evacuation assistance confirmed',22,True)
txt(759,315,'Expected arrival window',15,True)
txt(759,349,'Today, 13:00-14:00',29,True)
para(759,405,'Team T-S accepted / Preparing\nWindow provided by team at 10:20\nNot a guaranteed arrival time',508,16,26)
box(740,543,550,132)
txt(759,560,'Medical assistance',21,True)
para(759,599,'Awaiting team acceptance.\nArrival time is not confirmed.',508,16,26)
button(740,703,550,'My location / situation changed')
button(740,758,550,"The team hasn't arrived")
para(740,819,'These reports return to the coordinator.\nA relief trip alone does not confirm your inclusion.',540,13,20,color=MID)
txt(119,916,'Before assignment, arrival is unknown. Each type of assistance has its own status and window.',15,True)
c.showPage()

# 6: Delay is a first-class part of resident timing, not a misleading old countdown.
page('06  When a plan changes - keep the resident informed', 'Coordinator and resident / 10:30 | Resource failure, held mission and withdrawn window.')
shell('Coordinator','Missions','10:30')
txt(212,191,'M-01 / S1 unavailable',26,True);badge(1079,196,296,'HELD / NEEDS REASSESSMENT')
box(212,264,588,550,PALE)
txt(232,283,'Reassessment and current brief',22,True)
para(232,331,'TEAM-01 / S1 unavailable at 10:30\nLinked M-01 transport prerequisite invalid\nP-A relief mission unaffected\nReplacement: Unknown / owner coordinator',545,16,28)
rule(232,464,780,464)
para(232,488,'Reviewed brief v2: Hold; replacement pending.\nSaved 10:30 / T-S acknowledgment pending\nHistorical v1 acknowledgment retained\nUnderlying progress: Preparing / now held',545,15,27)
button(232,620,546,'Verify replacement / revise plan',True)
button(232,678,546,'Inspect team report / dependency')
para(232,746,'No replacement is offered as ready without checks.\nNeed remains open; task has an owner.',545,14,23,color=MID)
box(821,264,554,550)
txt(842,283,'Resident C-01 / updated 10:30',22,True)
badge(842,332,513,'EVACUATION DELAYED / NEW TIME UNKNOWN')
para(842,389,'Your assigned transport is unavailable. The coordinator is arranging a replacement.',507,18,29)
para(842,483,'Previous window 13:00-14:00 withdrawn.\nNew arrival time: not confirmed\nNext status update: 11:00, desk commitment\nAn update time is not an arrival time.',507,16,28)
rule(842,615,1355,615)
para(842,636,'Medical assistance remains awaiting acceptance.\nNo medical arrival window is invented.',507,16,27)
button(842,722,513,'Update my location / situation')
bottom('Old windows remain in history, but cannot masquerade as the current estimate.', 'Status view is the v1 channel; outbound SMS/callback/push and real message delivery are not implemented.')
c.showPage()

# 7: Missing people and recovery, within the emergency/manual review surface.
page('07  Field discovery and incomplete intake - keep unknowns visible', 'Emergency desk supporting states | These are distinct review examples, not concurrent accepted missions.')
shell('Coordinator','Emergency desk','10:40')
txt(212,191,'Review field / incomplete reports',26,True)
box(212,265,577,550,PALE)
txt(232,284,'FIELD-PC / scoped P-C observation',22,True)
badge(232,333,536,'PROPOSED EVENTS / NOT YET APPROVED')
para(232,388,'Local observer reports one household needing supplies in a single building subset C01. The rest was not visited.',531,17,27)
para(232,487,'Observer/time: synthetic field fixture / 10:35\nProvisional association: H-PC\nNeed: assistance reported / quantity unknown\nMedical request: not reported, not proven absent',531,15,26)
para(232,612,'Review scoped coverage separately from need.\nDo not clear all P-C or manufacture household totals.',531,16,26)
button(232,702,536,'Review each event / assign follow-up',True)
para(232,769,'Approved scoped discovery leaves unvisited area unknown.',531,13,20,color=MID)
box(809,265,566,550)
txt(829,284,'Interrupted emergency call',22,True)
badge(829,333,526,'INCOMPLETE / REPORTED URGENCY VISIBLE')
para(829,388,'Permission received; call disconnected before the landmark was clarified. Received content remains an incomplete report.',521,17,27)
para(829,514,'Location: Unknown / no fabricated pin\nIdentity: unresolved / shared phone not identity\nHuman review owner: coordinator\nTeam assignment / arrival: not confirmed',521,15,27)
button(829,659,526,'Assign review / clarification action',True)
para(829,729,'Missing fields do not hide suspected danger.\nNo completed intake or rescue promise is inferred.\nReal escalation protocol remains an operational gate.',521,14,23,color=MID)
bottom('Discovery reaches beyond incoming household requests; coverage remains scoped and dated.', 'Recovery preserves received evidence and uncertainty; no actual field visit, call or clinical decision occurred.')
c.showPage()
c.save()
print(OUT)
