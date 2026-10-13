import {Adventure,serialize as nightSave,restore as restoreNight} from './engine.js';
import {Morning} from './morning.js';
import {Handover} from './handover.js';
export class Campaign extends Adventure {
  constructor(){super();this.morning=null;this.handover=null;}
  choices(){return this.handover?this.handover.choices():this.morning?this.morning.choices():super.choices();}
  act(action) {
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
  return game.handover?{...data,schema:3,engine_version:'0.5.0'}:game.morning?{...data,schema:2,engine_version:'0.4.0'}:data;
}
export function restore(data) {
  if(data?.schema===1) {
    const old=restoreNight(data),game=new Campaign();
    game.state=old.state;game.workshop=old.workshop;game.history=old.history;return game;
  }
  if(!data||data.format!=='waystone-save'||!((data.schema===2&&data.engine_version==='0.4.0')||(data.schema===3&&data.engine_version==='0.5.0'))
    ||!Array.isArray(data.actions)||data.actions.length>1024||data.actions.some(a=>typeof a!=='string'||a.length>32))throw new Error('Incompatible campaign save.');
  const game=new Campaign();for(const action of data.actions) {
    if(data.schema===2&&action==='handover')throw new Error('The handover requires a schema-3 save.');
    game.act(action);
  }
  if(data.schema===3&&!game.handover)throw new Error('A schema-3 save must include the handover.');
  return game;
}
