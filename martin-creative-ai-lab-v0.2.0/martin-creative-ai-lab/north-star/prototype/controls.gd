extends RefCounted
## Local keyboard preferences, separate from cosmetic achievement data and Combat rules.
const ACTIONS := ["move_left","move_right","move_up","move_down","aim_left","aim_right","aim_up","aim_down","strike","skill","step","interact"]
const LABELS := ["Move left","Move right","Move up","Move down","Aim left","Aim right","Aim up","Aim down","Blade counter","Guard / feint","Directional step","Recover / hand over"]
const DEFAULTS := {"move_left":KEY_A,"move_right":KEY_D,"move_up":KEY_W,"move_down":KEY_S,"aim_left":KEY_LEFT,"aim_right":KEY_RIGHT,"aim_up":KEY_UP,"aim_down":KEY_DOWN,"strike":KEY_J,"skill":KEY_K,"step":KEY_SPACE,"interact":KEY_E}
const NAV := [KEY_LEFT,KEY_RIGHT,KEY_UP,KEY_DOWN]
const RESERVED := [KEY_ESCAPE,KEY_ENTER,KEY_KP_ENTER,KEY_1,KEY_2,KEY_R,KEY_T,KEY_C,KEY_F1,KEY_F5,KEY_F12]
var keys: Dictionary=DEFAULTS.duplicate()
var path := ""
var dirty := false
var blocked := false
var status := "Defaults. Apply to save on this device."
var suppressed := {}
var pattern=RegEx.new()
var replacements := {}

func _init() -> void:
	pattern.compile("\\b(RIGHT arrow|WASD|ARROWS|SPACE|K|J|E|W|D)\\b")
	refresh_labels()

func load_profile(profile_path: String) -> bool:
	path=profile_path
	keys=DEFAULTS.duplicate();dirty=false;blocked=false;suppressed.clear()
	status="Defaults. Apply to save on this device.";refresh_labels()
	var data=read_profile(path)
	if data.kind=="missing":return true
	if data.kind!="valid":block_save();return false
	keys=data.mapping;refresh_labels();status="Saved on this device."
	return true

static func allowed(code: int) -> bool:
	if code in RESERVED:return false
	return (code>=KEY_A and code<=KEY_Z) or (code>=KEY_0 and code<=KEY_9) or code in NAV or code in [KEY_SPACE,KEY_TAB,KEY_BACKSPACE,KEY_DELETE,KEY_INSERT,KEY_HOME,KEY_END,KEY_PAGEUP,KEY_PAGEDOWN,KEY_F2,KEY_F3,KEY_F4,KEY_F6,KEY_F7,KEY_F8,KEY_F9,KEY_F10,KEY_F11,KEY_COMMA,KEY_PERIOD,KEY_SLASH,KEY_SEMICOLON,KEY_APOSTROPHE,KEY_BRACKETLEFT,KEY_BRACKETRIGHT,KEY_MINUS,KEY_EQUAL,KEY_BACKSLASH,KEY_QUOTELEFT]

static func valid(mapping: Variant) -> bool:
	if not mapping is Dictionary or mapping.size()!=ACTIONS.size():return false
	var seen: Array[int]=[]
	for action in ACTIONS:
		if not mapping.has(action):return false
		var code=mapping[action]
		if typeof(code) not in [TYPE_INT,TYPE_FLOAT] or code!=int(code) or not allowed(int(code)) or int(code) in seen:return false
		seen.append(int(code))
	return true

static func assign(mapping: Dictionary, action: String, code: int) -> String:
	if action not in ACTIONS:return "Unknown action."
	if not allowed(code):return "Reserved or unsupported key. Choose an unmodified keyboard key."
	for other in ACTIONS:
		if other!=action and mapping[other]==code:return "Already used by "+LABELS[ACTIONS.find(other)]+". Change that action first."
	mapping[action]=code
	return ""

static func event_code(event: InputEventKey) -> int:
	# Navigation has logical identity in Godot/X11; letters retain physical positions.
	return event.keycode if event.keycode in NAV else event.physical_keycode

func matches(event: InputEventKey, action: String) -> bool:
	return not suppressed.has(int(keys[action])) and event_code(event)==int(keys[action])

func down(action: String) -> bool:
	var code: int=int(keys[action])
	var held: bool=Input.is_key_pressed(code) if code in NAV else Input.is_physical_key_pressed(code)
	if suppressed.has(code):
		if not held:suppressed.erase(code)
		return false
	return held

