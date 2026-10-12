extends SceneTree
## Actual combat clocks and renderer; fixtures declare positions/stages, not human input.
var arena
var failures: Array[String] = []
var checks := 0
var captures := ""

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool,message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

func frame() -> void:
	arena.queue_redraw()
	await RenderingServer.frame_post_draw if DisplayServer.get_name()!="headless" else process_frame

func capture(name: String) -> void:
	if captures.is_empty() or DisplayServer.get_name()=="headless": return
	await frame()
	root.get_texture().get_image().save_png(captures.path_join(name+".png"))

func setup() -> void:
	arena.reset_encounter()
	arena.mode="fight"
	arena._sync_ui()
	arena.player.position=Vector2(560,400)
	arena.boss.position=Vector2(645,400)
	arena.boss_stage="windup"
	arena.stage_duration=100
	arena.pattern="sweep"
	arena.aim=Vector2.LEFT
	arena.attack_origin=arena.boss.position
	arena.attack_hit=false

func run() -> void:
	captures=OS.get_environment("VEIL_CAPTURE_DIR")
	arena=load("res://arena.tscn").instantiate()
	root.add_child(arena)
	await process_frame
	arena.set_physics_process(false)
	setup()
	for actor in ["runner","warden"]:
		var spec: Dictionary=arena.Motion.CATALOG.data.actors[actor]
		check(spec.frames.size()==16,"Sixteen actual atlas regions load for "+actor)
		var image: Image=(arena.Motion.RUNNER if actor=="runner" else arena.Motion.WARDEN).get_image()
		if image.is_compressed(): image.decompress()
		var isolated := true
		var fits_walls := true
		for item in spec.frames:
			var rect:=Rect2i(item.region[0],item.region[1],item.region[2],item.region[3])
			isolated = isolated and item.pivot[1]<=rect.size.y and image.get_region(rect).get_used_rect().has_area()
			for x in range(rect.position.x,rect.end.x):
				isolated = isolated and image.get_pixel(x,rect.position.y).a<0.125 and image.get_pixel(x,rect.end.y-1).a<0.125
			for y in range(rect.position.y,rect.end.y):
				isolated = isolated and image.get_pixel(rect.position.x,y).a<0.125 and image.get_pixel(rect.end.x-1,y).a<0.125
			var bounds: Array=item.opaque_bounds
			var pivot:=Vector2(item.pivot[0],item.pivot[1])
			for side in [-1,1]:
				for point in [Vector2(94,189),Vector2(1186,651)] if actor=="runner" else [Vector2(108,203),Vector2(1172,637)]:
					for corner in [Vector2(bounds[0],bounds[1]),Vector2(bounds[2],bounds[3])]:
						var pixel: Vector2=point+Vector2(0,22)+(corner-pivot)*float(spec.scale)*Vector2(side,1)
						fits_walls = fits_walls and Rect2(30,140,1220,550).has_point(pixel)
		check(isolated,"Actual imported "+actor+" frames have content, valid foot pivots and transparent cell borders")
		check(fits_walls,"All opaque "+actor+" poses fit inside the presentation buffer at collision-wall limits in both orientations")
	# Start costs resources; contact and the matching art/cue happen later once.
	arena.step_fight(.01,Vector2.ZERO,true,false,false)
	check(arena.boss_hp==160 and arena.stamina<100 and arena.Motion.runner_frame(arena)==4,"Strike starts in anticipation with paid resolve and no damage")
	check(not arena.sound.events.has("strike"),"Blade sound waits for contact")
	await capture("strike-preparation")
	arena.step_fight(.09,Vector2.ZERO,false,false,false)
	check(arena.boss_hp==160,"Before 100ms there is no blade damage")
	arena.step_fight(.01,Vector2.ZERO,false,false,false)
	check(arena.boss_hp==156 and arena.Motion.runner_frame(arena)==5 and arena.sound.events.has("strike"),"100ms contact applies guarded damage, contact pose and sound together")
	await capture("strike-contact")
	arena.step_fight(.08,Vector2.ZERO,false,false,false)
	check(arena.boss_hp==156 and arena.Motion.runner_frame(arena)==6,"Follow-through never repeats damage")
	arena.step_fight(.07,Vector2.ZERO,false,false,false)
	check(arena.Motion.runner_frame(arena)==7,"Blade reaches its visible recovery pose")
	await capture("strike-recovery")
	arena.step_fight(.07,Vector2.ZERO,false,false,false)
	check(arena.player_action.is_empty(),"The complete blade action returns control after 320ms")
	# Locking orientation creates a real whiff, not a radial hit behind the attacker.
	setup()
	arena.step_fight(.01,Vector2.ZERO,true,false,false)
	arena.boss.position=Vector2(480,400)
	arena.step_fight(.11,Vector2.LEFT,false,false,false)
	check(arena.boss_hp==160 and not arena.runner_flipped,"Movement cannot redirect the committed blade or flip its pose")
	check(arena.feedback.begins_with("Missed"),"A positional whiff is explained in the real HUD")
	# Dodge cancels an unlanded action without refunding or a later ghost hit.
	setup()
	arena.step_fight(.01,Vector2.ZERO,true,false,false)
	arena.step_fight(.02,Vector2.LEFT,false,false,true)
	check(arena.player_action.is_empty() and arena.Motion.runner_frame(arena)>=8 and arena.Motion.runner_frame(arena)<=11,"Dodge cancels anticipation into its own pose sequence")
	for i in 20: arena.step_fight(.01,Vector2.ZERO,false,false,false)
	check(arena.boss_hp==160 and arena.stats.strikes==1 and arena.stats.dodges==1 and arena.stamina<75,"Cancelled blade never lands or refunds spent resolve")
	setup()
	arena.step_fight(.01,Vector2.ZERO,false,true,false)
	check(arena.seals.is_empty() and arena.Motion.runner_frame(arena)==12,"Seal begins in gather pose without an instant projectile")
	arena.step_fight(.075,Vector2.ZERO,false,false,false)
	check(arena.seals.size()==1 and arena.Motion.runner_frame(arena)==13 and arena.sound.events.has("seal"),"75ms cast contact releases one real projectile with pose and cue")
	arena.step_fight(.01,Vector2.ZERO,false,false,false)
	check(arena.seals.size()==1,"Held cast does not release a second projectile")
	setup()
	arena.step_fight(.01,Vector2.ZERO,false,true,false)
	arena._take_hit()
	for i in 15: arena.step_fight(.01,Vector2.ZERO,false,false,false)
	check(arena.seals.is_empty() and arena.hp==5,"Actual damage interrupts an uncast seal")
	setup()
	arena.step_fight(.01,Vector2.ZERO,true,true,false)
	check(arena.stats.strikes==1 and arena.stats.seals==0,"Simultaneous blade/cast chooses one coherent action")
	arena.pause_game()
	var frozen=[arena.action_time,arena.Motion.runner_frame(arena),arena.boss_hp,arena.runner_walk_clock,arena.stage_time]
	for i in 10:
		arena.step_fight(.1,Vector2.RIGHT,true,true,true)
		await process_frame
	check(frozen==[arena.action_time,arena.Motion.runner_frame(arena),arena.boss_hp,arena.runner_walk_clock,arena.stage_time],"Pause freezes gameplay and both pose clocks; no ghost contact")
	arena._begin_or_resume()
	arena.step_fight(.1,Vector2.ZERO,false,false,false)
	check(arena.boss_hp==156,"Explicit resume continues the unfinished contact once")
	arena.reset_encounter()
	check(arena.player_action.is_empty() and arena.action_time==0 and arena.runner_walk_clock==0 and arena.warden_walk_clock==0,"Restart clears all action and locomotion clocks")
	# Native sprite coordinates share one physical foot anchor despite uneven generated placement.
	setup()
	for pattern in ["sweep","charge","wave"]:
		arena.pattern=pattern
		var base:=4 if pattern=="sweep" else 8 if pattern=="charge" else 12
		arena.boss_stage="windup"
		check(arena.Motion.warden_frame(arena)==base,"Warden anticipation is tied to "+pattern)
		await capture(pattern+"-anticipation")
		arena.boss_stage="active"
		arena.stage_time=.04
		arena.stage_duration=.4
		check(arena.Motion.warden_frame(arena)==base+1,"Warden contact/drive is tied to "+pattern)
		await capture(pattern+"-active")
		arena.boss_stage="recover"
		arena.stage_time=.25
		check(arena.Motion.warden_frame(arena)==base+3,"Warden spent pose is tied to "+pattern)
		await capture(pattern+"-recovery")
	setup()
	arena.player.position=Vector2(300,260)
	var walking_frames: Array[int]=[]
	for i in 25:
		await physics_frame
		arena.step_fight(.016,Vector2.RIGHT,false,false,false)
		var pose: int=arena.Motion.runner_frame(arena)
		if not walking_frames.has(pose): walking_frames.append(pose)
	check(walking_frames.size()==4,"Actual native movement visits every walk keyframe")
	await capture("walk")
	arena.toggle_tactics()
	await capture("tactics-motion")
	check(arena.help_panel.get_rect().end.x<1280 and arena.help_panel.get_rect().end.y<690,"Updated native tactics fit inside the play viewport")
	arena._begin_or_resume()
	# A short rendered sequence is an engine demonstration with declared fixtures.
	if OS.get_environment("VEIL_MOTION_DEMO")=="1": await demonstrate()
	print("MOTION_CHECKS ",JSON.stringify({"checks":checks,"failures":failures}))
	arena.sound.stop()
	OS.delay_msec(150)
	quit(0 if failures.is_empty() else 1)

func demonstrate() -> void:
	setup()
	arena.player.position=Vector2(400,400)
	arena.boss.position=Vector2(800,400)
	arena.attack_origin=arena.boss.position
	for i in 180:
		var move:=Vector2.RIGHT if i<30 else Vector2.ZERO
		if i==45 or i==110:
			arena.player.position=Vector2(710,400)
			arena.boss_stage="recover"
			arena.stage_time=0
			arena.stage_duration=2
		if i==75:
			arena.player.position=Vector2(500,400)
			arena.boss_stage="windup"
			arena.pattern="wave"
			arena.stage_time=0
			arena.stage_duration=1.4
			arena.attack_origin=arena.boss.position
			arena.aim=arena.boss.position.direction_to(arena.player.position)
			arena.attack_hit=false
		if i==130:
			arena.player.position=Vector2(600,400)
			arena.boss_stage="windup"
			arena.pattern="charge"
			arena.stage_time=0
			arena.stage_duration=.6
			arena.attack_origin=arena.boss.position
			arena.aim=arena.boss.position.direction_to(arena.player.position)
			arena.attack_hit=false
		arena.step_fight(1.0/30,move,i==45 or i==110,i==35,i==112)
		await frame()
