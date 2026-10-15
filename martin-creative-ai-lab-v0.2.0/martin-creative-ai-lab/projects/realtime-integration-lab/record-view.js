(() => {
  'use strict';
  const byId=id=>document.getElementById(id);
  const record=JSON.parse(byId('record-data').textContent),actions=record.actions || [];
  const status={todo:'To do',doing:'In progress',blocked:'Blocked',done:'Done'};
  const fold=value=>value.normalize('NFKD').replace(/\p{M}/gu,'').toLowerCase();
  const date=value=>`${new Date(value).toLocaleString()} (${value})`;
  const node=(tag,text,className)=>{const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;};
  const button=(text,click)=>{const el=node('button',text);el.type='button';el.onclick=click;return el;};
  const owner=action=>action.owner_name===null?'Unassigned':action.owner_name;
  const pageSize=20;
  const byEntry=new Map(record.entries.map((entry,index)=>[entry.id,{entry,index}]));
  const records=record.entries.map(entry=>({kind:entry.kind,id:entry.id,time:entry.created_at,entry,text:fold(entry.body)}));
  for(const action of actions)for(const event of action.history)records.push({kind:'action',id:event.id,time:event.created_at,event,action,text:fold(`${event.action.title} ${event.action.note}`)});
  // Reading order merges the two streams; revision authority still comes from
  // the recorded revision numbers, not the machine's wall clock.
  records.sort((a,b)=>b.time.localeCompare(a.time)||a.kind.localeCompare(b.kind)||b.id-a.id);
  let workPage=0,resultPage=0,matches=records,openedFrom=null;
  document.querySelector('footer').dataset.sourceHash=document.querySelector('footer code').textContent;
  document.title=`${record.project.name} · Reading copy`;
  byId('project-name').textContent=record.project.name;
  byId('snapshot-time').textContent=`Snapshot exported ${date(record.exported_at)}. This file does not receive later changes.`;
  byId('summary').textContent=`${record.entries.length} discussion/decision entries · ${actions.length} actions · ${records.length-record.entries.length} action revisions`;
  if(!Object.hasOwn(record,'actions'))byId('work-help').textContent='This earlier JSON export contains no action data. It does not establish whether actions existed in the workspace.';
  for(const name of [...new Set(actions.filter(a=>a.owner_name!==null).map(a=>a.owner_name))].sort((a,b)=>a.localeCompare(b))) {
    const option=node('option',name);option.value=JSON.stringify(name);byId('work-owner').append(option);
  }
  function range(count,page) {return count?`${page*pageSize+1}–${Math.min((page+1)*pageSize,count)} of ${count}`:'No matches';}
  function badge(value) {return node('span',status[value],`badge ${value}`);}
  function entryCard(entry) {
    const card=node('li');card.dataset.entry=entry.id;
    card.append(node('p',`${entry.kind==='decision'?'Decision':'Discussion note'} · ${entry.author} · ${date(entry.created_at)}`,'meta'),node('p',entry.body,'body'));
    return card;
  }
  function actionCard(action,heading='h3') {
    const card=node('div',undefined,'card');card.dataset.action=action.id;
    card.append(node(heading,action.title,'body'),badge(action.status),node('p',`Owner label: ${owner(action)} · revision ${action.revision}`,'meta'));
    card.append(node('p',action.note||'No update note recorded.','body'),node('p',`Updated ${date(action.updated_at)}`,'meta'));
    return card;
  }
  function drawWork() {
    const filtered=actions.filter(action=>(byId('work-status').value==='all'||action.status===byId('work-status').value)&&
      (byId('work-owner').value==='all'||JSON.stringify(action.owner_name)===byId('work-owner').value));
    workPage=Math.min(workPage,Math.max(0,Math.ceil(filtered.length/pageSize)-1));
    byId('work-count').textContent=filtered.length?`${range(filtered.length,workPage)} actions at export`:'No actions match these filters.';
    byId('work-list').replaceChildren(...filtered.slice(workPage*pageSize,(workPage+1)*pageSize).map(action=>{
      const item=node('li');item.dataset.action=action.id;
      item.append(node('h3',action.title,'body'),badge(action.status),node('p',`${owner(action)} · revision ${action.revision}`,'meta'),node('p',action.note||'No update note recorded.','body'));
      const open=button('Open decision and revisions',()=>showAction(action,action.history.at(-1),open));item.append(open);return item;
    }));
    byId('work-prev').disabled=workPage===0;byId('work-next').disabled=(workPage+1)*pageSize>=filtered.length;
  }
  function drawResults() {
    byId('result-count').textContent=`${range(matches.length,resultPage)} saved records`;
    byId('results').replaceChildren(...matches.slice(resultPage*pageSize,(resultPage+1)*pageSize).map(match=>{
      let item;
      if(match.entry)item=entryCard(match.entry);
      else {
        const snapshot=match.event.action;item=node('li');item.dataset.event=match.id;
        item.append(node('p',`Action revision ${snapshot.revision} · ${match.event.author} · ${date(match.time)}${snapshot.revision===match.action.revision?' · Current at export':' · Historical'}`,'meta'),node('h3',snapshot.title,'body'),badge(snapshot.status),node('p',snapshot.note||'No update note recorded.','body'));
      }
      const open=button('Open saved context',()=>match.entry?showEntry(match.entry,open):showAction(match.action,match.event,open));item.append(open);return item;
    }));
    byId('result-prev').disabled=resultPage===0;byId('result-next').disabled=(resultPage+1)*pageSize>=matches.length;
  }
  function search() {
    const query=byId('query').value,terms=fold(query.trim()).split(/\s+/u).filter(Boolean);
    if(query.length>160||terms.length>8||(!terms.length&&query.trim())) {
      matches=[];resultPage=0;drawResults();byId('result-count').textContent='Use up to 8 literal words and 160 characters, including at least one searchable character.';return;
    }
    const kind=byId('record-kind').value;
    matches=records.filter(match=>(kind==='all'||match.kind===kind)&&terms.every(term=>match.text.includes(term)));
    resultPage=0;drawResults();
  }
  function detail(title,opener) {
    openedFrom=opener;byId('detail-heading').textContent=title;
    byId('detail-body').replaceChildren();byId('detail').hidden=false;byId('detail-heading').focus();
  }
  function nearby(entry) {
    const {index}=byEntry.get(entry.id),list=node('ol');
    for(const neighbor of record.entries.slice(Math.max(0,index-2),index+3)) {
      const card=entryCard(neighbor);card.dataset.selected=String(neighbor.id===entry.id);list.append(card);
    }
    return list;
  }
  function linkedWork(entry,opener) {
    const section=node('section'),linked=actions.filter(action=>action.source_id===entry.id);
    section.append(node('h3','Linked work at export'));
    if(!linked.length){section.append(node('p','No linked actions in this export.'));return section;}
    const count=node('p',undefined,'meta'),list=node('ol'),nav=node('nav');nav.setAttribute('aria-label','Linked work pages');let page=0;
    const prev=button('Previous linked actions',()=>{page--;draw();}),next=button('Next linked actions',()=>{page++;draw();});
    function draw() {
      count.textContent=range(linked.length,page);
      list.replaceChildren(...linked.slice(page*pageSize,(page+1)*pageSize).map(action=>{
        const item=node('li');item.append(actionCard(action,'h4'),button('Open action history',()=>showAction(action,action.history.at(-1),opener)));return item;
      }));prev.disabled=page===0;next.disabled=(page+1)*pageSize>=linked.length;
    }
    nav.append(prev,next);section.append(count,list,nav);draw();return section;
  }
  function showEntry(entry,opener) {
    detail(entry.kind==='decision'?'Decision and nearby discussion':'Discussion context',opener);
    byId('detail-body').append(node('p','Up to two saved entries before and after the selected entry. They retain their own recorded order.','muted'),nearby(entry));
    if(entry.kind==='decision')byId('detail-body').append(linkedWork(entry,opener));
    byId('detail-heading').scrollIntoView({block:'start'});
  }
  function showAction(action,event,opener) {
    detail(`Action revision ${event.revision} and current work at export`,opener);
    const comparison=node('div',undefined,'comparison'),historical=actionCard(event.action,'h4'),current=actionCard(action,'h4');
    historical.prepend(node('h3',event.revision===action.revision?'Selected revision · current at export':'Selected revision · historical'));
    historical.append(node('p',`Recorded by ${event.author}`,'meta'));
    current.prepend(node('h3','Current at export'));
    comparison.append(historical,current);byId('detail-body').append(comparison);
    if(action.source_id!==null) {
      const source=byEntry.get(action.source_id).entry;
      byId('detail-body').append(node('h3','Source decision and nearby discussion'),nearby(source));
    } else byId('detail-body').append(node('p','This action has no linked decision source.','muted'));
    const history=node('section'),count=node('p',undefined,'meta'),list=node('ol'),nav=node('nav');nav.setAttribute('aria-label','Revision pages');
    history.append(node('h3','Complete revision history'),count,list,nav);byId('detail-body').append(history);
    // Start on the selected revision, including those beyond the live 50-event panel.
    let page=Math.floor((event.revision-1)/pageSize);
    const prev=button('Earlier revisions',()=>{page--;draw();}),next=button('Later revisions',()=>{page++;draw();});nav.append(prev,next);
    function draw() {
      count.textContent=`${range(action.history.length,page)} revisions`;
      list.replaceChildren(...action.history.slice(page*pageSize,(page+1)*pageSize).map(revision=>{
        const item=node('li');item.dataset.revision=revision.revision;item.dataset.selected=String(revision.id===event.id);
        item.append(node('p',`Revision ${revision.revision} · ${revision.author} · ${date(revision.created_at)}`,'meta'),node('h4',revision.action.title,'body'),badge(revision.action.status),node('p',`${owner(revision.action)} · ${revision.action.note||'No update note recorded.'}`,'body'));
        item.append(button('Compare this revision',()=>showAction(action,revision,opener)));return item;
      }));prev.disabled=page===0;next.disabled=(page+1)*pageSize>=action.history.length;
    }
    draw();byId('detail-heading').scrollIntoView({block:'start'});
  }
  // Build only on demand: normal browsing remains bounded to twenty cards.
  // The immutable source, not the active filters or visible pages, is authoritative.
  let reportReady=false;
  function prepareReport() {
    if(reportReady)return;
    const report=document.createDocumentFragment();
    const heading=node('h2','Complete snapshot report');heading.id='report-heading';heading.tabIndex=-1;
    report.append(heading,node('p','All saved entries, current actions and every action revision are included. Reading filters and page selections do not restrict this report.','scope'));
    report.append(node('p',byId('summary').textContent,'meta'));
    const work=node('section');work.append(node('h2','Current work at export'));
    if(!Object.hasOwn(record,'actions'))work.append(node('p','Action data is unavailable in this earlier export. This does not establish whether actions existed.'));
    else if(!actions.length)work.append(node('p','No actions in this export.'));
    for(const action of actions) {
      const card=actionCard(action);card.dataset.reportAction=action.id;
      card.append(node('p',`Action ID: ${action.id} · Created by ${action.creator_name} · ${date(action.created_at)}`,'meta'));
      card.append(node('p',action.source_id===null?'No linked decision.':`Source decision #${action.source_id}: ${action.decision_body}`,'body'));
      work.append(card);
    }
    report.append(work);
    const discussion=node('section'),entries=node('ol');discussion.append(node('h2','Complete discussion and decisions'),node('p','Original saved entry order. Entry numbers identify linked decision sources.','meta'));
    if(!record.entries.length)discussion.append(node('p','No discussion or decisions in this export.'));
    for(const entry of record.entries) {
      const card=entryCard(entry);card.dataset.reportEntry=entry.id;
      card.prepend(node('h3',`Entry #${entry.id}`));entries.append(card);
    }
    discussion.append(entries);report.append(discussion);
    const history=node('section');history.append(node('h2','Complete action revision history'),node('p','Grouped by action; revisions retain their recorded sequence. Historical ownership and status may differ from current work at export.','meta'));
    if(!Object.hasOwn(record,'actions'))history.append(node('p','Action history is unavailable in this earlier export.'));
    else if(!actions.length)history.append(node('p','No action revisions in this export.'));
    for(const action of actions) {
      const group=node('section');group.append(node('h3',action.title),node('p',`Action ID: ${action.id} · ${action.history.length} revisions`,'meta'));
      const revisions=node('ol');
      for(const event of action.history) {
        const item=node('li');item.dataset.reportEvent=event.id;
        item.append(node('h4',`Revision ${event.revision} · ${event.revision===action.revision?'Current at export':'Historical'}`),
          node('p',`Recorded by ${event.author} · ${date(event.created_at)}`,'meta'),
          node('p',event.action.title,'body'),badge(event.action.status),
          node('p',`Owner label: ${owner(event.action)}`,'meta'),node('p',event.action.note||'No update note recorded.','body'));
        revisions.append(item);
      }
      group.append(revisions);history.append(group);
    }
    report.append(history);byId('complete-report').replaceChildren(report);reportReady=true;
  }
  byId('prepare-report').onclick=()=>{
    prepareReport();document.body.classList.add('report-mode');byId('report-controls').hidden=false;byId('reader').hidden=true;
    byId('report-heading').focus();byId('report-heading').scrollIntoView({block:'start'});
  };
  byId('close-report').onclick=()=>{
    document.body.classList.remove('report-mode');byId('report-controls').hidden=true;byId('reader').hidden=false;byId('prepare-report').focus();
  };
  byId('print-report').onclick=()=>window.print();
  // Ctrl/Cmd+P and the browser menu receive the same complete report. Cancelling
  // the dialog leaves the reading state untouched, including its selected pages.
  window.addEventListener('beforeprint',prepareReport);
  byId('back').onclick=()=>{byId('detail').hidden=true;if(openedFrom?.isConnected)openedFrom.focus();else{byId('record-heading').tabIndex=-1;byId('record-heading').focus();}};
  for(const id of ['work-status','work-owner'])byId(id).onchange=()=>{workPage=0;drawWork();};
  byId('work-prev').onclick=()=>{workPage--;drawWork();};byId('work-next').onclick=()=>{workPage++;drawWork();};
  byId('search-form').onsubmit=event=>{event.preventDefault();search();};
  byId('result-prev').onclick=()=>{resultPage--;drawResults();};byId('result-next').onclick=()=>{resultPage++;drawResults();};
  byId('download-json').onclick=()=>{
    const url=URL.createObjectURL(new Blob([JSON.stringify(record)],{type:'application/json'}));
    const anchor=node('a');anchor.href=url;anchor.download=`project-${record.project.id}.json`;anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  };
  drawWork();drawResults();
})();
