extends RefCounted
## Fixed keyboard/mouse controls for the separate authority experiment only.
## This does not consume the playable scene's remaps or gamepad preferences.
const KEYS := [KEY_W,KEY_A,KEY_S,KEY_D,KEY_UP,KEY_LEFT,KEY_DOWN,KEY_RIGHT,KEY_K,KEY_J,KEY_SPACE,KEY_L]
const EDGES := ["feint","step","strike"]
const BUTTONS := {"guard":[KEY_K,-MOUSE_BUTTON_RIGHT],"feint":[KEY_J],"step":[KEY_SPACE],"strike":[KEY_L,-MOUSE_BUTTON_LEFT]}
# Two pending presses retain a quick repress without building an unbounded future queue.
const MAX_PENDING := 2
var held:Dictionary={}
var pending:Dictionary={"feint":0,"step":0,"strike":0}
var previous:Dictionary={"feint":false,"step":false,"strike":false}
var suspended:=false
var quarantined:=false

func active(action:String) -> bool:
	return BUTTONS[action].any(func(code):return held.has(code))

func receive(event:InputEvent) -> void:
	var code:int=0
	var pressed:=false
	if event is InputEventKey:
		if event.echo:return
		code=event.physical_keycode if event.physical_keycode in KEYS else event.keycode
		if not code in KEYS:return
		pressed=event.pressed
	elif event is InputEventMouseButton:
		if event.button_index not in [MOUSE_BUTTON_LEFT,MOUSE_BUTTON_RIGHT]:return
		code=-event.button_index;pressed=event.pressed
	else:return
	if pressed==held.has(code):return
	var was:Dictionary={}
	for action in EDGES:was[action]=active(action)
	if pressed:held[code]=true
	else:held.erase(code)
	if quarantined and not suspended and held.is_empty():quarantined=false
	if suspended or quarantined:return
	for action in EDGES:
		if not was[action] and active(action):pending[action]=mini(MAX_PENDING,int(pending[action])+1)

func clear_edges() -> void:
	for action in EDGES:pending[action]=0;previous[action]=false

func suspend() -> void:
	suspended=true;quarantined=true;clear_edges()

func resume() -> void:
	suspended=false;quarantined=not held.is_empty();clear_edges()

func command(aim:Vector2) -> Dictionary:
	var result:Dictionary={"move":Vector2.ZERO,"aim":Vector2.ZERO,"guard":false,"feint":false,"step":false,"strike":false}
	if suspended or quarantined:return result
	var horizontal:int=int(held.has(KEY_D) or held.has(KEY_RIGHT))-int(held.has(KEY_A) or held.has(KEY_LEFT))
	var vertical:int=int(held.has(KEY_S) or held.has(KEY_DOWN))-int(held.has(KEY_W) or held.has(KEY_UP))
	result.move=Vector2(horizontal,vertical).limit_length();result.aim=aim;result.guard=active("guard")
	for action in EDGES:
		# The wire consumer detects rising edges; every pulse needs a false packet.
		if previous[action]:previous[action]=false
		elif pending[action]>0:
			pending[action]-=1;previous[action]=true;result[action]=true
	return result
