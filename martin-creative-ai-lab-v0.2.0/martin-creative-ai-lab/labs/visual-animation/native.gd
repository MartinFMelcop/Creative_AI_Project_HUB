extends SceneTree
# Execute staged source selection and draw arguments; the recorder replaces only renderer I/O.
class CanvasRecorder extends RefCounted:
 var transforms: Array=[]
 var regions: Array=[]
 func draw_set_transform(position: Vector2, rotation: float=0, scale: Vector2=Vector2.ONE) -> void:
  transforms.append([position,rotation,scale])
 func draw_texture_rect_region(_texture, rect: Rect2, region: Rect2, _tint: Color) -> void:
  regions.append([rect,region])
func _initialize() -> void:
 var source=load('res://motion.gd')
 var arena={'dash_time':0.0,'player_action':'none','action_emitted':false,'action_time':0.0,'damage_flash':0.0,'runner_walk_clock':0.0,'runner_moving':false,'boss_stage':'approach','stage_time':0.0,'stage_duration':1.0,'pattern':'sweep','warden_walk_clock':0.0,'warden_moving':false,'PARRY_END':0.3}
 var checks=[]
 for item in [['idle',{},3],['walk',{'runner_moving':true,'runner_walk_clock':0.2},2],['dash',{'dash_time':0.15},9],['strike_windup',{'dash_time':0.0,'player_action':'strike'},4],['strike_active',{'action_emitted':true,'action_time':0.1},5],['strike_recovery',{'action_time':0.2},6],['strike_end',{'action_time':0.3},7],['seal',{'player_action':'seal','action_emitted':false},12],['seal_active',{'action_emitted':true,'action_time':0.1},13],['seal_recovery',{'action_time':0.2},14],['seal_end',{'action_time':0.3},15]]:
  arena.merge(item[1],true)
  if source.runner_frame(arena)!=item[2]:push_error('Runner selection '+item[0]);quit(1);return
  checks.append(item[0])
 for stage in ['windup','active','recovery']:
  for pattern in ['sweep','charge','wave']:
   arena.boss_stage=stage;arena.pattern=pattern;arena.stage_time=0.1
   var base=4 if pattern=='sweep' else 8 if pattern=='charge' else 12
   var expected=base if stage=='windup' else base+1 if stage=='active' else 10 if pattern=='charge' else base+3
   if source.warden_frame(arena)!=expected:push_error('Warden selection');quit(1);return
   checks.append('warden_'+stage+'_'+pattern)
 var catalog=JSON.parse_string(FileAccess.get_file_as_string('res://media/motion-catalog.json'))
 for actor in ['runner','warden']:
  for frame in 16:
   for flipped in [false,true]:
    var recorder=CanvasRecorder.new()
    source.draw_actor(recorder,Vector2(320,218),actor,frame,flipped,Color.WHITE)
    var transform=recorder.transforms[0];var rect=recorder.regions[0][0];var spec=catalog.actors[actor];var pivot=Vector2(spec.frames[frame].pivot[0],spec.frames[frame].pivot[1])
    var anchor=transform[0]+(rect.position+pivot*spec.scale)*transform[2]
    if not anchor.is_equal_approx(Vector2(320,240)):
     print('WRONG_ANCHOR_DETECTED');quit(1);return
    var region=catalog.actors[actor].frames[frame].region
    if recorder.regions[0][1]!=Rect2(region[0],region[1],region[2],region[3]):push_error('Wrong crop');quit(1);return
 checks.append('64_actual_draw_argument_registration_and_crop_controls')
 print('VISUAL_NATIVE '+JSON.stringify({'controls':checks,'selection_controls':20,'draw_controls':64,'renderer':'staged native draw-argument recorder; no raster/pixel claim'}))
 quit()
