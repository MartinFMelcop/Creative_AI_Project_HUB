extends SceneTree
## Refutable snapshot-only presentation checks; no local Combat instance.
const Remote=preload("../authority/remote.gd")
var checks:=0
var failed:Array=[]
func check(condition: bool, label: String) -> void:
	checks+=1
	if not condition: failed.append(label)
func frame(tick: int, player: Vector2, courier: Vector2, mode: String="play") -> Dictionary:
	return {"v":1,"kind":"state","tick":tick,"ack":-1,"quarantined":false,"state":{
		"mode":mode,"role":"Guardian","player":[player.x,player.y],"courier":[courier.x,courier.y],"hp":5,"cargo":3,"energy":100.0,
		"tick":tick,"health_limit":5,"enemy_focus":3,"guard_style":"Steady","guard_state":"DOWN","guard":false,"redirected":false,
		"facing":[1,0],"locked_face":[1,0],"target":[0,0],"pulse":[0,0],"step_dir":[0,0],
		"step_left":0.0,"strike_cooldown":0.0,"feint_cooldown":0.0,"step_cooldown":0.0,"opening":0.0,"clock":0.0,
		"message":"Server-owned crossing.","last_impact":{},"counters":{"counters":0},"phase":"rest",
		"actions":{"counter_radius":130.0,"draw_radius":340.0,
			"step":{"status":"ready","cost":25.0,"wait":0.0,"drain":0.0},
			"counter":{"status":"armored","cost":12.0,"wait":0.0,"drain":0.0},
			"technique":{"status":"hold","cost":22.0,"wait":0.0,"drain":12.0}}}}
func remote():
	var value=Remote.new()
	value.receive_message({"v":1,"kind":"welcome","session":"0123456789abcdef0123456789abcdef"})
	return value
func pump(value, seconds: float=.03) -> void:
	var until=Time.get_ticks_msec()+int(seconds*1000)
	while Time.get_ticks_msec()<until:
		value.poll(.001)
		OS.delay_usec(1000)
