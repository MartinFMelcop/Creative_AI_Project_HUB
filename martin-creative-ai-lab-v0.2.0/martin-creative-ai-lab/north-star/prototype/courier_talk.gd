extends RefCounted
## One optional arrival conversation. Facts and confirmed aid belong to this journey.
const Combat=preload("res://combat.gd")
const OPTIONS:=["heal","brace","keep"]
var active:=false
var facts:Dictionary={}
var draft:=""
var choice:=""
var page:="offer"
var message:=""

func open(source,medicine: String) -> bool:
	if active or source.mode!="won" or source.hp<=0 or source.cargo<=0 or source.courier.x<Combat.FINISH:return false
	if facts.is_empty():
		facts={"role":source.role,"style":source.guard_style,"hp":source.hp,"health_limit":source.health_limit,
			"route":source.route.kind,"medicine":medicine,"blocks":source.counters.blocks,
			"redirects":source.counters.redirects,"disabled":source.sentinel_disabled(),"covered":source.route.covered}
	active=true;draft="";page="offer";message=""
	return true

func enabled(id: String) -> bool:
	if facts.is_empty() or not OPTIONS.has(id):return false
	return facts.hp<facts.health_limit if id=="heal" else true

func select(id: String) -> bool:
	if not active or page!="offer" or not choice.is_empty():return false
	if not enabled(id):
		message="You have no wound to bind. The strip is still unspent." if id=="heal" else "Choose one of the listed responses."
		draft="";return false
	draft=id;message="Selected only. ENTER confirms; ESC leaves the strip unspent."
	return true

func confirm() -> bool:
	if not active or page!="offer" or not choice.is_empty() or not enabled(draft):return false
	choice=draft;draft="";message=""
	return true

func close() -> void:
	active=false;draft="";page="offer";message=""

func suspend() -> void:
	if active and choice.is_empty():draft="";message="Selection cleared. Choose again before confirming."

func aid() -> String:
	return choice if choice in ["heal","brace"] else ""

func road_lines() -> Array[String]:
	if facts.is_empty():return []
	var lines:Array[String]=[]
	if facts.route=="ridge":lines.append("We took the ridge. The high screen caught %d bolts."%facts.covered)
	else:lines.append("We stayed on the road. You kept the way to this gate open.")
	if facts.role=="Guardian" and facts.blocks>0:lines.append("I saw you turn that shield toward the bolts meant for me.")
	elif facts.role=="Duelist" and facts.redirects>0:lines.append("You drew the bolts off my line. I had to trust you to move.")
	else:lines.append("We reached this gate alive. I won't pretend the road was safe.")
	if facts.disabled:lines.append("When its focus broke, I could run. I heard it go quiet.")
	else:lines.append("Its focus was still turning when I reached the gate.")
	if facts.medicine=="delivered":lines.append("The sealed case is with me. I'll carry it on to the clinic.")
	elif facts.medicine=="carried":lines.append("You recovered the case, but never handed it to me. It isn't delivered.")
	else:lines.append("The medicine never reached my hands. I can't promise it to the clinic.")
	return lines

func reply_lines() -> Array[String]:
	match choice:
		"heal":return ["Sit. I'll bind that wound just before you leave.","The strip is set aside for your arm; it can't also hold the winch.","Start the return with +1 health, up to your fitted limit."]
		"brace":return ["Then take it for the winch. Thread it through the cracked housing.","Your arrival health stays as it is.","Your return winch starts at 3 integrity instead of 2."]
		"keep":return ["All right. I'll keep it for the road ahead.","You leave with your arrival health and the ordinary winch.","No aid is applied. You can still attempt the return gate."]
	return ["One strip left in my repair roll. Your wound, or that winch?" if facts.get("hp",0)<facts.get("health_limit",0) else "One strip left. Will you need it for that cracked winch?", "I can spare it. But it can't do both jobs."]

func snapshot() -> Dictionary:
	return {"active":active,"facts":facts.duplicate(true),"draft":draft,"choice":choice,"page":page,"message":message}
