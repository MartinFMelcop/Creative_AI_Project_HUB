import {Adventure,serialize as nightSave,restore as restoreNight} from './engine.js';
import {Morning} from './morning.js';
import {Afternoon} from './afternoon.js';
import {Handover} from './handover.js';
import {REVIEW_ACTIONS} from './deferred-request.js';
export class Campaign extends Adventure {
  constructor(){super();this.morning=null;this.handover=null;this.afternoon=null;}
  choices(){return this.afternoon?this.afternoon.choices():this.handover?this.handover.choices():this.morning?this.morning.choices():super.choices();}
  act(action) {
    if(action==='afternoon') {
      if(this.afternoon||!this.handover?.state.ending)throw new Error('The afternoon follows a signed receipt.');
      const before=this.handover.snapshot();this.afternoon=new Afternoon(this.handover);
      const result={action,cost:0,text:this.afternoon.opening(),before,after:this.afternoon.snapshot()};
      this.history.push(result);return result;
    }
    if(this.afternoon){const result=this.afternoon.act(action);this.history.push(result);return result;}
    if(action==='handover') {
      if(this.handover||!this.morning?.state.ending)throw new Error('The handover follows a completed morning.');
      const before=this.morning.snapshot();this.handover=new Handover(before);
      const result={action,cost:0,text:this.handover.opening(),before,after:this.handover.snapshot()};
      this.history.push(result);return result;
    }
    if(this.handover){const result=this.handover.act(action);this.history.push(result);return result;}
    if(action==='morning') {
      if(this.morning||!this.state.ending)throw new Error('The morning follows a completed night crossing.');
      const before=this.snapshot();this.morning=new Morning(before);
      const result={action,cost:0,text:this.morning.opening(),before,after:this.morning.snapshot()};
      this.history.push(result);return result;
    }
    if(!this.morning)return super.act(action);
    const result=this.morning.act(action);this.history.push(result);return result;
  }
}
export function serialize(game) {
  const data=nightSave(game);
  return game.afternoon?.review?{...data,schema:5,engine_version:'0.7.0'}:game.afternoon?{...data,schema:4,engine_version:'0.6.0'}:game.handover?{...data,schema:3,engine_version:'0.5.0'}:game.morning?{...data,schema:2,engine_version:'0.4.0'}:data;
}
export function restore(data) {
  if(data?.schema===1) {
    const old=restoreNight(data),game=new Campaign();
    game.state=old.state;game.workshop=old.workshop;game.history=old.history;return game;
  }
  if(!data||data.format!=='waystone-save'||!((data.schema===2&&data.engine_version==='0.4.0')||(data.schema===3&&data.engine_version==='0.5.0')||(data.schema===4&&data.engine_version==='0.6.0')||(data.schema===5&&data.engine_version==='0.7.0'))
    ||!Array.isArray(data.actions)||data.actions.length>1024||data.actions.some(a=>typeof a!=='string'||a.length>32))throw new Error('Incompatible campaign save.');
  const game=new Campaign();for(const action of data.actions) {
    if(data.schema===2&&action==='handover')throw new Error('The handover requires a schema-3 save.');
    if(data.schema<5&&REVIEW_ACTIONS.has(action))throw new Error('Revisiting the request requires a schema-5 save.');
    if(data.schema<4&&action==='afternoon')throw new Error('The afternoon requires a schema-4 save.');
    game.act(action);
  }
  if(data.schema===3&&!game.handover)throw new Error('A schema-3 save must include the handover.');
  if(data.schema===4&&!game.afternoon)throw new Error('A schema-4 save must include the afternoon.');
  if(data.schema===5&&!game.afternoon?.review)throw new Error('A schema-5 save must include the deferred request.');
  return game;
}
