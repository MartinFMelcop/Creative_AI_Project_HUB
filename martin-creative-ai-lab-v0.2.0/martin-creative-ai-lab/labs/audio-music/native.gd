extends SceneTree
var sound
var capture: AudioEffectCapture
var checks=[]
var failures=[]
var measurements={}
func _initialize():call_deferred('run')
func check(value: bool,name: String):
 if not value:push_error(name);failures.append(name)
 checks.append(name)
func peak_for(seconds: float) -> float:
 capture.clear_buffer()
 await create_timer(seconds).timeout
 var frames=capture.get_buffer(capture.get_frames_available())
 var peak=0.0
 for frame in frames:peak=maxf(peak,maxf(absf(frame.x),absf(frame.y)))
 measurements['captured_frames']=measurements.get('captured_frames',0)+frames.size()
 return peak
func skew() -> float:
 AudioServer.lock()
 var delta=absf(sound.tracks[0].get_playback_position()-sound.tracks[1].get_playback_position())
 AudioServer.unlock()
 return delta
func run():
 sound=Node.new();sound.set_script(load('res://sound.gd'));root.add_child(sound)
 capture=AudioEffectCapture.new();capture.buffer_length=2.0;AudioServer.add_bus_effect(0,capture)
 await create_timer(.2).timeout
 measurements.aligned=skew();check(measurements.aligned<.015,'actual_same_block_stems_within_15ms')
 measurements.audible=await peak_for(.2);check(measurements.audible>.001,'actual_post_limiter_audio_nonzero')
 sound.set_phase(true)
 await create_timer(1.2).timeout
 check(sound.mix>.99,'actual_phase_crossfade_reaches_endpoint')
 measurements.after_crossfade=skew();check(measurements.after_crossfade<.015,'crossfade_keeps_transport_phase')
 sound.set_suspended(true);var before= sound.events.size();sound.cue('hurt');check(sound.events.size()==before,'suspended_source_drops_cue')
 await create_timer(.1).timeout
 measurements.suspended=await peak_for(.15);check(measurements.suspended<.0001,'actual_suspended_output_silent')
 sound.set_suspended(false);sound.toggle_mute();await create_timer(.1).timeout
 sound.cue('hurt');check(sound.events[-1]=='hurt','muted_source_audits_without_playback')
 measurements.muted=await peak_for(.15);check(measurements.muted<.0001,'actual_muted_output_below_minus80db')
 sound.toggle_mute()
 for i in 100:sound.cue('strike')
 check(sound.voices.size()==8 and sound.events.size()==64,'bounded_eight_voices_and_64_events')
 sound.limiter.pre_gain_db=12
 measurements.stress=await peak_for(.2);check(measurements.stress>.001 and measurements.stress<.86,'actual_gain_stress_limiter_below_minus1_3db')
 sound.limiter.pre_gain_db=0
 AudioServer.lock();sound.tracks[1].seek(sound.tracks[0].get_playback_position()+.1);AudioServer.unlock()
 await create_timer(.15).timeout
 measurements.shifted=skew();check(measurements.shifted>.05,'atomic_100ms_shift_detected_above50ms')
 sound.reset();await create_timer(.15).timeout
 measurements.restored=skew();check(measurements.restored<.015,'actual_reset_restores_transport')
 check(sound.events.is_empty() and sound.mix==0 and sound.target_mix==0,'actual_reset_clears_phase_and_event_history')
 sound.stop();await create_timer(.1).timeout
 measurements.stopped=await peak_for(.15);check(measurements.stopped<.0001,'actual_stop_output_silent')
 if not failures.is_empty():quit(1);return
 print('AUDIO_SOURCE_NATIVE '+JSON.stringify({'controls':checks,'measurements':measurements,'driver':AudioServer.get_driver_name()}))
 quit()
