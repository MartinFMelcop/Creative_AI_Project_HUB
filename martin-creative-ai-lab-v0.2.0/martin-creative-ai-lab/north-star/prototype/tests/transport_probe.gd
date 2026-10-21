extends "remote_journey.gd"
## Observe the unchanged fixed native-input policy, never alter its decisions or model.
var frame_visits:Dictionary={}
var transitions:Array=[]
var transition_count:=0
var observations:=0
var quarantine_observations:=0
var last_observed_tick:=-1
var max_tick_gap:=0
var last_status:=""
var prior_suspended:=false
var resumes:=0
var started_at:=0
func _initialize() -> void:
	started_at=Time.get_ticks_msec();super._initialize()
func _process(delta:float) -> bool:
	if view!=null:
		var status:String=view.remote.status
		frame_visits[status]=frame_visits.get(status,0)+1
		if status!=last_status:
			transition_count+=1
			if transitions.size()<48:transitions.append({"elapsed_ms":Time.get_ticks_msec()-started_at,"status":status})
			last_status=status
		if prior_suspended and not view.controls.suspended:resumes+=1
		prior_suspended=view.controls.suspended
		if not view.remote.latest.is_empty():
			var tick:int=int(view.remote.latest.tick)
			if tick!=last_observed_tick:
				observations+=1
				if last_observed_tick>=0:max_tick_gap=maxi(max_tick_gap,tick-last_observed_tick)
				last_observed_tick=tick
				if view.remote.latest.quarantined:quarantine_observations+=1
	return super._process(delta)
func finish(success:bool,reason:String) -> void:
	super.finish(success,reason)
	var file=FileAccess.open(output,FileAccess.READ)
	if file==null:return
	var result:Dictionary=JSON.parse_string(file.get_as_text());file.close()
	result.transport_observation={"frame_visits":frame_visits,"transitions":transitions,"transition_count":transition_count,"transitions_truncated":transition_count>transitions.size(),
		"distinct_observations":observations,"quarantine_observations":quarantine_observations,
		"max_observed_tick_gap":max_tick_gap,"explicit_policy_resumes":resumes,
		"limits":"Frame visits and scripted resumes are not participants, RTT or human experience. State tick gaps include observer scheduling."}
	file=FileAccess.open(output,FileAccess.WRITE)
	if file:file.store_string(JSON.stringify(result,"  ")+"\n");file.close()
