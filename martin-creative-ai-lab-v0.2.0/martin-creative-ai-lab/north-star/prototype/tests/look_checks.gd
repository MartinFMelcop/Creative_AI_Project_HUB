extends SceneTree
const Look=preload("res://character_look.gd")
const Arena=preload("res://arena.gd")
const Actors=preload("res://actors.gd")
const Policy=preload("res://tests/policy.gd")
const GatePolicy=preload("res://tests/gate_policy.gd")
var passed:=0
var failed:=0
var journeys:=[]
func check(value: bool,label: String) -> void:
	if value:passed+=1
	else:failed+=1;push_error(label)
func key(a,code: int) -> void:
	var event=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=true;a._unhandled_key_input(event)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var look=Look.new();check(look.applied==Look.DEFAULTS and not look.active,"New process starts with original look")
	look.cycle(1);check(look.applied==Look.DEFAULTS,"Closed editor cannot change look")
	look.enter("Guardian","Riposte","riveted");look.cycle(-1)
	check(look.draft.skin==3 and look.applied.skin==0,"Wrapped draft never applies implicitly")
	look.cancel();check(look.draft==Look.DEFAULTS and not look.active,"Cancel discards draft")
	look.enter("Duelist","Steady","trail");look.draft={"skin":2,"hair":2,"dye":1};look.confirm()
	check(look.applied=={"skin":2,"hair":2,"dye":1},"Apply commits independent visual choices")
	look.draft.skin=0;check(look.applied.skin==2,"Applied choice does not alias draft")
	look.enter("Guardian","Steady","standard");check(look.draft==look.applied,"Reopen starts at applied look")
	for field in Look.FIELDS:
		look.row=Look.FIELDS.find(field)
		var initial:int=look.draft[field]
		for i in Look.NAMES[field].size():look.cycle(1)
		check(look.draft[field]==initial,"Complete choice cycle is stable: "+field)
	look.pose_index=1;look.reset_preview();var start:Vector2=look.preview.player
	look.step(.05);check(look.preview.player.x>start.x,"Walk preview executes actual movement")
	look.paused=true;var frozen=look.preview.snapshot();look.step(.05)
	check(look.preview.snapshot()==frozen,"Focus suspension freezes preview")
	look.paused=false;look.role="Guardian";look.pose_index=2;look.reset_preview();look.step(.05)
	check(look.preview.guard,"Response preview executes actual Guardian guard")
	look.role="Duelist";look.reset_preview();look.step(.05)
	check(look.preview.redirected and look.preview.counters.redirects==1,"Response preview executes paid Duelist draw")
	look.pose_index=3;look.reset_preview();look.step(.05)
	check(look.preview.step_left>0 and look.preview.counters.dodges==1,"Step preview executes paid step")
	look.pose_index=4;look.reset_preview();look.step(.05)
	check(look.preview.strike_cooldown>0 and look.preview.counters.counters==0,"Blade sample is actual armor strike, not fake counter")
	var a=Arena.new();root.add_child(a);a.set_physics_process(false)
	var before=a.game.snapshot();var reward=a.keepsakes.snapshot();var fitting=a.workshop.snapshot()
	key(a,KEY_F3);check(a.character_look.active,"Actual title opens editor")
	key(a,KEY_RIGHT);key(a,KEY_DOWN);key(a,KEY_RIGHT);key(a,KEY_DOWN);key(a,KEY_RIGHT)
	check(a.character_look.draft=={"skin":1,"hair":1,"dye":1} and a.character_look.applied==Look.DEFAULTS,"Actual arrows change draft only")
	key(a,KEY_2);key(a,KEY_TAB);key(a,KEY_SPACE);a._physics_process(.05)
	check(a.selected=="Guardian" and a.workshop.snapshot()==fitting,"Preview role/fitting never changes real choices")
	check(a.game.snapshot()==before and a.keepsakes.snapshot()==reward,"Preview cannot progress live world or award marks")
	a.character_look.pose_index=2;a.character_look.reset_preview();a._physics_process(1.0/60)
	check(a.look_actor.pose(a.character_look.preview)=="draw","Changing preview model retains its first accepted draw gesture")
	a.character_look.pose_index=4;a.character_look.reset_preview();a._physics_process(1.0/60)
	check(a.look_actor.pose(a.character_look.preview)=="blade","First paid blade action is actually shown")
	var previous_preview=a.character_look.preview
	for i in 60:
		a._physics_process(1.0/60)
		if a.character_look.preview!=previous_preview:break
	a._physics_process(1.0/60)
	check(a.character_look.preview!=previous_preview and a.look_actor.pose(a.character_look.preview)=="blade","Natural preview loop retains the next first action")
	a.open_controls();var preview_before=a.character_look.preview.snapshot();a._physics_process(.05)
	check(a.character_look.preview.snapshot()==preview_before,"Controls freeze preview")
	key(a,KEY_ESCAPE);key(a,KEY_ESCAPE);check(not a.character_look.active and a.character_look.applied==Look.DEFAULTS,"Native discard keeps actual look")
	key(a,KEY_F3);key(a,KEY_RIGHT);key(a,KEY_ENTER)
	check(a.character_look.applied.skin==1 and not a.character_look.active,"Native apply commits appearance")
	key(a,KEY_F3);key(a,KEY_DELETE);key(a,KEY_ESCAPE)
	check(a.character_look.applied.skin==1,"Defaults stay a reversible draft until apply")
	a.begin_crossing();key(a,KEY_F3);check(not a.character_look.active,"Live consumer cannot open title-only editor")
	a.abandon();check(a.character_look.applied.skin==1,"Approach replacement retains session appearance")
	check(Look.new().applied==Look.DEFAULTS,"Fresh instance retains session-only boundary")
	a.free()
	for role in ["Guardian","Duelist"]:
		for custom in [false,true]:
			a=Arena.new();root.add_child(a);a.set_physics_process(false);a.selected=role
			if custom:
				a.character_look.enter(role,"Steady","standard");a.character_look.draft={"skin":3,"hair":2,"dye":3};a.character_look.confirm()
			a.begin_crossing()
			for i in 4200:
				if a.game.mode!="play":break
				a.advance_crossing(1.0/60,{} if i<170 else Policy.command(a.game));a.actors.observe(a.game)
			check(a.game.mode=="won","Complete escort: "+role+str(custom))
			var first=a.game.snapshot();check(a.begin_return_gate(),"Continue actual outcome")
			for i in 6000:
				if a.game.mode!="play":break
				a.advance_crossing(1.0/60,GatePolicy.command(a.return_gate,"work"));a.actors.observe(a.game)
			check(a.game.mode=="won","Complete second goal: "+role+str(custom))
			check(a.character_look.applied==({"skin":3,"hair":2,"dye":3} if custom else Look.DEFAULTS),"Look survives both actual goals")
			journeys.append({"role":role,"custom":custom,"look":a.character_look.applied.duplicate(),"crossing":first,"return_gate":a.return_gate.snapshot()})
			a.free()
	for i in [0,2]:
		check(journeys[i].crossing==journeys[i+1].crossing and journeys[i].return_gate==journeys[i+1].return_gate,"Custom and original look have exactly equal mechanical journeys")
	var hashes={}
	for name in ["character_look.gd","actors.gd","arena.gd","tests/look_checks.gd"]:hashes[name]=FileAccess.get_sha256("res://"+name)
	var report={"checks":{"passed":passed,"failed":failed},"consumer_hashes":hashes,"journeys":journeys}
	var args=OS.get_cmdline_user_args()
	if args.size()==1:
		var file=FileAccess.open(args[0],FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n")
	print("LOOK_CHECKS ",passed," passed / ",failed," failed");quit(1 if failed else 0)