func socket_checks() -> void:
	var listener=TCPServer.new()
	var port:int=35000+OS.get_process_id()%20000
	var listening:=false
	for index in 20:
		if listener.listen(port,"127.0.0.1")==OK: listening=true; break
		port+=1
	check(listening,"Loopback fixture binds an actual TCP server")
	if not listening: return
	var value=Remote.new()
	check(value.connect_session(port),"Transport starts asynchronous loopback connect")
	pump(value)
	if not listener.is_connection_available():
		check(false,"Loopback connection reaches fixture"); value.close(); listener.stop(); return
	var peer:StreamPeerTCP=listener.take_connection(); peer.set_no_delay(true); peer.poll()
	var hello_bytes:PackedByteArray=peer.get_data(peer.get_available_bytes())[1]
	var hello=JSON.parse_string(hello_bytes.get_string_from_utf8().strip_edges())
	check(hello is Dictionary and hello.kind=="hello" and hello.role=="Guardian","Real TCP receives the canonical hello")
	peer.put_data((JSON.stringify({"v":1,"kind":"welcome","session":"0123456789abcdef0123456789abcdef"})+"\n").to_utf8_buffer())
	var message:PackedByteArray=(JSON.stringify(frame(3,Vector2(100,200),Vector2(160,390)))+"\n").to_utf8_buffer()
	peer.put_data(message.slice(0,13)); pump(value)
	check(value.latest.is_empty(),"Partial TCP frame cannot create a snapshot")
	peer.put_data(message.slice(13)); pump(value)
	check(value.status=="live" and value.can_send(),"Complete real TCP snapshot enables one intent")
	check(value.send_intent({"move":Vector2(5,5),"aim":Vector2.RIGHT,"strike":true}),"Real TCP admits a finite quantized intent")
	check(not value.can_send() and not value.send_intent({}),"Repeated send cannot exceed monotonic heartbeat cadence")
	peer.poll(); var request_bytes:PackedByteArray=peer.get_data(peer.get_available_bytes())[1]
	var request=JSON.parse_string(request_bytes.get_string_from_utf8().strip_edges())
	check(request is Dictionary and request.seq==0 and request.move==[707.0,707.0] and request.strike and not request.has("hp"),"Wire intent contains normalized values and no local authority")
	# Fast new confirmations cannot buy another send; elapsed time can, without one.
	peer.put_data((JSON.stringify(frame(6,Vector2(110,200),Vector2(170,390)))+"\n").to_utf8_buffer()); pump(value,.005)
	check(not value.can_send(),"New confirmation cannot bypass heartbeat rate")
	pump(value,.06)
	check(value.can_send() and value.sequence==1,"Elapsed monotonic interval enables next sequence")
	check(value.send_intent({"guard":true}),"Held guard heartbeat does not require another snapshot")
	pump(value,.06)
	check(value.can_send() and value.latest.tick==6,"Same confirmed tick permits a fresh bounded heartbeat")
	peer.poll();peer.get_data(peer.get_available_bytes())
	value.advance_presentation(.3)
	check(value.status=="stale" and not value.send_intent({"guard":true,"move":Vector2.RIGHT}),"Stale heartbeat cannot preserve active intent")
	check(not value._transmit({"guard":true}),"Shared transmit guard cannot bypass stale neutral restriction")
	check(value.send_neutral(),"Stale transport can send only explicit neutral heartbeat")
	peer.poll();var neutral_bytes:PackedByteArray=peer.get_data(peer.get_available_bytes())[1]
	var neutral=JSON.parse_string(neutral_bytes.get_string_from_utf8().strip_edges())
	check(neutral is Dictionary and neutral.seq==2 and neutral.move==[0.0,0.0] and neutral.aim==[0.0,0.0] and not neutral.guard and not neutral.feint and not neutral.step and not neutral.strike,"Actual stale wire contains no prior held action")
	check(not value.send_neutral(),"Neutral heartbeats share the same rate bound")
	peer.put_data((JSON.stringify(frame(9,Vector2(120,200),Vector2(1001,390),"won"))+"\n").to_utf8_buffer()); pump(value)
	peer.disconnect_from_host(); pump(value)
	check(value.status=="terminal" and value.confirmed.mode=="won","Real TCP close retains confirmed terminal result")
	value.close(); listener.stop()
	var oversized_server=TCPServer.new()
	check(oversized_server.listen(port,"127.0.0.1")==OK,"Malformed-frame fixture binds")
	var bounded=Remote.new(); bounded.connect_session(port); pump(bounded)
	if oversized_server.is_connection_available():
		var oversized_peer:StreamPeerTCP=oversized_server.take_connection()
		oversized_peer.put_data("x".repeat(17000).to_utf8_buffer()); pump(bounded)
		check(bounded.status=="error" and bounded.latest.is_empty(),"Actual oversized unterminated authority frame fails closed")
		oversized_peer.disconnect_from_host()
	else: check(false,"Malformed fixture connected")
	bounded.close(); oversized_server.stop()
