extends RefCounted
## Native InputMap adapter. Pad actions are separate so disconnect cannot release keyboard input.

const DEADZONE := 0.22
const KEYS := {"left":[KEY_A,KEY_LEFT],"right":[KEY_D,KEY_RIGHT],"up":[KEY_W,KEY_UP],"down":[KEY_S,KEY_DOWN],"strike":[KEY_J],"seal":[KEY_K],"dash":[KEY_SPACE],"parry":[KEY_L],"begin":[KEY_ENTER],"pause":[KEY_ESCAPE],"help":[KEY_F1],"mute":[KEY_M],"practice":[KEY_P]}
const BUTTONS := {"left":JOY_BUTTON_DPAD_LEFT,"right":JOY_BUTTON_DPAD_RIGHT,"up":JOY_BUTTON_DPAD_UP,"down":JOY_BUTTON_DPAD_DOWN,"strike":JOY_BUTTON_X,"seal":JOY_BUTTON_Y,"dash":JOY_BUTTON_B,"parry":JOY_BUTTON_LEFT_SHOULDER,"begin":JOY_BUTTON_A,"pause":JOY_BUTTON_START,"help":JOY_BUTTON_BACK,"mute":JOY_BUTTON_RIGHT_SHOULDER,"practice":JOY_BUTTON_RIGHT_STICK}
var using_gamepad := false
var last_device := -1

func setup() -> void:
	for action in KEYS:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
			for key in KEYS[action]:
				var event := InputEventKey.new()
				event.physical_keycode = key
				InputMap.action_add_event(action,event)
		var pad: String = "pad_"+action
		if not InputMap.has_action(pad):
			InputMap.add_action(pad,DEADZONE)
			var button := InputEventJoypadButton.new()
			button.button_index = BUTTONS[action]
			button.device = -1
			InputMap.action_add_event(pad,button)
			if action in ["left","right","up","down"]:
				var axis := InputEventJoypadMotion.new()
				axis.axis = JOY_AXIS_LEFT_X if action in ["left","right"] else JOY_AXIS_LEFT_Y
				axis.axis_value = -1.0 if action in ["left","up"] else 1.0
				axis.device = -1
				InputMap.action_add_event(pad,axis)

func observe(event: InputEvent) -> bool:
	var was_pad := using_gamepad
	if (event is InputEventJoypadButton and event.pressed) or (event is InputEventJoypadMotion and event.axis in [JOY_AXIS_LEFT_X,JOY_AXIS_LEFT_Y] and absf(event.axis_value)>DEADZONE):
		using_gamepad = true
		last_device = event.device
	elif (event is InputEventKey and event.pressed and not event.echo) or (event is InputEventMouseButton and event.pressed):
		using_gamepad = false
	return was_pad != using_gamepad

func pressed(action: String) -> bool:
	return Input.is_action_just_pressed(action) or Input.is_action_just_pressed("pad_"+action)

func movement() -> Vector2:
	return (Input.get_vector("left","right","up","down")+Input.get_vector("pad_left","pad_right","pad_up","pad_down",DEADZONE)).limit_length()

func clear_pad() -> void:
	for action in BUTTONS: Input.action_release("pad_"+action)

func disconnected(device: int) -> bool:
	if device != last_device: return false
	var was_active := using_gamepad
	clear_pad()
	last_device = -1
	using_gamepad = false
	return was_active
