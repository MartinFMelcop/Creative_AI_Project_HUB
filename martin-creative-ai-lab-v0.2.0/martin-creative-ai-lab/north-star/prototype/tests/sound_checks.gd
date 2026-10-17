extends RefCounted
const Sound = preload("res://sound.gd")
const Combat = preload("res://combat.gd")
const Trial = preload("res://tests/rehearsal_checks.gd")
const ControlsChecks = preload("res://tests/controls_checks.gd")

static func names(sound) -> Array:
	return sound.history.map(func(e):return e.cue)

static func run(checker) -> Dictionary:
	var samples := {};var identities := []
	for name in Sound.NAMES:
		var stream=Sound.stream_for(name)
		var peak := 0;var total := 0.0
		for i in stream.data.size()/2:
			var value: int=stream.data.decode_s16(i*2)
			peak=maxi(peak,absi(value));total+=value
		var hash=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(stream.data)
		var digest: String=hash.finish().hex_encode();identities.append(digest)
		checker.check(stream.mix_rate==22050 and not stream.stereo and stream.data.size()==roundi(Sound.LENGTHS[name]*22050)*2 and peak>100 and peak<16384 and absi(stream.data.decode_s16(0))<5 and absi(stream.data.decode_s16(stream.data.size()-2))<5,"Cue "+name+" is bounded non-silent unclipped mono PCM with soft endpoints")
		samples[name]={"pcm_sha256":digest,"frames":stream.data.size()/2,"peak":peak,"mean":snappedf(total/(stream.data.size()/2),0.001)}
	var unique := {}
	for identity in identities:unique[identity]=true
	checker.check(identities.size()==8 and identities.size()==unique.size(),"Threat and character-response cues have distinct PCM identities")
	var node=ControlsChecks.scene(checker,"sound")
	checker.check(node.sound.voices.size()==2 and node.sound.history.is_empty(),"Actual title starts silent with only two bounded voices")
	node.begin_crossing();node.game.clock=1.79;node._physics_process(0.02)
	checker.check(names(node.sound)==["bolt"],"Actual phase transition emits one bolt warning")
	for i in 8:node._physics_process(0.02)
	checker.check(names(node.sound)==["bolt"],"Held warning does not repeat every frame")
	Trial.key(node,KEY_ESCAPE)
	checker.check(not node.sound.voices[0].playing and not node.sound.voices[1].playing,"Actual pause immediately stops active voices")
	Trial.key(node,KEY_ENTER);node._physics_process(0.02)
	checker.check(names(node.sound)==["bolt"],"Resume does not replay an old warning")
	node.game.player=Vector2(550,390);node.game.facing=Vector2.RIGHT;node.game.clock=0.89
	node.taps.skill=true
	# Real held skill polling is separate; prepare live model guard through real commands.
	for i in 3:node.game.step(0.05,{"skill":true})
	node.sync_sound()
	checker.check(names(node.sound).back()=="block" and node.game.counters.blocks==1,"Successful frontal contact has its own resonant block cue")
	node.selected="Duelist";node.begin_crossing();node.game.phase="bolt";node.game.target=node.game.courier
	Trial.key(node,KEY_K);node._physics_process(0.02)
	checker.check(names(node.sound)==["bolt","draw"] and node.game.counters.redirects==1,"Actual Duelist input sounds only an accepted redirection")
	Trial.key(node,KEY_K);node._physics_process(0.02)
	checker.check(names(node.sound)==["bolt","draw"],"Rejected repeated feint has no false success sound")
	node.begin_crossing();node.game.cycle=2;node.game.clock=1.79;node._physics_process(0.02)
	checker.check(names(node.sound)==["pulse"],"Floor warning uses the distinct low pulse cue")
	node.game.clock=0.99;node._physics_process(0.02)
	checker.check(names(node.sound).back()=="hurt" and node.game.hp==4,"Actual damaging pulse emits hurt feedback")

	node.begin_crossing();node.game.player=Combat.ENEMY+Vector2(-100,0);node.game.opening=1
	Trial.key(node,KEY_J);node._physics_process(0.02)
	checker.check(names(node.sound)==["counter"] and node.game.counters.counters==1,"A reachable real counter emits its dry contact cue")
	node.begin_crossing();node.game.courier.x=999.9;node._physics_process(0.02);node._physics_process(0.02)
	checker.check(names(node.sound)==["won"],"Terminal victory cadence plays once, not every result frame")
	node.begin_crossing();node.game.hp=0;node._physics_process(0.02)
	checker.check(names(node.sound)==["lost"],"Defeat cadence follows actual terminal ownership")
	Trial.key(node,KEY_R)
	checker.check(node.sound.history.is_empty() and not node.sound.voices[1].playing,"Abandon/reselection clears old voices and event history")

	Trial.key(node,KEY_F1);Trial.key(node,KEY_F5)
	checker.check(node.controls_open and node.sound.muted,"F5 in actual settings mutes cues without changing control bindings")
	Trial.key(node,KEY_ESCAPE);node.begin_crossing();node.game.clock=1.79;node._physics_process(0.02)
	checker.check(node.sound.history.is_empty(),"Muted gameplay consumes transitions silently")
	Trial.key(node,KEY_F1);Trial.key(node,KEY_F5);Trial.key(node,KEY_ESCAPE);Trial.key(node,KEY_ENTER);node._physics_process(0.02)
	checker.check(node.sound.history.is_empty(),"Unmuting and resuming never replays muted history")
	Trial.key(node,KEY_T) # No live-play management effect.
	node.game.phase="rest";node.game.clock=1.79;node.game.cycle=2;node._physics_process(0.02)
	checker.check(names(node.sound)==["pulse"],"New threats sound normally after explicit unmute")
	node._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	checker.check(node.game.mode=="paused" and not node.sound.voices[0].playing,"Focus loss pauses and immediately silences the native consumer")
	var late=Combat.new();late.reset("Guardian");late.elapsed=30;late.mode="won";late.record("protected")
	node.sound.observe(late)
	checker.check(node.sound.history.is_empty(),"Attaching to an old model never replays historical contact or victory")
	var report={"cues":samples,"voice_limit":2,"mute_is_session_only":true}
	node.queue_free()
	return report
