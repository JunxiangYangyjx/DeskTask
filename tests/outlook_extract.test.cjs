const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {multiDateMail} = require('./outlook_fixtures.cjs');
const context = {};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../extensions/outlook/extract.js'), 'utf8'), context);
const extract = text => JSON.parse(JSON.stringify(context.DeskTaskOutlook.candidates(text)));
test('Chinese and English explicit dates with event time and location', () => {
  assert.deepEqual(extract('Date: 3 December 2026\nTime: 6:00 pm\nVenue: Melati Ballroom'), {
    dates:['2026-12-03'], time:'18:00', location:'Melati Ballroom'
  });
  assert.deepEqual(extract('日期：2026年10月17日\n时间：17:30\n地点：海洋馆').dates, ['2026-10-17']);
  assert.deepEqual(extract('October 17, 2026').dates, ['2026-10-17']);
});
test('Do not infer missing years or accept impossible dates', () => {
  assert.deepEqual(extract('October 17; 2026-02-30').dates, []);
  assert.equal(extract('Time: 13 pm').time, '');
  assert.deepEqual(extract('2026-10-17 and 2026-12-03').dates, ['2026-10-17','2026-12-03']);
  assert.equal(extract('Received: 09:00').time, '');
});
test('One email produces registration, training, slides and competition milestones', () => {
  const steps = JSON.parse(JSON.stringify(context.DeskTaskOutlook.milestones(multiDateMail)));
  assert.deepEqual(steps.map(({title,due_date,time,end_time})=>({title,due_date,time,end_time})),[
    {title:'报名',due_date:'2026-11-02',time:'16:00',end_time:''},
    {title:'培训',due_date:'2026-11-04',time:'',end_time:''},
    {title:'交 PPT',due_date:'2026-11-09',time:'16:00',end_time:''},
    {title:'比赛',due_date:'2026-11-17',time:'13:00',end_time:'16:00'},
  ]);
  assert.ok(steps.every(step=>step.evidence.length>0));
  assert.deepEqual(JSON.parse(JSON.stringify(context.DeskTaskOutlook.milestones('Meeting mentioned on 17 November 2026.'))),[]);
});
