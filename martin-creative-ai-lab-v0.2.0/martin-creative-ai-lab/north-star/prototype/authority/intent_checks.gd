extends SceneTree
## Native event-adapter controls; no Combat instance or model stepping.
const Intent=preload("intent.gd")
var passed:=0
var failed:=0
func check(condition:bool,label:String) -> void:
	if condition:passed+=1
	else:failed+=1;push_error(label)
func key(adapter,code:int,pressed:bool,echo:bool=false,physical:bool=false) -> void:
	var event:=InputEventKey.new();event.pressed=pressed;event.echo=echo
	if physical:event.physical_keycode=code
	else:event.keycode=code
	adapter.receive(event)
func mouse(adapter,button:int,pressed:bool) -> void:
	var event:=InputEventMouseButton.new();event.button_index=button;event.pressed=pressed;adapter.receive(event)
func neutral(value:Dictionary) -> bool:
	return value.move==Vector2.ZERO and not value.guard and not value.feint and not value.step and not value.strike
func _initialize() -> void:
	var adapter=Intent.new()
	check(not adapter.suspended and not adapter.quarantined,"Fresh adapter accepts explicit input")
	for code in [KEY_J,KEY_SPACE,KEY_L]:
		var action:String={KEY_J:"feint",KEY_SPACE:"step",KEY_L:"strike"}[code]
		key(adapter,code,true);key(adapter,code,false)
		check(adapter.command(Vector2.RIGHT)[action],"Quick tap survives until sample: "+action)
		check(not adapter.command(Vector2.RIGHT)[action],"Release packet follows pulse: "+action)
		check(not adapter.command(Vector2.RIGHT)[action],"Tap cannot repeat: "+action)
		key(adapter,code,true)
		check(adapter.command(Vector2.RIGHT)[action],"Fresh press fires: "+action)
		key(adapter,code,true,true);key(adapter,code,true)
		check(not adapter.command(Vector2.RIGHT)[action] and not adapter.command(Vector2.RIGHT)[action],"Held/repeated events do not fire: "+action)
		key(adapter,code,false);key(adapter,code,true)
		check(adapter.command(Vector2.RIGHT)[action],"Release permits next press: "+action)
		key(adapter,code,false);key(adapter,code,true);key(adapter,code,false)
		check(not adapter.command(Vector2.RIGHT)[action],"Repress waits for mandatory false packet: "+action)
		check(adapter.command(Vector2.RIGHT)[action],"Queued repress survives false packet: "+action)
		adapter.command(Vector2.RIGHT)
	# Two complete taps between samples preserve their distinct rising edges.
	key(adapter,KEY_SPACE,true);key(adapter,KEY_SPACE,false);key(adapter,KEY_SPACE,true);key(adapter,KEY_SPACE,false)
	check(adapter.command(Vector2.RIGHT).step and not adapter.command(Vector2.RIGHT).step and adapter.command(Vector2.RIGHT).step,"Two quick taps retain two separated pulses")
	adapter.command(Vector2.RIGHT)
	key(adapter,KEY_W,true,false,true);key(adapter,KEY_D,true,false,true)
	var movement:Vector2=adapter.command(Vector2.RIGHT).move
	check(is_equal_approx(movement.length(),1) and movement.x>0 and movement.y<0,"Physical WASD normalizes diagonal movement")
	key(adapter,KEY_W,false,false,true);key(adapter,KEY_D,false,false,true)
	key(adapter,KEY_DOWN,true);key(adapter,KEY_LEFT,true)
	movement=adapter.command(Vector2.RIGHT).move
	check(is_equal_approx(movement.length(),1) and movement.x<0 and movement.y>0,"Logical arrows provide alternative movement")
	key(adapter,KEY_DOWN,false);key(adapter,KEY_LEFT,false)
	key(adapter,KEY_A,true);key(adapter,KEY_RIGHT,true)
	check(adapter.command(Vector2.RIGHT).move==Vector2.ZERO,"Opposing bindings cancel")
	key(adapter,KEY_A,false);key(adapter,KEY_RIGHT,false)
	key(adapter,KEY_K,true);mouse(adapter,MOUSE_BUTTON_RIGHT,true);key(adapter,KEY_K,false)
	check(adapter.command(Vector2.RIGHT).guard,"Either held guard binding retains guard")
	mouse(adapter,MOUSE_BUTTON_RIGHT,false)
	check(not adapter.command(Vector2.RIGHT).guard,"Both guard bindings must release")
	mouse(adapter,MOUSE_BUTTON_LEFT,true)
	check(adapter.command(Vector2.RIGHT).strike,"Left mouse produces strike edge")
	key(adapter,KEY_L,true);mouse(adapter,MOUSE_BUTTON_LEFT,false)
	adapter.command(Vector2.RIGHT)
	check(not adapter.command(Vector2.RIGHT).strike,"Overlapping strike bindings are one held action")
	key(adapter,KEY_L,false)
	key(adapter,KEY_K,true);key(adapter,KEY_W,true);key(adapter,KEY_SPACE,true)
	adapter.suspend()
	check(adapter.suspended and adapter.quarantined and neutral(adapter.command(Vector2.RIGHT)),"Suspend clears movement, guard and queued actions")
	adapter.resume()
	check(not adapter.suspended and adapter.quarantined and neutral(adapter.command(Vector2.RIGHT)),"Resume cannot rearm held controls")
	key(adapter,KEY_K,false);key(adapter,KEY_W,false)
	check(adapter.quarantined,"Partial release cannot leave quarantine")
	key(adapter,KEY_SPACE,false)
	check(not adapter.quarantined and neutral(adapter.command(Vector2.RIGHT)),"Complete release rearms without an action")
	key(adapter,KEY_J,true);key(adapter,KEY_J,false)
	check(adapter.command(Vector2.RIGHT).feint,"New press after release works")
	adapter.suspend();key(adapter,KEY_L,true);adapter.resume()
	check(adapter.quarantined and neutral(adapter.command(Vector2.RIGHT)),"Press during suspension does not carry into resume")
	key(adapter,KEY_L,false);key(adapter,KEY_L,true)
	check(adapter.command(Vector2.RIGHT).strike,"Suspended press needs release and a new press")
	key(adapter,KEY_L,false);adapter.suspend();key(adapter,KEY_UP,true);key(adapter,KEY_UP,false)
	check(adapter.suspended and neutral(adapter.command(Vector2.RIGHT)),"Release while suspended does not silently resume")
	adapter.resume()
	check(not adapter.quarantined and neutral(adapter.command(Vector2.RIGHT)),"Explicit resume after release is neutral")
	var irrelevant:=InputEventKey.new();irrelevant.keycode=KEY_F12;irrelevant.pressed=true;adapter.receive(irrelevant)
	check(adapter.held.is_empty(),"Unknown keys cannot grow held state")
	check(adapter.command(Vector2.DOWN).aim==Vector2.DOWN,"Aim passes through without owning simulation")
	print("INTENT_CHECKS ",JSON.stringify({"passed":passed,"failed":failed}))
	quit(0 if failed==0 else 1)
