"""Draw static review wireframes only. No application logic, network or integrations."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
import textwrap
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/pdf/relief-ledger-wireframes-v1.1.pdf'
W,H=1440,1000
c=canvas.Canvas(str(OUT),pagesize=(W,H))
c.setTitle('Relief Ledger - static wireframes for scope review')
c.setAuthor('Relief Ledger product planning')
INK='#252525'; MID='#616161'; LINE='#B8B8B8'; PALE='#F2F2F2'; WHITE='#FFFFFF'

def rect(x,y,w,h,fill=WHITE,stroke=LINE):
 c.setFillColor(HexColor(fill));c.setStrokeColor(HexColor(stroke));c.setLineWidth(.8);c.rect(x,H-y-h,w,h,fill=1,stroke=1)
def line(x,y,x2,y2,dash=False):
 c.setStrokeColor(HexColor(LINE));c.setDash(3,3) if dash else c.setDash();c.line(x,H-y,x2,H-y2);c.setDash()
def text(x,y,s,size=16,bold=False,color=INK):
 c.setFillColor(HexColor(color));c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,H-y-size,s)
def para(x,y,s,w,size=16,leading=23,color=INK,bold=False):
 font='Helvetica-Bold' if bold else 'Helvetica';yy=y
 for explicit in s.split('\n'):
  words=explicit.split();buf=''
  for word in words:
   trial=(buf+' '+word).strip()
   if stringWidth(trial,font,size)>w and buf:
    text(x,yy,buf,size,bold,color);yy+=leading;buf=word
   else:buf=trial
  if buf:text(x,yy,buf,size,bold,color);yy+=leading
  elif not explicit:yy+=leading
 return yy

def label(x,y,s):text(x,y,s,13,True,MID)
def button(x,y,w,s,primary=False):
 rect(x,y,w,36,INK if primary else WHITE,INK if primary else LINE)
 text(x+12,y+8,s,14,True,WHITE if primary else INK)
def badge(x,y,w,s):
 rect(x,y,w,28,PALE);text(x+9,y+6,s,12,True)
def section(x,y,w,title):text(x,y,title,19,True);line(x,y+34,x+w,y+34)
def note(x,y,n,title,body):
 badge(x,y,28,str(n));headend=para(x+39,y+2,title,157,16,22,INK,True)
 return para(x,max(y+44,headend+15),body,198,15,22,MID)+27

def page(title,subtitle):
 rect(0,0,W,H,WHITE,WHITE)
 text(40,27,title,28,True);text(40,67,subtitle,16,False,MID)
 text(40,940,'RELIEF LEDGER  |  STATIC DESIGN PROPOSAL  |  ALL DATA / LOCATIONS SYNTHETIC',13,True,MID)
 text(1250,940,f'{c.getPageNumber():02d} / 11',13,True,MID)
def shell(active):
 rect(40,110,1120,790)
 rect(40,110,1120,62,PALE)
 text(60,128,'Relief Ledger',21,True);text(278,134,'Fictional Harbor district',15)
 badge(682,127,154,'SYNTHETIC SCENARIO')
 text(890,132,'Coordinator',15,True);button(1020,122,119,'Search')
 rect(40,172,154,728,PALE)
 for i,name in enumerate(['Situation','Contact Center','Response']):
  yy=208+i*62
  if name==active:rect(51,yy-8,132,43,'#DFDFDF',LINE)
  text(60,yy,name,16,name==active)
 text(60,773,'Source health',13,True);para(60,800,'Fixture only\nNo live feeds',116,13,20,MID)
 text(212,909,'Scenario clock only  |  Each observation and plan retains its own time.',13,False,MID)

def notes(items):
 y=124
 for i,(title,body) in enumerate(items,1):y=note(1200,y,i,title,body)

def rows(x,y,width,cols,data,widths):
 rect(x,y,width,37,PALE)
 cur=x
 for title,w in zip(cols,widths):text(cur+10,y+11,title,13,True);cur+=w
 yy=y+37
 for row in data:
  line(x,yy+54,x+width,yy+54);cur=x
  for val,w in zip(row,widths):para(cur+10,yy+12,val,w-20,13,17);cur+=w
  yy+=55
 return yy

# Review guide / product flow
page('Review the product, before implementation','Proposed navigation, one integrated story, supporting states and two expanded map views.')
text(52,130,'Three coordinator destinations',24,True)
for x,head,body in [(52,'Situation','Flood evidence + exposure + assessment gaps'),(454,'Contact Center','Calls, messages and event-by-event review'),(856,'Response','Owned tasks, team/resources and current plans')]:
 rect(x,181,350,148,PALE);text(x+20,204,head,23,True);para(x+20,249,body,302,18,26)
text(52,386,'The story to demonstrate',24,True)
steps=[('1','Find a gap','Area A has potential exposure but no relevant assessment.'),('2','Review a discovery','A scoped field report finds H5. The rest remains unknown.'),('3','Clarify an emergency request','A real call separates the moved household from its neighbor.'),('4','Keep the plan current','V1 fails. Linked plans need review; M2 stays unchanged.')]
for i,(n,head,body) in enumerate(steps):
 yy=437+i*87;badge(55,yy,32,n);text(107,yy,head,20,True);text(107,yy+31,body,17)
text(55,824,'What to review',19,True)
para(55,858,'Page hierarchy, missing information, review authority, volunteer workflow and the proposed scope cuts. These are drawings, not an application or evidence that phone, satellite or medical integrations work.',1260,17,25)
c.showPage()

# 01 Situation
page('01  Situation - where have we not checked?','S01-S07  |  Flood evidence, potentially exposed settlements and assessment gaps.')
shell('Situation')
text(213,195,'Situation',26,True);button(915,192,224,'Create assessment task',True)
text(214,239,'Flood evidence   |   Assessment gaps [selected]   |   Known cases',15,True)
line(213,273,1141,273)
label(212,295,'LAYERS')
for i,s in enumerate(['[x] Observed extent','[x] Buildings','[ ] Population model','[ ] Station readings','[ ] Forecasts','[ ] Local reports']):text(212,326+i*38,s,14)
para(212,584,'Types stay separate. No street-depth or safe-route inference.',164,14,21,MID)
rect(389,295,452,378,PALE)
# schematic area / footprint dots (not satellite imagery)
rect(418,337,206,277,'#E1E1E1');rect(657,337,151,277,WHITE)
text(430,349,'Area A',20,True);text(669,349,'Area B',20,True)
for i in range(24):
 xx=432+(i%6)*29;yy=395+(i//6)*45
 rect(xx,yy,17,23,'#B3B3B3' if i<12 else WHITE)
text(429,592,'12 exposed detections',13);text(668,395,'Scoped',16,True);text(668,422,'observation',14);text(668,450,'10:00',15)
para(406,635,'Schematic extent / footprints. Not a satellite image.',419,12,17,MID)
rect(855,295,286,378)
text(872,312,'Harbor East / Area A',18,True);badge(872,347,243,'NO CURRENT SCOPED ASSESSMENT')
para(872,392,'12 / 24 building detections overlap the synthetic extent.',246,16,23)
para(872,454,'Modeled exposed population: 120\nReference year: 2025\nUncertainty: not supplied',246,14,22)
para(872,540,'Households / occupancy: Unknown\nObserved extent: 09:40\nBuilding source: FP-A fixture',246,13,21,MID)
button(872,622,243,'Inspect sources / scope')
section(212,706,929,'Needs attention - separate from feasible options')
rows(212,750,929,['Item','Evidence / scope','Next owner'],[
 ('Area A assessment gap','Potential exposure; no scoped check','Unassigned'),
 ('H4 assistance request','Location unknown; no confirmed option','Unassigned')],[270,405,254])
notes([('Knowledge gap','No report does not mean no need. This view proposes a check, not a victim count.'),('Source dates','Observation time and population reference year remain visible. A new fetch is not a new observation.'),('Scoped control','Area B has relevant scoped evidence. It is not labeled safe.'),('Action boundary','Create a draft assessment. Resource/access checks precede an actionable assignment.')])
c.showPage()

# 02 Inbox
page('02  Contact Center - review what was reported','C01-C09  |  One queue for calls, messages and field observations.')
shell('Contact Center')
text(213,195,'Contact Center',26,True);button(979,192,161,'Manual intake')
text(213,239,'All   |   Calls   |   Messages   |   Field reports   |   Review needed',15,True)
rect(212,290,239,532,PALE)
text(229,308,'Review queue',18,True)
for yy,title,sub in [(358,'FLD-01 / field report','10:15 - Area A discovery'),(461,'CALL-01 / inbound','10:25 - clarification needed'),(564,'H4 / text request','Unlocated; no option'),(667,'TEAM-01 / update','10:30 - V1 unavailable')]:
 line(228,yy-15,432,yy-15);text(230,yy,title,15,True);para(230,yy+28,sub,194,13,20)
text(473,291,'FLD-01 / scoped observation',21,True)
badge(473,335,241,'PROPOSED EVENTS - NOT APPROVED')
text(473,388,'Observer: T1 team lead',16)
text(473,419,'Observed 10:15 / received 10:16',14,False,MID)
rect(473,464,381,217,PALE)
label(490,480,'ORIGINAL FIELD STATEMENT')
para(490,517,'We checked one building subset in Area A. Household H5 reports needing assistance at L1. The rest of Area A was not assessed.',344,17,26)
para(473,719,'Assessment action and knowledge coverage are separate. Recording this observation does not clear the area.',378,15,23)
rect(875,291,265,531)
text(890,310,'Proposed review',19,True)
para(890,355,'1  Partial scoped assessment\n2  Provisional H5 case link\n3  Reported assistance need',230,15,26)
label(890,460,'IDENTITY / CASE ASSOCIATION')
para(890,490,'Field observer reference only. Household identity still provisional.',229,14,22)
badge(890,560,228,'EVIDENCE: REPORTED')
para(890,608,'Each event needs its own review decision. A report may be partly approved.',227,14,22)
button(890,715,229,'Review events',True);button(890,768,229,'Leave unresolved')
notes([('Same review path','Field discovery, text and telephone evidence enter the same queue; source/channel stay visible.'),('Distinct household','Provisional H5 is not authenticated by a phone number or automatically merged with a neighbor.'),('Partial coverage','The discovery supplies a scoped observation. Unvisited places remain unknown.'),('Manual recovery','Manual intake remains available when AI fails. This does not imply live call-transfer support.')])
c.showPage()

# 03 Event review
page('03  Contact Center - clarify, then approve each event','C03-C06  |  A proposed location change must not silently rewrite the plan.')
shell('Contact Center')
text(213,195,'CALL-01 / review events',25,True)
badge(882,196,258,'INTAKE ENDED - REVIEW PENDING')
text(213,242,'Case candidate H5  |  association clarified  |  current record v3',14)
rect(212,291,423,540,PALE)
text(231,310,'Conversation evidence',20,True)
label(231,351,'THAI ORIGINAL RETAINED IN RECORD')
label(231,380,'LABELED ENGLISH TRANSLATION')
para(231,419,'Our family is now at Harbor Community Building; there are three of us. Our neighbor stayed at the old place. We share a phone. A family member needs medical help.',378,17,26)
line(229,602,615,602)
text(231,624,'Clarification',18,True)
para(231,660,'Who moved? H5 household.\nNeighbor is a different household.\nExact move time: Unknown.',380,15,24)
para(231,755,'No arrival time or assistance promise. Report received for coordinator review.',379,14,21,MID)
section(657,291,481,'Proposed events / individual decisions')
text(671,350,'1  Reported current location',18,True)
text(671,388,'H5: L1 -> L3 / Harbor Community Building',14)
text(671,418,'Source excerpt 01 / move time unknown',13,False,MID)
text(671,449,'M1 planned pickup remains L1 until revised.',14,True)
button(672,489,135,'Edit proposal');button(825,489,297,'Approve attributed report',True)
line(670,551,1121,551)
text(671,574,'2  Neighbor stayed / identity unknown',17,True)
para(671,611,'Keep as proxy area report; no invented household case. Leave association unresolved.',449,14,22)
button(671,676,205,'Leave unresolved');button(891,676,231,'Reject unsupported field')
line(670,730,1121,730)
text(671,749,'3  Medical help reported: Unassessed',16,True)
text(671,785,'Coordinator review is not clinical assessment.',13,False,MID)
notes([('Review is granular','Approving the location event does not approve the neighbor identity or corroborate medical facts.'),('Current vs planned','The case location changes; the existing pickup assumption is flagged. A coordinator must revise the brief.'),('Evidence survives','Original language, labeled translation, excerpt, timing and record version remain inspectable.'),('Conflict state','If another review changes v3, show a stale-review conflict and require rereading before approval.')])
c.showPage()

# 04 Response
page('04  Response - own the next action','RSP01-RSP08  |  Team progress, reassessment and household outcomes remain separate.')
shell('Response')
text(213,195,'Response',26,True);button(977,192,163,'Create draft task',True)
text(213,241,'Assessment   |   Assistance   |   Teams & resources   |   Reassessment',15,True)
rows(212,293,929,['Task','Progress','Team / resource','Attention'],[
 ('M1 / H5 assistance','Not started','T1 / V1','Needs reassessment'),
 ('M2 / H2 assistance','Not started','T2 / V2','No linked change'),
 ('M3 / H3 later task','Draft / sequential','Proposed T1 / V1','Resource check needed'),
 ('A1 / Area A assessment','Scoped outcome reviewed','T1 released explicitly','Area partly assessed'),
 ('VFY-01 / replacement','Draft / owner: desk','No option confirmed','Verify replacement')],[252,230,226,221])
section(213,658,560,'Available options and missing checks')
para(214,708,'V1 unavailable - attributed team report at 10:30\nT1 is not automatically unavailable.\nReplacement / capacity / access: Not confirmed',551,16,26)
button(214,807,240,'Inspect team / resource')
rect(799,659,341,188,PALE)
text(817,677,'M1 needs reassessment',19,True)
para(817,722,'Reason: explicit V1 dependency.\nOwner: coordinator\nNext: verify replacement; hold task.',303,15,24)
button(817,795,306,'Open current plan',True)
notes([('Exact dependency','V1 affects M1 and M3. M2 stays unchanged. No generic team-wide unavailable flag.'),('No double booking','M3 is a later sequential draft; capacity/time are pending, not a second active mission.'),('Scarcity visible','No confirmed replacement means blocked/unassigned work and an open need.'),('Scoped outcomes','A1 task completion records only its scoped observation. It cannot mark the whole area assessed.')])
c.showPage()

# 05 assignment
page('05  Response - reassess the plan and its brief','RSP04-RSP06  |  A new acknowledgment does not mean assistance was delivered.')
shell('Response')
text(213,195,'M1 / H5 assistance plan',25,True);badge(912,193,225,'BLOCKED - REASSESSMENT')
text(213,245,'Current reported location L3  |  planned pickup L3 after explicit revision',14)
rect(213,290,438,536,PALE)
section(231,307,399,'Current constraints')
para(231,364,'T1 capability: scenario-reviewed\nV1: reported unavailable at 10:30\nReplacement: Unknown\nAccess authorization: must be checked\nDestination D1: scoped acceptance only',397,16,27)
line(230,525,629,525)
text(231,550,'Progress / dependencies',18,True)
para(231,590,'Not started\nLinked to H5 pickup, T1, V1 and D1\nV1 changes flag M1 / M3\nM2 unchanged',397,16,27)
para(231,739,'No safe route or arrival promise is inferred from the map.',396,15,22,MID)
rect(672,290,467,536)
text(691,309,'Draft brief v2 / not yet saved',21,True)
badge(691,356,422,'AFTER SAVE: TEAM MUST ACKNOWLEDGE v2')
para(691,404,'Hold assistance task. Replacement resource is not confirmed. VFY-01 will verify options and report back to its assigned owner.',423,17,26)
label(691,525,'EVIDENCE AND HISTORY')
para(691,555,'TEAM-01: V1 report\nCALL-01: H5 location\nv1 acknowledgment retained\nNo task progress erased',421,15,25)
button(691,689,422,'Save reviewed brief v2',True)
para(691,751,'After authorized save, T1 must acknowledge v2. Acknowledge means received the brief, not started/completed.',421,14,21,MID)
notes([('Reassessment loop','Reason -> evidence -> owner -> next check -> revised brief -> acknowledgment.'),('History remains','The prior brief and acknowledgment stay visible. Each reason needs an explicit review decision.'),('Unknown prerequisites','An unknown replacement or access check is not a passed constraint.'),('Pending-save state','If a concurrent version changes, stop and rereview; never show a draft as successfully saved.')])
c.showPage()

# 06 Case
page('06  Shared case detail - needs and outcomes','Case drawer  |  Medical coordination is administrative; clinical governance is unavailable.')
shell('Contact Center')
text(213,195,'Case H5 / provisional household reference',25,True)
text(213,242,'Current reported location L3  |  attributed resident report  |  time uncertainty',14)
section(213,296,929,'Separate needs / current outcomes')
rows(213,349,928,['Need','Current status','Outcome evidence'],[
 ('Assistance requested','Open; M1 blocked','No confirmed receipt'),
 ('Medical help reported','Unassessed','Qualified recipient not confirmed')],[269,304,355])
rect(213,531,444,295,PALE)
text(232,549,'Medical coordination',20,True)
para(232,596,'Reported medical assistance request\nCoordinator review owner: desk\nReferral: not requested\nRecipient: not confirmed\nAccepted handover / care: Unknown',404,15,26)
button(232,761,405,'Assign non-clinical follow-up')
rect(677,531,463,295)
text(695,549,'Evidence / correction history',20,True)
para(695,596,'10:15  FLD-01 - provisional discovery\n10:25  CALL-01 - current location L3\n10:30  TEAM-01 - V1 unavailable\nCurrent location differs from old pickup\nShared phone does not identify neighbor',423,14,26)
button(695,761,424,'Inspect / dispute attributed report')
notes([('No universal close','Water, transport, medical help and other needs have separate outcomes. Task completion is not receipt.'),('No clinical score','Unassessed stays unassessed. The coordinator is not a clinical reviewer.'),('Referral is distinct','Referral requested, acceptance, handover and confirmed care would need separate evidence.'),('Correction path','Dispute or correct a link/outcome with reason and history. Unreachable is not confirmation.')])
c.showPage()

# 07 mobile support
page('07  Supporting views - volunteer and resident','Own-task mobile view and resident text intake. Coordinator navigation stays three pages.')
# phones
for x in [162,716]:rect(x,125,394,740,PALE,INK);rect(x+14,143,366,701,WHITE)
text(187,171,'Team T1 / own task',21,True);badge(188,216,340,'SYNTHETIC - RESTRICTED VIEW')
text(187,276,'M1 / current brief v2',20,True)
para(188,321,'Hold task. Replacement resource not confirmed. Next verification owner: desk.',333,17,26)
text(188,434,'Progress: Not started',16,True)
text(188,467,'Brief v1 acknowledgment retained',14,False,MID)
button(187,515,342,'Acknowledge brief v2',True)
text(188,583,'Report own-team update',17,True)
rect(188,622,339,54,PALE);text(201,638,'V1 availability / observed time',14)
button(188,705,341,'Submit report for review')
para(188,767,'Only assigned details. Acknowledgment does not mean delivery.',333,13,20,MID)
text(741,171,'Resident text intake',21,True);badge(742,216,341,'SYNTHETIC PROTOTYPE')
para(742,274,'Processing permission required. Your message will be reviewed; assistance is not confirmed.',331,16,25)
rect(742,393,340,125,PALE)
para(755,408,'You: We moved. Our neighbor stayed. We share a phone.',309,16,24)
rect(742,539,340,119)
para(755,554,'Clarification: Who moved, and which location are you at now?',309,16,24)
rect(742,682,340,52,PALE);text(755,697,'Write your reply...',14)
button(742,751,340,'Submit message',True)
notes([('Minimum necessary','Team leads see only their own assignments and report fields, not the entire inbox or other cases.'),('Version-specific','Acknowledgment is tied to v2. The hold instruction remains separate from mission progress.'),('Accessible intake','Simple text clarification; no registration maze or promise of emergency coverage.'),('Connectivity boundary','No offline-sync or outbound callback guarantee. Unsent and pending review are explicit states.')])
c.showPage()
# 08 recovery variants
page('08  Recovery states - uncertainty stays visible','Failure variants  |  These are separate state examples, not one simultaneous incident.')
shell('Contact Center')
text(213,195,'Review and recovery',26,True)
rect(213,281,444,245,PALE);text(232,300,'Interrupted call',21,True)
badge(232,345,405,'INCOMPLETE - NO CASE UPDATE')
para(232,393,'Consented received content retained as an incomplete report. No rescue promise or completed-intake label.',402,16,24)
button(232,468,405,'Assign manual review owner')
rect(679,281,462,245);text(698,300,'Stale review conflict',21,True)
badge(698,345,424,'RECORD CHANGED - APPROVAL BLOCKED')
para(698,393,'Another reviewer updated v3 to v4. Inspect both sources and reread the current record before approval.',423,16,24)
button(698,468,424,'Reread current version')
rect(213,559,444,267);text(232,578,'Assessment attempt unreachable',20,True)
badge(232,623,405,'COVERAGE STILL UNKNOWN')
para(232,670,'Attempt recorded with time and scope. Area gap remains visible; next owner and alternative check required.',404,16,24)
button(232,768,405,'Record reason / next owner')
rect(679,559,462,267,PALE);text(698,578,'Disputed receipt report',21,True)
badge(698,623,424,'OUTCOME DISPUTED - NEED OPEN')
para(698,670,'Team delivery report and household account differ. Preserve both; review each need and correction basis.',423,16,24)
button(698,768,424,'Inspect conflicting evidence')
notes([('No false success','Incomplete call is not completed intake. It cannot silently change a case.'),('Version integrity','The review must catch current-version conflicts before an authoritative write.'),('Unknown coverage','An unreachable check does not mean the area has no needs or has been assessed.'),('Outcome evidence','Delivery and receipt stay separate. Coordinator approval alone is not corroboration.')])
c.showPage()

# Expanded map workspace: cartographic drawing, never real geographic data.
def circle(x,y,r,fill=WHITE):
 c.setFillColor(HexColor(fill));c.setStrokeColor(HexColor(INK));c.circle(x,H-y,r,fill=1,stroke=1)
def polygon(points,fill):
 path=c.beginPath();path.moveTo(points[0][0],H-points[0][1])
 for xx,yy in points[1:]:path.lineTo(xx,H-yy)
 path.close();c.setFillColor(HexColor(fill));c.setStrokeColor(HexColor(LINE));c.drawPath(path,fill=1,stroke=1)
def map_drawing(x,y,w,h,response=False):
 rect(x,y,w,h,'#FAFAFA')
 # Fictional streets, extent and river; not an imported basemap.
 for yy in [y+80,y+170,y+270,y+370]:
  rect(x+9,yy,w-18,13,WHITE);line(x+9,yy+6,x+w-9,yy+6)
 for xx in [x+82,x+277,x+499]:
  rect(xx,y+15,13,h-30,WHITE);line(xx+6,y+15,xx+6,y+h-15)
 polygon([(x+365,y+12),(x+407,y+12),(x+391,y+170),(x+435,y+319),(x+406,y+h-15),(x+365,y+h-15),(x+393,y+320),(x+350,y+175)],'#D2D2D2')
 text(x+402,y+205,'River',13,True,MID)
 rect(x+111,y+99,120,241,'#E2E2E2')
 for i in range(9):line(x+113,y+108+i*26,x+229,y+133+i*26,True)
 # A boundary with all 24 detections; exactly 12 intersect this fixture extent.
 rect(x+106,y+74,252,278,WHITE)
 rect(x+111,y+99,120,241,'#E2E2E2')
 for i in range(9):line(x+113,y+108+i*26,x+229,y+133+i*26,True)
 text(x+122,y+77,'Area A / Harbor East',16,True)
 for row in range(4):
  for col in range(6):
   rect(x+137+col*34,y+124+row*44,17,23,'#999999' if col<3 else WHITE,INK)
 text(x+122,y+315,'12 exposed / 24 detections',12,True)
 rect(x+466,y+93,127,183,WHITE)
 text(x+479,y+106,'Area B',16,True)
 para(x+479,y+145,'Scoped check\n10:00\nNot a safety label',103,12,19,MID)
 # Landmarks are synthetic anchors, with no invented metric accuracy.
 for xx,yy,name in [(x+287,y+395,'L1'),(x+493,y+393,'L3')]:
  circle(xx,yy,9);text(xx-8,yy+16,name,13,True)
 if response:
  text(x+130,y+376,'Named landmark points',12,False,MID)
  circle(x+493,y+393,16)
  text(x+464,y+434,'H5 / M1',13,True)
  text(x+275,y+434,'Old report',12,False,MID)
 else:
  badge(x+120,y+356,240,'NO CURRENT SCOPED ASSESSMENT')
 badge(x+13,y+13,255,'SCHEMATIC - NO REAL COORDINATES')
 button(x+w-47,y+12,33,'+');button(x+w-47,y+55,33,'-')
 text(x+14,y+h-28,'N ^  |  Geographic scale unavailable in drawing',11,False,MID)

page('09  Situation - a map as the main workspace','Map / list / detail  |  Locate evidence and assessment gaps, then create an owned check.')
shell('Situation')
text(213,195,'Situation map',26,True);button(915,192,224,'Create assessment draft',True)
text(214,245,'[x] Extent   [x] Buildings   [x] Assessment gaps   [ ] Cases   [ ] Team reports',14,True)
text(214,278,'Observed extent: 09:40  |  Source: fixture  |  Map [selected] / List',14,False,MID)
map_drawing(213,317,611,489)
rect(843,317,297,489)
text(860,337,'Selected: Area A',20,True)
badge(860,380,263,'ASSESSMENT GAP - NO HEADCOUNT')
para(860,431,'12 exposed building detections\nPopulation estimate: 120\nModel reference year: 2025\nHouseholds / occupancy: Unknown',260,15,25)
line(860,551,1123,551)
para(860,573,'Extent observed: 09:40\nFootprints: FP-A fixture\nDepth here: Unknown\nAssessment: no current scoped check',260,14,24)
button(860,688,263,'Inspect source / scope')
button(860,741,263,'Draft assessment task',True)
text(214,831,'Legend: shaded = observed extent; filled building = overlap; text badge = assessment gap',13)
text(214,858,'Unlocated reports: H4 stays in the list. No exact pin or household identity is invented.',13,True)
notes([('Map is central','Pan/zoom, layer controls, map/list selection and a focused details panel are proposed interactions.'),('Independent evidence','Extent, point depth readings and forecasts need different symbols, dates and references.'),('Reach silent areas','Select an exposure gap to draft a scoped assessment. No request count is used as proof of safety.'),('Honest map boundary','This is a fictional cartographic sketch. It demonstrates neither real imagery nor a live flood feed.')])
c.showPage()

page('10  Response - see the task in its spatial context','Response map  |  Compare reported and planned locations without implying a safe route.')
shell('Response')
text(213,195,'Response map',26,True);button(922,192,217,'Open M1 current plan',True)
text(214,245,'Tasks / Map [selected]   |   [x] Own scope   [x] Cases   [ ] Team position reports',14,True)
text(214,278,'Scenario 10:30  |  M1 pickup explicitly revised to L3  |  No route generated',14,False,MID)
map_drawing(213,317,611,489,True)
rect(843,317,297,489)
text(860,337,'H5 / M1 assistance',20,True)
badge(860,380,263,'BLOCKED - V1 UNAVAILABLE')
para(860,429,'Current reported location: L3\nSource: CALL-01, received 10:25\nExact move time: Unknown\nLocation accuracy: Unknown',261,14,24)
line(860,535,1123,535)
para(860,556,'Planned pickup: L3, revised\nTeam: T1 / resource: V1\nLatest T1 position: not plotted\nDestination D1 position: not supplied',261,14,24)
button(860,681,263,'Inspect constraints / evidence')
button(860,733,263,'Review / revise task',True)
text(214,831,'Legend: double ring = selected case; simple circle = landmark; no connecting route lines',13)
text(214,858,'Unlocated work and unknown team positions remain in lists. M2 is unchanged.',13,True)
notes([('Compare location types','Reported current location and planned pickup are separate even when both name L3.'),('Report, not live GPS','Only an authorized position report with time and accuracy basis can create a team marker.'),('Scope and privacy','Medical narratives stay off map pins. A team lead sees only necessary own-task locations.'),('No map auto-dispatch','A nearby marker does not establish capacity, availability, access or a safe route.')])
c.showPage()

c.save()
print(OUT)
