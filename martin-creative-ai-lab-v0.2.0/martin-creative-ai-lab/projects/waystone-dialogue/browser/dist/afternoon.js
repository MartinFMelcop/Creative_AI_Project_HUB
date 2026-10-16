import {DeferredRequest,REVIEW_ACTIONS} from './deferred-request.js';
// New adaptation fiction: execute inherited work without rewriting earlier records.
export class Afternoon {
  constructor(handover) {
    if(!handover.state.ending)throw new Error('Sign the noon receipt first.');
    this.receipt=structuredClone(handover.snapshot());
    const m=handover.morning.morning;
    this.route=handover.afternoon();
    this.state={time:4,elapsed:0,people:m.people,iven:this.route.iven,medicine:m.medicine,
      timely:m.timely,recall:m.medicine==='supplied'&&m.timely,grain:m.grain,seed:m.seed,
      reserve_used:m.reserve_used,ending:null};
    this.history=[];this.review=null;
  }
  snapshot(){return {afternoon:structuredClone(this.state),receipt:structuredClone(this.receipt),route:structuredClone(this.route),...(this.review?{review:this.review.snapshot()}: {})};}
  reviewActive(){return !!this.review&&!this.review.state.ending&&this.review.state.stage!=='paused';}
  commitment(){return this.review?.state.ending?this.review.state:this.receipt.handover;}
  canRevisit(){return !this.state.ending&&this.state.time>0&&this.receipt.handover.decision==='keep-crossing'&&this.receipt.handover.term==='review-later'&&(!this.review||this.review.state.stage==='paused');}
  opening(){return "The wagon turns upstream. Mara brings four clean counters from the clinic; the morning counters stay folded inside the old list. 'These are ours until dusk.'\n\n"+
    (this.route.road?"A kitchen cart is already on the causeway.":this.route.ferry?(this.route.iven?"Iven pushes the ferry clear for the next load.":(this.commitment().decision==='send-guide'?"Mara tests an oar against the patched bow. Iven has gone upstream; a loaded return will take two shifts.":"Mara tests an oar against the patched bow. Iven is still across the channel; a loaded return will take two shifts.")):"The ferry has gone or is still unusable. Mara tightens her pack straps. The ridge trail carries one crate in two shifts.")+"\n\nThe attendant checks the clinic entry; Mara counts the crates already received. Senn's seed has its own line. There are four shifts of light, and no extra crew on the wagon coming back.";}
  choices(){
    const s=this.state,r=this.route,out=[];
    const add=(name,label,cost,detail)=>{if(cost<=s.time)out.push({name,label,cost,detail});};
    if(s.ending)return out;
    if(this.reviewActive())return this.review.choices();
    if(s.people<4||(!s.iven&&this.commitment().decision!=='send-guide'))
      add('recover-crew',this.commitment().decision==='send-guide'?'Bring the remaining mill villagers home.':'Bring the remaining mill party and Iven home.',r.road?1:r.ferry?r.shifts_per_trip:3,'Recover people, not a new transport route. An upstream volunteer is never recalled by this action.');
    if(s.medicine==='missing') {
      const dry=['waiting','aboard'].includes(this.receipt.morning.night.expedition.medicine);
      add(dry?'retrieve-chest':'depot',dry?'Retrieve the dry chest.':'Collect the depot replacement.',dry?(r.road||r.ferry?1:2):2,dry?'Dry supplies still need one shift at the clinic.':'Uses the depot reserve; one more shift to supply the clinic.');
    }
    if(s.medicine==='ready')add('supply-clinic','Unpack dry supplies at the clinic.',1,'Opens afternoon care. The missed morning deadline stays on record; recall callers separately.');
    if(s.medicine==='supplied'&&!s.recall)add('recall','Visit the morning callers and reopen the queue.',1,'Mara and the attendant find the people who left. This does not change when medicine arrived.');
    if(s.grain<4)add('grain',`Carry ${Math.min(4-s.grain,r.grain_per_trip)} grain crate(s).`,r.shifts_per_trip,`${r.route}: ${r.grain_per_trip} crate(s) per ${r.shifts_per_trip} shift(s). ${4-s.grain} still at the mill.`);
    if(s.seed==='loft')add('seed','Bring the sowing seed to dry ground.',r.shifts_per_trip,'A separate load from kitchen grain; planting needs two more shifts and all four villagers.');
    if(s.seed==='saved'&&s.people===4)add('plant','Drain the strip and plant with Senn.',2,'Seed goes into drained ground. No harvest is claimed.');
    if(this.canRevisit())add('revisit-request','Revisit the deferred upstream request.',0,'Count the work already done; hear the crew again before lending a boat or guide. Nothing leaves just by opening the request.');
    add('close','Stop work and wait for dusk.',s.time,'Keep unfinished work and upstream obligations visible. No automatic ferry or guide return.');
    return out;
  }
  act(action){
    const choice=this.choices().find(c=>c.name===action);if(!choice)throw new Error('That afternoon task is unavailable.');
    const before=this.snapshot(),s=this.state;let text='';
    switch(action){
      case 'revisit-request':{const resumed=this.review?.state.stage==='paused';this.review=new DeferredRequest(this.receipt,{afternoon:this.state,route:this.route});text=this.review.opening(resumed);break;}
      case 'recover-crew':s.people=4;
        if(this.commitment().decision!=='send-guide'){s.iven=true;this.route.iven=true;if(this.route.ferry&&!this.route.road)this.route.shifts_per_trip=1;}
        text="Senn checks the last names at the clinic gate. "+(this.commitment().decision==='send-guide'?"Iven is still upstream by his own agreement. ":"Iven comes up from the channel with the mooring hook. ")+"Mara leaves the noon receipt folded; these arrivals belong on the afternoon sheet.";break;
      case 'retrieve-chest':s.medicine='ready';text="You lift the sealed chest from the mill. The attendant clears the clinic steps. She asks you to stay and unpack it before calling anyone back.";break;
      case 'depot':s.medicine='ready';s.reserve_used=true;text="The depot keeper counts out the replacement packets and writes the empty reserve box's number on your sheet. You carry the load to the clinic steps.";break;
      case 'supply-clinic':s.medicine='supplied';text="The attendant opens the packets and sets out clean dressings. The morning chairs are empty. Mara takes the callers' addresses from beneath the list.";break;
      case 'recall':s.recall=true;text="Mara walks the lane while the attendant opens the clinic. One caller is mending a shutter; another has gone to the kitchen. You leave the new opening time at both doors and bring the waiting list back. No one erases the morning arrival time.";break;
      case 'grain':{const amount=Math.min(4-s.grain,this.route.grain_per_trip);s.grain+=amount;text=`The kitchen receiver counts ${amount} crate(s) off your ${this.route.route==='causeway'?'cart':'load'}. `+(s.grain===4?"She shuts the fourth bin and takes the mill key off the food list.":`She leaves room beside the bins. ${4-s.grain} crate(s) still need carrying.`);break;}
      case 'seed':s.seed='saved';text="You carry Senn's tied sack to the dry boards by the clinic. She checks the knot, then looks toward the planting strip. 'We need time to open that drain.'";break;
      case 'plant':s.seed='sown';text="Senn sends Lio to the drain mouth. The rest of you turn the wet soil away from the strip before she opens the sack. The last row goes in while water runs down the new cut. She leaves the spade by the gate for the next rain.";break;
      default:
        if(REVIEW_ACTIONS.has(action)){text=this.review.act(action).text;if(this.review.state.ending){this.route=this.review.routeAfter();s.iven=this.route.iven;}}
        break;
      case 'close':text="You put the tools away and wait for dusk. Mara draws a line beneath the afternoon entries. The remaining jobs go below it, with the loft key. She keeps Dain's receipt separate.";break;
    }
    s.elapsed+=choice.cost;s.time-=choice.cost;
    if(action==='close'||!s.time)s.ending='DUSK_LIST';
    const result={action,cost:choice.cost,text,before,after:this.snapshot()};this.history.push(result);return result;
  }
  upstreamEnding(){
    if(!this.review?.state.ending)return null;
    const c=this.review.state;
    if(c.decision==='keep-crossing')return 'The afternoon crew refused the deferred request after reviewing its remaining work. No boat or guide left; no upstream rescue is reported.';
    const asset=c.decision==='lend-ferry'?'ferry':'guide Iven';
    return `The ${asset} left after ${c.openedAt} afternoon shift(s), with ${c.remaining} shift(s) of local light remaining. The noon receipt still records a deferred request. `+
      (c.term==='return-at-dusk'?'The new agreed return is due now. No return or upstream rescue has been observed.':'The new loan has no agreed return time. No return or upstream rescue has been observed.');
  }
  epilogue(){
    const s=this.state,upstream=this.upstreamEnding();if(!s.ending)throw new Error('Afternoon work is still open.');
    return [s.people===4?'All four mill villagers are home.':`${4-s.people} mill villagers still need a crossing crew. Their shelter locations stay on the list.`,
      s.medicine==='supplied'?(s.timely?'The clinic was supplied on time this morning.':s.recall?'Afternoon care is open and the morning callers have been contacted. The original late supply time remains.':'The clinic has supplies, but the morning callers still need contacting.'):s.medicine==='ready'?'Dry supplies wait on the steps; the clinic still needs help unpacking.':'Dry clinic supplies are still missing.',
      `${s.grain} of 4 grain crates received; ${4-s.grain} remain at the mill.`,
      s.seed==='sown'?'Seed is planted; the drain needs checking after rain. Harvest is unknown.':s.seed==='saved'?'Seed is dry in the yard; draining and planting remain.':'The sowing seed is still in the loft.',
      s.reserve_used?'The depot reserve needs replacing.':'The depot reserve was not used.',
      upstream || (this.receipt.handover.decision==='keep-crossing'?(this.receipt.handover.term==='decline'?'The upstream request was refused. No rescue there is reported.':'The upstream request awaits a later review. No loan was promised.'):
      this.receipt.handover.term==='return-at-dusk'?'The agreed return is due now. No return has been observed; Mara leaves the receipt open.':'The upstream loan has no agreed return time. No return or upstream rescue has been observed.')].join('\n\n');
  }
}