func release(event: InputEventKey) -> void:
	suppressed.erase(event_code(event))

func quarantine() -> void:
	for action in ACTIONS:
		var code: int=int(keys[action])
		if (Input.is_key_pressed(code) if code in NAV else Input.is_physical_key_pressed(code)):suppressed[code]=true

func vector(prefix: String) -> Vector2:
	return Vector2(float(down(prefix+"_right"))-float(down(prefix+"_left")),float(down(prefix+"_down"))-float(down(prefix+"_up")))

func name_for(action: String, mapping: Dictionary={}) -> String:
	return OS.get_keycode_string(int((keys if mapping.is_empty() else mapping)[action]))

func refresh_labels() -> void:
	replacements={"WASD":name_for("move_left")+"/"+name_for("move_right")+"/"+name_for("move_up")+"/"+name_for("move_down"),"ARROWS":name_for("aim_left")+"/"+name_for("aim_right")+"/"+name_for("aim_up")+"/"+name_for("aim_down"),"RIGHT arrow":name_for("aim_right"),"K":name_for("skill"),"J":name_for("strike"),"E":name_for("interact"),"SPACE":name_for("step"),"W":name_for("move_up"),"D":name_for("move_right")}

func describe(value: String) -> String:
	var result := "";var previous := 0
	for match in pattern.search_all(value):
		result+=value.substr(previous,match.get_start()-previous)+replacements[match.get_string()]
		previous=match.get_end()
	return result+value.substr(previous)

func apply(mapping: Dictionary) -> bool:
	if not valid(mapping):status="Invalid controls; active bindings unchanged.";return false
	keys=mapping.duplicate();refresh_labels();dirty=true
	return save()

func read_profile(candidate: String) -> Dictionary:
	if candidate.is_empty():return {"kind":"invalid"}
	if not FileAccess.file_exists(candidate):return {"kind":"invalid" if DirAccess.dir_exists_absolute(candidate) else "missing"}
	var file=FileAccess.open(candidate,FileAccess.READ)
	if file==null:return {"kind":"invalid"}
	var length=file.get_length()
	if length>4096:file.close();return {"kind":"invalid"}
	var bytes=file.get_buffer(length);file.close()
	var content=bytes.get_string_from_utf8()
	if bytes.size()!=length or content.to_utf8_buffer()!=bytes:return {"kind":"invalid"}
	var parser=JSON.new()
	if parser.parse(content)!=OK:return {"kind":"invalid"}
	var data=parser.data
	if not data is Dictionary or data.size()!=2 or not data.has("schema_version") or not data.has("keys"):return {"kind":"invalid"}
	if typeof(data.schema_version) not in [TYPE_INT,TYPE_FLOAT] or data.schema_version!=1 or not valid(data["keys"]):return {"kind":"invalid"}
	# Godot JSON numbers are floats; restore integer key identity before exact readback.
	var normalized := {}
	for action in ACTIONS:normalized[action]=int(data["keys"][action])
	return {"kind":"valid","mapping":normalized}

func save() -> bool:
	# Invalid/unknown primary bytes are never silently replaced, even after initial load.
	if read_profile(path).kind not in ["valid","missing"]:block_save();return false
	blocked=false
	var temp=path+"."+str(OS.get_process_id())+"."+str(Time.get_ticks_usec())+".tmp"
	var file=FileAccess.open(temp,FileAccess.WRITE)
	if file==null:return write_failed()
	file.store_string(JSON.stringify({"schema_version":1,"keys":keys})+"\n");file.flush()
	var error=file.get_error();file.close()
	var checked=read_profile(temp)
	if error!=OK or checked.kind!="valid" or checked.mapping!=keys:
		DirAccess.remove_absolute(temp);return write_failed()
	if replace_file(temp,path)!=OK:DirAccess.remove_absolute(temp);return write_failed()
	dirty=false;status="Applied and saved on this device."
	return true

func replace_file(from: String,to: String) -> Error:
	return DirAccess.rename_absolute(from,to)

func block_save() -> void:
	blocked=true;status="Profile unavailable. Restore or remove it, then apply again. Session controls remain usable."

func write_failed() -> bool:
	dirty=true;status="Applied this session; not saved. Repair the path, then S retries here."
	return false

func snapshot() -> Dictionary:
	return {"keys":keys.duplicate(),"dirty":dirty,"blocked":blocked,"status":status}
