import test from 'node:test';
import assert from 'node:assert/strict';
import schedule from '../assets/schedule.js';
import {execFileSync} from 'node:child_process';
const rows=JSON.parse(execFileSync('python3',['-c',"import sys,json;sys.path.insert(0,'scripts');from render_schedule import ROWS;print(json.dumps([{'name':n,'description':d,'times':{k.lower():v for k,v in t.items()}} for n,d,t in ROWS]))"],{encoding:'utf8'}));
test('every existing meeting is available in its daily view',()=>{
  const days=['monday','tuesday','wednesday','thursday','friday','saturday'];
  assert.deepEqual(days.map(d=>schedule.dayMeetings(rows,d,'').length),[6,7,8,7,1,7]);
  assert.equal(rows.length,28);
});
test('daily view orders explicit times and retains ambiguous rehearsal times',()=>{
  assert.equal(schedule.dayMeetings(rows,'monday','')[0].time,'4:15PM');
  assert.equal(schedule.dayMeetings(rows,'saturday','')[0].time,'8:15AM');
  assert.equal(schedule.dayMeetings(rows,'saturday','').at(-1).time,'12:00-5:00');
  assert.equal(schedule.dayMeetings(rows,'friday','')[0].time,'4:00-7:00');
});
test('search handles punctuation, descriptions and combinations without changing data',()=>{
  assert.equal(rows.filter(r=>schedule.matches(r,'hip hop')).length,4);
  assert.equal(schedule.dayMeetings(rows,'monday','hip hop').length,2);
  assert.equal(schedule.dayMeetings(rows,'monday','ballet 9').length,2);
  assert.equal(rows.filter(r=>schedule.matches(r,"trot’n tots")).length,1);
  assert.equal(schedule.dayMeetings(rows,'wednesday','no such class').length,0);
});
