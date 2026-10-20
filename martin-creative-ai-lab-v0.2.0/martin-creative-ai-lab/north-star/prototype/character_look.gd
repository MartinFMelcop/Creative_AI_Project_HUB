extends RefCounted
## Session expression is separate from combat, fitted gear and earned marks.
const Combat=preload("res://combat.gd")
const DEFAULTS:={"skin":0,"hair":0,"dye":0}
const FIELDS:=["skin","hair","dye"]
const NAMES:={"skin":["Original","Sand","Bronze","Umber"],"hair":["Uncovered","Swept","Tied"],"dye":["Original","Indigo","Rust","Moss"]}
const SKIN:=[Color("e9eddf"),Color("d6ad83"),Color("a9704f"),Color("6d4438")]
const CLOTH:=[Color.TRANSPARENT,Color("514c76"),Color("79503e"),Color("446450")]
const OUTFITS:=["standard","riveted","trail"]
const POSES:=["Rest","Walk","Response","Step","Blade"]
var applied:Dictionary=DEFAULTS.duplicate()
var draft:Dictionary=DEFAULTS.duplicate()
var active:=false
var paused:=false
var row:=0
var role:="Guardian"
var style:="Steady"
var outfit:=0
var pose_index:=0
var sample_time:=0.0
var preview=Combat.new()

func enter(kind: String, technique: String, fitting: String) -> void:
	active=true;paused=false;row=0;draft=applied.duplicate()
	role=kind;style=technique;outfit=maxi(0,OUTFITS.find(fitting));pose_index=0;reset_preview()

func cycle(direction: int) -> void:
	if not active:return
	var field:String=FIELDS[row]
	draft[field]=posmod(draft[field]+direction,NAMES[field].size())

func confirm() -> void:
	if not active:return
	applied=draft.duplicate();active=false

func cancel() -> void:
	draft=applied.duplicate();active=false

func reset_preview() -> void:
	preview=Combat.new();preview.reset(role,style);preview.fit_outfit(OUTFITS[outfit]);sample_time=0
	if pose_index==2 and role=="Duelist":preview.phase="bolt";preview.target=preview.courier
	if pose_index==4:preview.player=Combat.ENEMY-Vector2(100,0)

func step(delta: float) -> void:
	if not active or paused:return
	var duration:float=0.5 if pose_index in [2,3,4] else 1.5
	if sample_time>=duration:
		reset_preview();return
	var command:Dictionary={}
	match pose_index:
		1:command.move=Vector2.RIGHT
		2:
			if role=="Guardian":command.skill=true
			else:command.skill_pressed=sample_time==0
		3:command={"move":Vector2.RIGHT,"dodge":sample_time==0}
		4:command.strike=sample_time==0
	preview.step(delta,command);sample_time+=clampf(delta,0,0.05)

func palette(editing: bool=false) -> Dictionary:
	var choice:Dictionary=draft if editing else applied
	return {"skin":SKIN[choice.skin],"hair":choice.hair,"cloth":CLOTH[choice.dye]}

func snapshot() -> Dictionary:
	return {"applied":applied.duplicate(),"draft":draft.duplicate(),"active":active,"paused":paused,
		"row":row,"preview_role":role,"preview_outfit":OUTFITS[outfit],"preview_pose":POSES[pose_index]}

class Portrait extends Node2D:
	var controller
	var actor
	func _draw() -> void:
		if controller and actor:actor.draw_player(self,controller.preview,controller.palette(true))
