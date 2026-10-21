extends RefCounted
## One mapped device owns pad state. No global InputMap or keyboard profile mutation.
const DEADZONE:=0.22
const BUTTONS:=[JOY_BUTTON_A,JOY_BUTTON_B,JOY_BUTTON_X,JOY_BUTTON_Y,JOY_BUTTON_LEFT_SHOULDER,JOY_BUTTON_RIGHT_SHOULDER,JOY_BUTTON_BACK,JOY_BUTTON_START,JOY_BUTTON_LEFT_STICK,JOY_BUTTON_RIGHT_STICK,JOY_BUTTON_DPAD_LEFT,JOY_BUTTON_DPAD_RIGHT,JOY_BUTTON_DPAD_UP,JOY_BUTTON_DPAD_DOWN]
var using_gamepad:=false
var device:=-1
var buttons:Dictionary={}
var suppressed:Dictionary={}
var axes:=[0.0,0.0,0.0,0.0]
var blocked_sticks:=[false,false]
var pattern:=RegEx.new()
func _init() -> void:pattern.compile("\\b(F1|F2|F3|F4|F5|ENTER|ESC|DELETE|SPACE|TAB|WASD|ARROWS|K|J|E|R|T|C)\\b")
func clear() -> void:
	buttons.clear();suppressed.clear();axes=[0.0,0.0,0.0,0.0];blocked_sticks=[false,false]
func keyboard() -> void:
	clear();using_gamepad=false;device=-1
func lose_device(id: int) -> bool:
	if device!=id:return false
	clear();device=-1;return true
func quarantine() -> void:
	for id in buttons:
		if buttons[id]:suppressed[id]=true
	for i in 2:blocked_sticks[i]=Vector2(axes[i*2],axes[i*2+1]).length()>DEADZONE
func receive(event: InputEvent) -> int:
	var intent:=false
	if event is InputEventJoypadButton:
		if event.button_index not in BUTTONS:return -1
		intent=event.pressed
	elif event is InputEventJoypadMotion:
		if event.axis not in [JOY_AXIS_LEFT_X,JOY_AXIS_LEFT_Y,JOY_AXIS_RIGHT_X,JOY_AXIS_RIGHT_Y]:return -1
		intent=absf(event.axis_value)>DEADZONE
	else:return -1
	if event.device!=device:
		if not intent:return -1
		clear();device=event.device
	if intent:using_gamepad=true
	if event is InputEventJoypadMotion:
		axes[event.axis]=clampf(event.axis_value,-1,1)
		for i in 2:
			if Vector2(axes[i*2],axes[i*2+1]).length()<=DEADZONE:blocked_sticks[i]=false
		return -1
	var was:bool=buttons.get(event.button_index,false)
	buttons[event.button_index]=event.pressed
	if not event.pressed:suppressed.erase(event.button_index);return -1
	return event.button_index if not was and not suppressed.has(event.button_index) else -1
func held(id: int) -> bool:return using_gamepad and buttons.get(id,false) and not suppressed.has(id)
func vector(stick: int) -> Vector2:
	if not using_gamepad or blocked_sticks[stick]:return Vector2.ZERO
	var value:=Vector2(axes[stick*2],axes[stick*2+1]).limit_length()
	var length:=value.length()
	return value.normalized()*((length-DEADZONE)/(1.0-DEADZONE)) if length>DEADZONE else Vector2.ZERO
func movement() -> Vector2:
	return (vector(0)+Vector2(float(held(JOY_BUTTON_DPAD_RIGHT))-float(held(JOY_BUTTON_DPAD_LEFT)),float(held(JOY_BUTTON_DPAD_DOWN))-float(held(JOY_BUTTON_DPAD_UP)))).limit_length()
func describe(value: String,context: String) -> String:
	var mapping:={"WASD":"LS","ARROWS":"RS","J":"X","K":"Y","SPACE":"B","E":"A","F1":"BACK","ESC":"START","ENTER":"A","R":"B","T":"X","TAB":"Y","C":"L3","F2":"LB","F3":"RB","F4":"RB","F5":"R3","DELETE":"X"}
	if context=="look":
		mapping.ESC="B";mapping.SPACE="Y";mapping.TAB="L3"
		value=value.replace("1 / 2 preview approach","LB / RB preview approach")
	elif context.begins_with("workshop"):
		mapping.ENTER="A" if context=="workshop_paused" else "Y";mapping.C="X"
	elif context=="talk":
		mapping.ESC="B";mapping.TAB="X"
		value=value.replace("1  Bind","UP  Bind").replace("2  Brace","DOWN  Brace").replace("3  Keep","RIGHT  Keep").replace("Choose 1, 2 or 3","Choose UP, DOWN or RIGHT")
	elif context=="title":value=value.replace("1  GUARDIAN","LEFT  GUARDIAN").replace("2  DUELIST","RIGHT  DUELIST")
	var matches:=pattern.search_all(value)
	for i in range(matches.size()-1,-1,-1):
		var found=matches[i];value=value.substr(0,found.get_start())+mapping[found.get_string()]+value.substr(found.get_end())
	return value
