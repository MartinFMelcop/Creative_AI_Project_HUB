import { DIALOGUE } from './dialogue.js';

export class Scene {
  constructor() {
    this.state = { stress:20, trust:45, respect:55, mood:'NEUTRAL', cooldown:0,
      turn:0, herbs_sorted:false, apology_due:false, apology_trust_ceiling:null,
      flags:[], events:[], ending:null };
    this.history = [];
  }
  snapshot() { return structuredClone(this.state); }
  available_actions() {
    const s = this.state;
    if (s.ending) return [];
    if (s.mood === 'OUTBURST') return ['wait','leave'];
    return Object.keys(DIALOGUE.actions).filter(a =>
      !(a === 'herbs' && s.herbs_sorted) && !(a === 'apologize' && !s.apology_due));
  }
  eligible(v) {
    const s = this.state, calm = s.mood !== 'OUTBURST';
    switch (v.source_id) {
      case 'DV_NPC0007_NEGOTIATION_001': return calm && s.trust >= 40;
      case 'DV_NPC0007_NEGOTIATION_002': return calm && s.trust < 40;
      case 'DV_NPC0007_MANIP_CONF_WARN_001': return calm && s.stress < 80;
      case 'DV_NPC0007_MANIP_CONF_OUTBURST_001': return calm && s.stress >= 80;
      case 'DV_NPC0007_GOODBYE_001': return calm && !s.flags.includes('FLAG_NPC0007_AVOID_PLAYER_TEMP');
      case 'DV_NPC0007_GOODBYE_002': return !calm || s.flags.includes('FLAG_NPC0007_AVOID_PLAYER_TEMP');
      case 'SCENE_BARGAIN_UNRESOLVED_LIE': return calm && s.apology_due;
      default: return calm;
    }
  }
  response(v) {
    const s = this.state;
    if (!v) {
      if (s.cooldown) return [
        'The Keeper grips the edge of the bench. You step back from the door.',
        'They turn away and loosen their grip, one finger at a time.',
        'They set a fallen seed pod beside the basket. You keep quiet.',
        'They pull the stool upright and sit. Their hands are still.',
        'The Keeper turns the stool to face you.'
      ][5 - s.cooldown];
      return s.herbs_sorted
        ? 'Lamplight catches the loose rune on the cleared bench. The Keeper checks a seed pod beside it.'
        : 'The Keeper picks another seed pod from the wet leaves. The light outside is fading.';
    }
    if (s.turn + 1 >= 12) {
      if (v.action === 'ask') return s.herbs_sorted
        ? "The basket is sorted. The light's gone; take the rune home tonight."
        : "My tools are still under these leaves. It's too dark to start the repair now.";
      if (v.action === 'bargain') {
        if (s.apology_due) return "You haven't withdrawn the false order. I won't agree to the repair. The light's gone.";
        if (s.trust >= 40 && !s.herbs_sorted) return "The tools are still under that basket. We can't finish before dark now.";
      }
      if (v.action === 'lie' && v.mood !== 'OUTBURST') return "There was no council order. Take the rune home. I won't start a repair in the dark.";
      if (v.action === 'apologize') return s.events.includes('EVT_NPC_OUTBURST')
        ? "I heard you. I'm still not agreeing to the repair. Take the rune home; we're out of daylight."
        : "You've withdrawn the order. It's too dark to start the repair tonight.";
    }
    if (v.action === 'ask' && s.herbs_sorted) return 'The basket is sorted. I can see that. Tell me who needs this crossing tonight.';
    if (v.action === 'bargain' && !s.apology_due) {
      if (s.trust >= 40 && s.herbs_sorted) return s.flags.includes('FLAG_PLAYER_LIED')
        ? "You withdrew the order. The village still needs the crossing. I'll fit the rune; hold the lamp."
        : "A crossing for the village, before dark. I'll fit the rune; hold the lamp steady.";
      if (s.trust < 40 && s.events.includes('EVT_NPC_OUTBURST')) return "You kept repeating that false order. I heard your apology, but I won't risk this repair on your word tonight.";
    }
    if (v.action === 'lie' && v.mood !== 'OUTBURST') {
      if (s.apology_due) return 'You already tried that order. Stop repeating it. The council gave you no authority here.';
      if (s.flags.includes('FLAG_PLAYER_LIED')) return "You withdrew that order. Now you're using it again?";
    }
    if (v.action === 'apologize' && s.events.includes('EVT_NPC_OUTBURST')) return "I heard you. I'll leave the door open. That doesn't mean I've agreed to the repair.";
    return v.text;
  }
  act(action) {
    if (!this.available_actions().includes(action)) throw new Error('That choice is unavailable. Use a listed choice.');
    const s = this.state, before = this.snapshot();
    const candidates = DIALOGUE.variants.filter(v => v.action === action && this.eligible(v));
    const variant = [...candidates].sort((a,b) => b.priority-a.priority || b.source_id.localeCompare(a.source_id))[0];
    let text = this.response(variant);
    if (variant) {
      for (const key of ['stress','trust','respect']) s[key] = Math.max(0,Math.min(100,s[key]+variant[key]));
      s.mood = variant.mood;
      for (const key of ['flags','events']) s[key] = [...new Set([...s[key],...variant[key]])].sort();
    }
    if (action === 'herbs') s.herbs_sorted = true;
    else if (action === 'lie') {
      if (!before.apology_due) s.apology_trust_ceiling = before.trust;
      s.apology_due = true;
    } else if (action === 'apologize') {
      s.trust = Math.min(s.trust,before.apology_trust_ceiling);
      s.apology_due = false; s.apology_trust_ceiling = null;
    }
    if (s.mood === 'OUTBURST' && before.mood !== 'OUTBURST') s.cooldown = 5;
    else if (before.cooldown > 0) {
      s.cooldown = before.cooldown - 1;
      if (!s.cooldown && s.mood === 'OUTBURST') {
        s.mood = 'WARY'; text += '\nTheir breathing steadies.';
        if (s.turn + 1 < 12) text += ' They are ready to listen again.';
      }
    }
    s.turn++;
    if (action === 'bargain' && s.herbs_sorted && before.trust >= 40 && !s.apology_due) s.ending = 'COOPERATED';
    else if (action === 'leave') s.ending = s.mood === 'AVOIDANT' ? 'DISMISSED' : 'LEFT';
    else if (s.turn >= 12) s.ending = 'DUSK';
    const result = {action,variant_id:variant?.source_id || 'SCENE_WAIT',
      variant_origin:variant && !variant.source_id.startsWith('SCENE_') ? 'legacy-adaptation' : 'scene',
      eligible_variants:candidates.map(v=>v.source_id).sort(),speaker:action === 'wait' ? 'Narrator' : 'Keeper',
      text,before,after:this.snapshot()};
    this.history.push(result); return result;
  }
}