func _initialize() -> void:
	var value=remote()
	value.receive_message(frame(1,Vector2(100,200),Vector2(160,390)))
	check(value.status=="live" and value.position==Vector2(100,200),"First confirmed position snaps")
	check(value.confirmed.hp==5 and value.latest.tick==1,"Full envelope and confirmed model remain distinct")
	value.receive_message(frame(4,Vector2(110,200),Vector2(170,390)))
	check(value.position==Vector2(100,200),"New position starts from previous confirmation")
	value.advance_presentation(.025)
	check(value.position.is_equal_approx(Vector2(105,200)) and value.courier_position.is_equal_approx(Vector2(165,390)),"Both positions interpolate only inside confirmed segment")
	check(value.confirmed.player==[110.0,200.0],"Interpolation never alters confirmed position")
	value.advance_presentation(.1)
	check(value.position==Vector2(110,200),"Interpolation clamps; no extrapolation")
	value.receive_message(frame(4,Vector2(999,999),Vector2.ZERO))
	value.receive_message(frame(1,Vector2(888,888),Vector2.ZERO))
	check(value.latest.tick==4 and value.confirmed.player==[110.0,200.0] and value.snapshots==2,"Duplicate and older snapshots cannot roll back state")
	value.advance_presentation(.2)
	check(value.status=="stale" and value.position==Vector2(110,200),"Delayed authority freezes presentation")
	check(not value.send_intent({"move":Vector2.RIGHT}),"Stale authority blocks intent")
	value.receive_message(frame(7,Vector2(140,200),Vector2(200,390)))
	check(value.status=="live" and value.age==0 and value.position==Vector2(140,200),"Recovery snaps to actual latest state")
	var phase=frame(10,Vector2(150,200),Vector2(210,390)); phase.state.phase="bolt"
	value.receive_message(phase)
	check(value.position==Vector2(150,200),"Phase transition snaps to prevent contradictory threat geometry")
	var held=frame(13,Vector2(160,200),Vector2(220,390)); held.quarantined=true
	value.receive_message(held)
	check(value.position==Vector2(160,200) and value.reason.contains("Release"),"Quarantine snaps and explains rearm")
	value.receive_message(frame(16,Vector2(170,200),Vector2(1001,390),"won"))
	value.close(); value.advance_presentation(10)
	check(value.status=="terminal" and value.confirmed.mode=="won" and value.position==Vector2(170,200),"Confirmed terminal survives close without local stepping")
	value.receive_message(frame(19,Vector2(999,999),Vector2.ZERO))
	check(value.status=="terminal" and value.latest.tick==16 and value.position==Vector2(170,200),"Later nonterminal state cannot replace confirmed result after close")
	var negative=remote(); var paid=frame(1,Vector2(100,200),Vector2(160,390)); paid.state.clock=-1.2
	negative.receive_message(paid)
	check(negative.status=="live","Actual paid counter negative rest interval remains valid")
	var required=["tick","health_limit","enemy_focus","guard_style","guard_state","guard","redirected","facing","locked_face","target","pulse","step_dir","step_left","strike_cooldown","feint_cooldown","step_cooldown","opening","clock","message","last_impact","counters","actions"]
	for key in required:
		var missing=remote(); var incomplete=frame(1,Vector2(100,200),Vector2(160,390)); incomplete.state.erase(key)
		missing.receive_message(incomplete)
		check(missing.status=="error" and missing.confirmed.is_empty(),"Required view fact cannot be omitted: "+key)
	for mutation in [{"hp":999},{"player":[NAN,0]},{"courier":[1]},{"energy":-1},{"mode":"invented"},{"facing":[INF,0]},{"step_left":-1},{"health_limit":"5"},{"enemy_focus":true},{"phase":"guess"},{"guard_state":"guessed"},{"guard":"false"},{"redirected":1},{"guard_style":"none"},{"message":[]},{"counters":{"counters":"3"}},{"counters":{}},{"tick":2},{"last_impact":[]},{"opening":INF},{"clock":-100},{"guard":true}]:
		var invalid=remote(); var bad=frame(1,Vector2(100,200),Vector2(160,390))
		bad.state.merge(mutation,true); invalid.receive_message(bad)
		check(invalid.status=="error" and invalid.confirmed.is_empty(),"Malformed snapshot rejected: "+str(mutation.keys()[0]))
	for mutation in [{"counter_radius":NAN},{"draw_radius":0},{"step":{}},{"counter":{"status":"invented","cost":12,"wait":0,"drain":0}},{"technique":{"status":"hold","cost":true,"wait":0,"drain":12}},{"step":{"status":"ready","cost":25,"wait":-1,"drain":0}},{"counter":{"status":"ready","cost":12,"wait":0,"drain":INF}}]:
		var invalid=remote();var bad=frame(1,Vector2.ZERO,Vector2.ZERO)
		bad.state.actions.merge(mutation,true);invalid.receive_message(bad)
		check(invalid.status=="error","Malformed action advice fails closed: "+str(mutation.keys()[0]))
	var wrong=Remote.new(); wrong.receive_message(frame(1,Vector2.ZERO,Vector2.ZERO))
	check(wrong.status=="error","Unwelcomed state cannot establish authority")
	var choice=Remote.new()
	check(not choice.connect_session(80) and choice.status=="error","Invalid local port fails before connecting")
	check(not choice.connect_session(31000,"Duelist","Steady"),"Invalid role/style pair fails before connecting")
	var bounded=remote(); var nested={"v":1,"kind":"state"}; var cursor=nested
	for index in 10: cursor["nested"]={}; cursor=cursor.nested
	bounded.receive_message(nested)
	check(bounded.status=="error","Message nesting is bounded")
	socket_checks()
	print(JSON.stringify({"passed":checks-failed.size(),"failed":failed.size(),"failures":failed}))
	quit(0 if failed.is_empty() else 1)
