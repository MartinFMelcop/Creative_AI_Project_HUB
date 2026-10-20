extends SceneTree
## Exercise the optional conversation through the real arrival and return consumer.
const Combat=preload("res://combat.gd")
const Talk=preload("res://courier_talk.gd")
const Gate=preload("res://return_gate.gd")
const Arena=preload("res://arena.gd")
const Policy=preload("res://tests/policy.gd")
const GatePolicy=preload("res://tests/gate_policy.gd")
var passed:=0
var failed:=0
var assertions:Array[String]=[]
var journeys:=[]

func check(value: bool,label: String) -> void:
	assertions.append(label)
	if value:passed+=1
	else:failed+=1;push_error(label)

func arrival(role: String="Guardian"):
	var source=Combat.new();source.reset(role)
	source.hp=3;source.energy=44;source.courier.x=Combat.FINISH;source.mode="won"
	return source

func key(scene,code: int) -> void:
	var event=InputEventKey.new();event.pressed=true;event.physical_keycode=code;event.keycode=code
	scene._unhandled_key_input(event)

func actual_arrival(role: String):
	var scene=Arena.new();root.add_child(scene);scene.set_physics_process(false)
	scene.selected=role;scene.begin_crossing()
	for i in 4200:
		if scene.game.mode!="play":break
		# Real unprotected first contact supplies the wound used by the aid choices.
		scene.advance_crossing(1.0/60,{} if i<170 else Policy.command(scene.game))
	return scene

func _initialize() -> void:call_deferred("run")

