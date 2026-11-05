/* Build interactive day views from the same table that Wix CMS edits. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else Promise.resolve(root.siteContentReady).then(() => api.init(document));
})(typeof window !== 'undefined' ? window : globalThis, () => {
  'use strict';
  const days = ['monday','tuesday','wednesday','thursday','friday','saturday'];
  const normalize = value => String(value || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[’']/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
  const matches = (item, query) => normalize(query).split(/\s+/).filter(Boolean).every(word => normalize(item.name + ' ' + item.description).includes(word));
  function timeOrder(value) {
    const match = /^(\d{1,2}):(\d{2})\s*(AM|PM)$/i.exec(value.trim());
    if (!match) return Infinity;
    return (+match[1] % 12) * 60 + +match[2] + (match[3].toUpperCase() === 'PM' ? 720 : 0);
  }
  function dayMeetings(items, day, query) {
    return items.filter(item => item.times[day] && matches(item,query))
      .map((item,index) => ({...item,time:item.times[day],index}))
      .sort((a,b) => (timeOrder(a.time)-timeOrder(b.time)) || a.index-b.index);
  }
  function init(document) {
    const page = document.querySelector('[data-schedule]');
    if (!page) return;
    const table = page.querySelector('.schedule-table');
    const items = [...table.tBodies[0].rows].filter(row=>!row.hidden).map(row => ({
      row, name:row.querySelector('.schedule-class-name').textContent.trim(),
      description:row.querySelector('.schedule-class-detail').textContent.trim(),
      times:Object.fromEntries(days.map((day,i)=>[day,row.querySelectorAll('td')[i+1].textContent.trim()]))
    }));
    const controls = page.querySelector('[data-schedule-tools]');
    const tabs = [...page.querySelectorAll('[data-schedule-day]')];
    const panel = page.querySelector('#schedule-results');
    const dayView = page.querySelector('[data-schedule-day-view]');
    const week = page.querySelector('[data-schedule-week]');
    const heading = page.querySelector('#schedule-day-heading');
    const dayRows = page.querySelector('[data-schedule-day-rows]');
    const search = page.querySelector('#schedule-search');
    const clear = page.querySelector('[data-schedule-clear]');
    const empty = page.querySelector('[data-schedule-empty]');
    const status = page.querySelector('[data-schedule-status]');
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    let selected = 'monday';
    function render(animate = false) {
      const query = search.value;
      const weekly = selected === 'week';
      const result = weekly ? items.filter(item=>matches(item,query)) : dayMeetings(items,selected,query);
      tabs.forEach(tab=>{const active=tab.dataset.scheduleDay===selected;tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;});
      panel.setAttribute('role','tabpanel');
      panel.setAttribute('aria-labelledby','schedule-tab-'+selected);
      panel.tabIndex=0;
      clear.hidden=!query;
      empty.hidden=result.length>0;
      week.hidden=!weekly || !result.length;
      dayView.hidden=weekly || !result.length;
      if (weekly) items.forEach(item=>{item.row.hidden=!matches(item,query);});
      else {
        heading.textContent=selected[0].toUpperCase()+selected.slice(1);
        dayRows.replaceChildren(...result.map(item=>{
          const row=document.createElement('tr');
          const time=document.createElement('th');time.scope='row';time.textContent=item.time;
          const cell=document.createElement('td');
          const name=document.createElement('span');name.className='schedule-day-name';name.textContent=item.name;cell.append(name);
          if(item.description){const detail=document.createElement('span');detail.className='schedule-day-detail';detail.textContent=item.description;cell.append(detail);}
          row.append(time,cell);return row;
        }));
      }
      status.textContent=result.length+' '+(result.length===1?'class':'classes')+(weekly?' in the full week':' on '+heading.textContent)+(query?' matching '+query:'')+'.';
      if(animate && !reduced.matches && panel.animate) panel.animate([{opacity:.35,transform:'translateY(5px)'},{opacity:1,transform:'translateY(0)'}],{duration:210,easing:'ease-out'});
    }
    tabs.forEach((tab,index)=>{
      tab.addEventListener('click',()=>{selected=tab.dataset.scheduleDay;render(true);});
      tab.addEventListener('keydown',event=>{
        let next;
        if(event.key==='ArrowRight')next=(index+1)%tabs.length;
        if(event.key==='ArrowLeft')next=(index-1+tabs.length)%tabs.length;
        if(event.key==='Home')next=0;
        if(event.key==='End')next=tabs.length-1;
        if(next!==undefined){event.preventDefault();tabs[next].focus();selected=tabs[next].dataset.scheduleDay;render(true);}
      });
    });
    search.addEventListener('input',()=>render());
    search.addEventListener('keydown',event=>{if(event.key==='Escape' && search.value){event.preventDefault();search.value='';render();}});
    clear.addEventListener('click',()=>{search.value='';render();search.focus();});
    page.querySelector('[data-schedule-reset]').addEventListener('click',()=>{search.value='';selected='week';render(true);search.focus();});
    controls.hidden=false;
    render();
  }
  return {normalize,matches,timeOrder,dayMeetings,init};
});
