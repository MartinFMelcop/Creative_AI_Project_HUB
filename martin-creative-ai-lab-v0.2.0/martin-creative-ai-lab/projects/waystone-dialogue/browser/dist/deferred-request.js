// New adaptation fiction. A later consultation cannot rewrite the noon receipt.
export const REVIEW_ACTIONS=new Set([
  'revisit-request','review-list','review-mara','review-iven','review-settle',
  'review-keep','review-boat','review-guide','review-back','review-dusk','review-open','review-pause'
]);

const frozenCopy=value=>{
  const freeze=item=>{if(item&&typeof item==='object'){for(const child of Object.values(item))freeze(child);Object.freeze(item);}return item;};
  return freeze(structuredClone(value));
};
const shifts=n=>`${n} shift${n===1?'':'s'}`;

export class DeferredRequest {
  constructor(receipt,{afternoon,route}={}) {
    const noon=receipt?.handover;
    if(!noon?.ending||noon.decision!=='keep-crossing'||noon.term!=='review-later')
      throw new Error('Only the deferred noon request can be reconsidered.');
    if(!afternoon||afternoon.ending||!Number.isFinite(afternoon.time)||afternoon.time<=0||!route)
      throw new Error('The request needs an open afternoon with light remaining.');
    this.receipt=frozenCopy(receipt);
    this.afternoon=frozenCopy(afternoon);
    this.route=frozenCopy(route);
    this.state={stage:'table',heard:[],decision:null,term:null,ending:null,
      openedAt:afternoon.elapsed,remaining:afternoon.time};
  }
  snapshot(){return structuredClone(this.state);}
  routeAfter(decision=this.state.decision) {
    const route=structuredClone(this.route);
    if(decision==='lend-ferry')route.ferry=false;
    if(decision==='send-guide')route.iven=false;
    route.route=route.road?'causeway':route.ferry?'ferry':'ridge trail';
    route.grain_per_trip=route.road?4:route.ferry?2:1;
    route.shifts_per_trip=route.road?1:route.ferry&&route.iven?1:2;
    return route;
  }
  facts() {
    const a=this.afternoon,r=this.route;
    return [
      `${shifts(a.time)} of light remain; ${shifts(a.elapsed)} have been used this afternoon.`,
      `${a.people} of 4 mill villagers are home. Iven is ${a.iven&&r.iven?'here with the local crew':'still across the channel'}.`,
      a.medicine==='supplied'?(a.timely?'The clinic was supplied on time this morning.':a.recall?'The clinic is supplied; the morning callers have been contacted. The morning deadline was missed.':'The clinic is supplied; the morning callers still need contacting. The morning deadline was missed.'):
        a.medicine==='ready'?'Dry medicine is on the steps; unpacking at the clinic remains.':'The clinic still needs dry medicine.',
      `${a.grain} of 4 grain crates are received; ${4-a.grain} remain at the mill.`,
      a.seed==='sown'?'The seed is planted; the drain needs checking after rain. No harvest is known.':
        a.seed==='saved'?'The seed is dry in the yard. Draining and planting remain.':'The sowing seed is still in the loft.',
      a.reserve_used?'The depot reserve was used and needs replacing.':'The depot reserve is untouched.',
      `The local ${r.route} carries ${r.grain_per_trip} grain crate(s) per ${shifts(r.shifts_per_trip)}.`
    ];
  }
  opening(resumed=false) {
    const a=this.afternoon;
    return [
      resumed?"The boat hand gets down from the wall by the high road. Mara unfolds the unsigned slip beside the noon copy. No boat or guide has left during the pause.":"A woman comes down the high road carrying the empty red towline over one shoulder. She was one of the boat hands on Dain's noon wagon. The wagon has already gone on.",
      "She stops at Mara's table. 'The receipt said to ask this crew again. Dain sent me back for an answer.' She sets down a clean slip beside the noon copy. 'If you lend the boat, I'll sign for it here.'",
      "Mara puts the afternoon sheet between the two receipts. "+(a.elapsed?"'We've worked since then. Start with this one.'":"'This is the afternoon crew's list. Start with this one.'")+" The boat hand waits while Mara wipes a patch of the table dry.",
      `${shifts(a.time)} of light remain. ${4-a.grain} grain crate(s) still need carrying. `+
        (a.seed==='sown'?"Senn's strip has been planted.":a.seed==='saved'?"Senn's sack is dry; the strip still needs draining and planting.":"Senn's sack is still in the loft."),
      a.iven&&this.route.iven?"Iven rests his mooring hook against the table. He has made no offer to this returning boat hand.":"Iven has not reached the yard. His name stays off the offer."
    ].join('\n\n');
  }
  choices() {
    const s=this.state,a=this.afternoon,r=this.route,out=[];
    const add=(name,label,detail)=>out.push({name,label,detail,cost:0});
    if(s.stage==='ended'||s.stage==='paused')return out;
    if(s.stage==='table') {
      if(!s.heard.includes('list'))add('review-list','Read the current afternoon list.','Count completed work, unfinished loads and the light left now.');
      if(!s.heard.includes('mara'))add('review-mara','Ask Mara about the work left here.','Hear what a loan would change after the afternoon work already done.');
      if(a.iven&&r.iven&&!s.heard.includes('iven'))add('review-iven','Ask Iven whether he will guide them now.','His noon answer does not supply consent for this later request.');
      add('review-settle','Consider an answer to the renewed request.','No boat or guide has been agreed.');
    } else if(s.stage==='decision') {
      add('review-keep','Keep the remaining transport and crew here.','Sign a final refusal; no later loan is promised.');
      if(r.ferry)add('review-boat','Offer the ferry, subject to written terms.',r.road?'Keep the causeway and local crew; lend the backup ferry.':'Local loads would use the ridge trail: 1 crate per 2 shifts.');
      if(a.iven&&r.iven&&s.heard.includes('iven'))add('review-guide','Accept Iven’s fresh offer, subject to terms.',r.road?'Keep the causeway and any ferry; Iven would leave the local crew.':r.ferry?'Keep the ferry; each loaded local trip without Iven would take 2 shifts.':'Keep the ridge trail; sending Iven would open no faster local route.');
      add('review-back','Return to the conversation.','Nothing has been handed over.');
    } else if(s.stage==='terms') {
      add('review-dusk','Require a return by dusk.',`Only ${shifts(a.time)} of local light remain. This sets an obligation; it cannot confirm a return.`);
      add('review-open','Agree to a loan without a return time.','The boat or guide remains unavailable locally until an actual return.');
      add('review-back','Reconsider before signing.','Withdraw the tentative offer; no resources have left.');
    }
    add('review-pause','Set the request aside and continue local work.','No loan is agreed. A later consultation must use the work list and people present then.');
    return out;
  }
  act(action) {
    if(!this.choices().some(c=>c.name===action))throw new Error('That renewed-request choice is unavailable.');
    const s=this.state,a=this.afternoon,r=this.route;let text='';
    switch(action) {
      case 'review-list':
        s.heard.push('list');
        text="Mara reads the afternoon entries in their order. The boat hand puts a finger under the noon date, then moves it to the new sheet. She makes no mark on the older receipt.\n\n"+this.facts().join('\n\n');break;
      case 'review-mara':
        s.heard.push('mara');
        text="Mara takes the kitchen tally from the nail above the table. "+
          (a.grain<4?`'There are ${4-a.grain} crates to carry. Tell me which route the next load will use before you untie anything.'`:"'The fourth crate is in. The kitchen won't need that crossing for grain again today.'")+
          '\n\n'+(a.medicine==='missing'?"She lays the clinic key beside it. 'We still need the dry packets.'":a.medicine==='ready'?"She lays the clinic key beside it. 'The packets are outside. Someone still has to open them with the attendant.'":!a.timely&&!a.recall?"She draws the callers' addresses out of her apron. 'I haven't been round to these doors yet.'":"The attendant returns the clinic key. Mara hangs it above the current sheet.")+
          '\n\n'+(r.road?"She points to the causeway entry. 'The cart can keep going. If the boat goes, strike it off the spare-route line.'":r.ferry?`She taps the ferry entry. 'With it here, a load takes ${shifts(r.shifts_per_trip)}. Without it, it's two shifts on the ridge for one crate.'`:"She puts the ridge pack under the bench. 'That is still what we carry with. A guide leaving won't give us another boat.'");break;
      case 'review-iven':
        s.heard.push('iven');
        text="The boat hand asks Iven to mark the shallow bar on her slip. He turns it over and draws the bend, then stops his pencil at the bar. 'From the road you won't see this edge.'\n\nHe looks at the afternoon tally. 'I can go now. You'll have to choose what this crew leaves unfinished. Put my limit in writing before I leave.' He sets the pencil across the slip. 'Ask me to sign it too.'";
        if(!r.road&&r.ferry)text+="\n\nMara pulls the spare oar out from under the bench. Iven checks its blade and leaves it beside her chair.";
        break;
      case 'review-settle':
        s.stage='decision';
        text="The boat hand straightens the clean slip. 'A boat, a guide, or a refusal. I'll carry the answer.' "+
          (s.heard.includes('iven')?"Iven waits beside the hook; his offer still needs terms.":a.iven&&r.iven?"Iven keeps his hands off the slip. He has not offered to go in this consultation.":"Mara leaves Iven's name on the missing-person line.");break;
      case 'review-back':
        s.stage='table';s.decision=null;s.term=null;
        text="You slide the unsigned slip back beside the work list. The boat hand leaves the towline on her shoulder. Mara opens the afternoon sheet again.";break;
      case 'review-keep':
        s.decision='keep-crossing';s.term='decline';s.ending='keep-crossing';s.stage='ended';
        text="You write that the remaining transport and crew will stay here. The boat hand signs beneath 'no boat or guide supplied' and tears off the local copy. She takes the high road with the refusal; Mara pins the new copy beside the noon request.";break;
      case 'review-boat':
        s.decision='lend-ferry';s.stage='terms';
        text="You point to the ferry entry. The boat hand writes its description on the clean slip. Mara keeps the mooring line on its hook. 'Write the terms before I release it.'\n\n"+
          (r.road?"The causeway remains on the local sheet. The ferry would be unavailable as a second route.":"Mara writes the proposed carrying rate in the margin: one crate on the ridge trail, two shifts per load.")+" The slip is unsigned; the ferry is still here.";break;
      case 'review-guide':
        s.decision='send-guide';s.stage='terms';
        text="You ask Iven to take the guide's line on the slip. He draws his hook toward his boot but leaves it on the ground. 'Put the return time beside my name, or say there isn't one.'\n\n"+
          (r.road?"Mara keeps the causeway on the local sheet.":r.ferry?"Mara writes two shifts beside each loaded ferry trip without him.":"The ridge trail remains the local route.")+" Iven waits for the terms before signing.";break;
      case 'review-dusk':
      case 'review-open': {
        s.term=action==='review-dusk'?'return-at-dusk':'open-return';s.stage='ended';s.ending=s.decision;
        text=action==='review-dusk'?"The boat hand writes 'return due at dusk' and signs her name. ":"The boat hand writes 'no return time agreed' and signs her name. ";
        text+=s.decision==='lend-ferry'?"Mara checks the copy, then takes the line off its hook. The boat hand carries it down to the ferry and pushes away from the landing. Iven stays with the local crew.":"Iven reads the terms and signs beneath his own name. He lifts the hook and follows the boat hand onto the high road. The local transport stays here.";
        if(s.decision==='lend-ferry'&&!(a.iven&&r.iven))text=text.replace(' Iven stays with the local crew.',' No local guide goes with her.');
        text+='\n\n'+(action==='review-dusk'?"Mara leaves the return box empty. A signature has set the deadline; no return has been observed.":"Mara leaves the loan open on the afternoon sheet. No return or result from upstream has been reported.");
        break;
      }
      case 'review-pause':
        s.stage='paused';s.decision=null;s.term=null;s.ending=null;
        text="Mara folds the unsigned slip around the noon copy. The ferry line and the local crew stay here. The boat hand sits on the wall by the high road while you return to work. Any later answer will need the list as it stands then.";break;
    }
    return {text};
  }
}