func run() -> void:
	var talk=Talk.new();var source=Combat.new();source.reset("Guardian")
	check(not talk.select("heal"),"Closed conversation cannot select aid")
	check(not talk.confirm(),"Closed conversation cannot confirm aid")
	check(not talk.open(source,"available"),"Live crossing cannot open aftermath")
	source.mode="lost";check(not talk.open(source,"available"),"Defeat cannot open aftermath")
	source.mode="won";check(not talk.open(source,"available"),"Won label without arrival cannot open aftermath")
	source=arrival();source.hp=0;check(not talk.open(source,"carried"),"Dead player cannot negotiate aid")
	source=arrival();source.cargo=0;check(not talk.open(source,"delivered"),"Lost courier cannot negotiate aid")
	source=arrival();source.route.kind="ridge";source.counters.blocks=2;source.route.covered=3
	var before=source.snapshot()
	check(talk.open(source,"carried"),"Genuine wounded arrival opens aftermath")
	check(talk.facts.role==source.role and talk.facts.hp==3 and talk.facts.health_limit==5 and talk.facts.route=="ridge" and talk.facts.covered==3 and talk.facts.medicine=="carried" and talk.facts.blocks==2 and talk.facts.redirects==0 and not talk.facts.disabled,"Conversation records actual route medicine and response facts")
	check(source.snapshot()==before,"Opening conversation does not change arrival")
	check(not talk.select("unknown") and talk.draft=="","Unknown aid is rejected without a draft")
	check(not talk.confirm() and talk.choice=="","Confirmation without a selected offer is inert")
	talk.page="road"
	check(not talk.select("brace") and not talk.confirm() and talk.aid()=="","Information branch cannot consume the single strip")
	talk.page="offer"
	check(talk.select("heal") and talk.draft=="heal","Wounded character can explicitly select dressing")
	check(talk.aid()=="" and talk.choice=="","Selected aid remains uncommitted")
	talk.page="road";check(not talk.confirm() and talk.choice=="","Information page cannot confirm an earlier offer selection");talk.page="offer"
	talk.close();check(not talk.active and talk.draft=="" and talk.choice=="","Closing discards an unconfirmed offer")
	check(talk.open(source,"carried") and talk.draft=="","Reopening does not silently restore discarded aid")
	talk.select("brace");check(talk.confirm() and talk.choice=="brace" and talk.aid()=="brace","Confirmation commits the single strip to the winch")
	talk.close();talk.open(source,"carried")
	check(talk.choice=="brace" and talk.aid()=="brace","Reopening preserves the committed offer")
	check(not talk.confirm(),"Repeated confirmation cannot issue another strip")
	check(not talk.select("heal") and talk.choice=="brace","Committed strip cannot also become dressing")
	check(source.snapshot()==before,"Neither conversation commitment nor reentry mutates completed escort")
	var captured=talk.facts.duplicate(true);source.hp=1;source.counters.blocks=8
	check(talk.facts==captured,"Remembered arrival facts do not alias later source changes")
	var accounts=[]
	for medicine in ["available","carried","delivered"]:
		source=arrival("Duelist");source.counters.redirects=2;source.enemy_focus=0
		var witness=Talk.new();witness.open(source,medicine)
		check(witness.facts.redirects==2 and witness.facts.disabled and witness.facts.medicine==medicine,"Actual draw and shutdown facts reach witness memory: "+medicine)
		accounts.append(witness.road_lines())
	check(accounts[0]!=accounts[1] and accounts[1]!=accounts[2] and accounts[0]!=accounts[2],"Undelivered recovered and delivered medicine receive distinct accounts")
	source=arrival();source.hp=source.health_limit;talk=Talk.new();talk.open(source,"available")
	check(not talk.enabled("heal"),"Full health exposes dressing as unavailable")
	check(not talk.select("heal") and talk.choice=="" and talk.aid()=="","Unavailable dressing cannot consume strip")
	var room=Gate.new()
	check(not room.begin(arrival(),"carried","unknown") and not room.active,"Return checkpoint rejects an unknown aid identifier")
	check(not room.begin(source,"carried","heal") and not room.active,"Return checkpoint rejects dressing at full health")
	for aid in ["heal","brace"]:
		source=arrival();before=source.snapshot();room=Gate.new();room.begin(source,"delivered",aid)
		check(room.game.hp==(4 if aid=="heal" else 3) and room.game.cargo==(3 if aid=="brace" else 2),"Committed aid changes only its promised initial resource: "+aid)
		check(room.entry.hp==3 and room.game.energy==44 and source.snapshot()==before,"Aid preserves source health and carried energy: "+aid)
		room.game.hp=1;room.game.cargo=1;room.retry();var checkpoint=room.snapshot();room.retry()
		check(room.snapshot()==checkpoint and room.game.hp==(4 if aid=="heal" else 3) and room.game.cargo==room.cargo_limit(),"Retry restores fixed prepared checkpoint without accumulating aid: "+aid)
	source=arrival();room=Gate.new();before=source.snapshot();room.begin(source,"carried")
	check(room.entry=={"role":"Guardian","style":"Steady","outfit":"standard","hp":3,"energy":44.0,"route":"road","medicine":"carried"},"Skipping conversation retains exact original checkpoint contract")
	check(source.snapshot()==before and room.game.hp==3 and room.game.cargo==2,"Skipped offer grants no aid or source mutation")
	var scene=Arena.new();root.add_child(scene);scene.set_physics_process(false)
	key(scene,KEY_F4);check(not scene.courier_talk.active,"Actual title rejects conversation")
	scene.begin_crossing();key(scene,KEY_F4);check(not scene.courier_talk.active,"Actual live adapter rejects conversation")
	scene.bindings.keys.strike=KEY_F4;scene.bindings.refresh_labels();scene.game.player=Combat.ENEMY+Vector2(-100,0);scene.game.opening=1.0
	key(scene,KEY_F4);scene._physics_process(1.0/60)
	check(scene.game.counters.counters==1 and not scene.courier_talk.active,"New result key preserves an existing live F4 gameplay remap")
	scene.game.mode="lost";key(scene,KEY_F4);check(not scene.courier_talk.active,"Actual defeat adapter rejects conversation")
	scene.game.mode="won";key(scene,KEY_F4);check(not scene.courier_talk.active,"Actual won label still needs genuine arrival geometry")
	scene.game=arrival();key(scene,KEY_F4);check(scene.courier_talk.active,"Actual F4 opens eligible conversation")
	before=scene.game.snapshot();key(scene,KEY_1);scene._physics_process(.05)
	check(scene.game.snapshot()==before and scene.courier_talk.draft=="heal" and scene.courier_talk.aid()=="","Actual choice preview freezes completed world and grants nothing")
	key(scene,KEY_F1);check(scene.controls_open and scene.courier_talk.draft=="","Opening settings disarms pending confirmation")
	key(scene,KEY_ESCAPE);check(not scene.controls_open and scene.courier_talk.active,"Closing settings returns to conversation")
	key(scene,KEY_TAB);check(scene.courier_talk.page=="road","Actual information branch can recall crossing without spending strip")
	key(scene,KEY_TAB);key(scene,KEY_2);scene._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(scene.courier_talk.draft=="" and scene.courier_talk.choice=="","Focus loss cannot leave an armed aid confirmation")
	key(scene,KEY_1);key(scene,KEY_ESCAPE)
	check(not scene.courier_talk.active and scene.courier_talk.choice=="","Actual Escape closes and discards selected aid")
	key(scene,KEY_F4);key(scene,KEY_2);key(scene,KEY_F2)
	check(scene.return_gate.active and scene.game.hp==3 and scene.game.cargo==2 and scene.courier_talk.choice=="","Actual departure ignores unconfirmed draft")
	key(scene,KEY_F4);check(not scene.courier_talk.active,"Live return objective cannot reopen conversation")
	scene.game.mode="paused";key(scene,KEY_R)
	check(not scene.courier_talk.active and scene.courier_talk.choice=="" and scene.courier_talk.facts.is_empty(),"Abandon clears conversation and its checkpoint ownership")
	scene.begin_crossing();scene.game=arrival();key(scene,KEY_F4);key(scene,KEY_2);key(scene,KEY_ENTER)
	check(scene.courier_talk.choice=="brace" and scene.game.hp==3,"Actual confirmation records a gift without live healing")
	key(scene,KEY_ESCAPE);key(scene,KEY_F4)
	check(scene.courier_talk.choice=="brace" and scene.courier_talk.aid()=="brace","Actual reopen cannot renew confirmed gift")
	scene.begin_crossing();check(scene.courier_talk.facts.is_empty() and scene.courier_talk.choice=="","New crossing clears the previous conversation")
	check(Talk.new().facts.is_empty() and Talk.new().choice=="","Fresh instance grants no remembered aid")
	for medicine in ["available","carried","delivered"]:
		scene.begin_crossing();scene.game=arrival("Duelist");scene.errand.state=medicine;key(scene,KEY_F4)
		check(scene.courier_talk.facts.medicine==medicine and scene.courier_talk.facts.role=="Duelist","Scene forwards current case ownership and actual approach: "+medicine)
	scene.free()
	for role in ["Guardian","Duelist"]:
		var measured=[]
		for choice in ["","heal","brace","keep"]:
			scene=actual_arrival(role)
			check(scene.game.mode=="won" and scene.game.hp<scene.game.health_limit,"Actual wounded crossing precedes choice: "+role+"/"+choice)
			var first=scene.game.snapshot();var earned=scene.keepsakes.earned.duplicate()
			if not choice.is_empty():
				key(scene,KEY_F4);check(scene.courier_talk.active,"Complete journey opens its real conversation: "+role+"/"+choice)
				key(scene,KEY_1 if choice=="heal" else (KEY_2 if choice=="brace" else KEY_3));key(scene,KEY_ENTER)
				check(scene.courier_talk.choice==choice,"Complete journey confirms the intended choice: "+role+"/"+choice)
			var memory=scene.courier_talk.snapshot();key(scene,KEY_F2)
			var entry=scene.return_gate.snapshot()
			check(scene.return_gate.active and scene.game.hp==first.hp+(1 if choice=="heal" else 0) and scene.game.cargo==(3 if choice=="brace" else 2),"Complete journey consumes only confirmed aid: "+role+"/"+choice)
			for i in 6000:
				if scene.game.mode!="play":break
				scene.advance_crossing(1.0/60,GatePolicy.command(scene.return_gate,"work"))
			check(scene.game.mode=="won" and scene.return_gate.opened() and scene.keepsakes.earned==earned,"Choice reaches actual exit without duplicate keepsake: "+role+"/"+choice)
			var record={"role":role,"choice":choice,"crossing":first,"conversation":memory,"entry":entry,"return_gate":scene.return_gate.snapshot()}
			journeys.append(record);measured.append(record);scene.free()
		for index in [1,2,3]:
			check(measured[0].crossing==measured[index].crossing,"Matched escort precedes every aid alternative: "+role+"/"+str(index))
		check(measured[0].entry==measured[3].entry and measured[0].return_gate==measured[3].return_gate,"Keeping strip retains exact no-conversation mechanical journey: "+role)
		check(measured[1].entry.game.hp==measured[0].entry.game.hp+1 and measured[1].entry.game.cargo==measured[0].entry.game.cargo,"Dressing changes health without repairing winch: "+role)
		check(measured[2].entry.game.cargo==measured[0].entry.game.cargo+1 and measured[2].entry.game.hp==measured[0].entry.game.hp,"Winch gift changes integrity without healing character: "+role)
	var hashes={}
	for name in ["courier_talk.gd","return_gate.gd","arena.gd","combat.gd","tests/conversation_checks.gd","tests/policy.gd","tests/gate_policy.gd"]:
		hashes[name]=FileAccess.get_sha256("res://"+name)
	var report={"checks":{"passed":passed,"failed":failed},"assertions":assertions,"consumer_hashes":hashes,"journeys":journeys}
	var args=OS.get_cmdline_user_args()
	if args.size()==1:
		var file=FileAccess.open(args[0],FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n")
	print("CONVERSATION_CHECKS ",passed," passed / ",failed," failed")
	for child in root.get_children():child.queue_free()
	await create_timer(.1).timeout
	quit(1 if failed else 0)
