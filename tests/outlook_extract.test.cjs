const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {multiDateMail} = require('./outlook_fixtures.cjs');
const context = {};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../extensions/outlook/extract.js'), 'utf8'), context);
const extract = (text, year = 2026) => JSON.parse(JSON.stringify(context.DeskTaskMail.candidates(text, year)));
test('Chinese and English explicit dates with event time and location', () => {
  assert.deepEqual(extract('Date: 3 December 2026\nTime: 6:00 pm\nVenue: Melati Ballroom'), {
    dates:['2026-12-03'], time:'18:00', location:'Melati Ballroom'
  });
  assert.deepEqual(extract('日期：2026年10月17日\n时间：17:30\n地点：海洋馆').dates, ['2026-10-17']);
  assert.deepEqual(extract('October 17, 2026').dates, ['2026-10-17']);
});
test('Reject impossible dates and preserve explicitly written years', () => {
  assert.deepEqual(extract('February 30; 2026-02-30; 2026年2月30日; 30 Feb 2026').dates, []);
  assert.equal(extract('Time: 13 pm').time, '');
  assert.deepEqual(extract('2026-10-17 and 2026-12-03').dates, ['2026-10-17','2026-12-03']);
  assert.equal(extract('Received: 09:00').time, '');
});

test('Combined date/time labels default missing years to this year', () => {
  assert.deepEqual(extract('Date & Time:\t28 Oct 09:29 (SGT)'), {
    dates:['2026-10-28'], time:'09:29', location:'', assumedYear:2026
  });
  assert.deepEqual(extract('Date and Time: 28 Oct. 2026 9:29 pm (SGT)'), {
    dates:['2026-10-28'], time:'21:29', location:''
  });
  assert.equal(extract('日期时间：2026年10月28日 09:29').time, '09:29');
  assert.equal(extract('Date/Time: Oct. 28, 2026 00:05:30').time, '00:05');
  assert.deepEqual(extract('Date/Time: Oct. 28, 2026 00:05:30').dates, ['2026-10-28']);
  for (const text of ['Date & Time: 28 Oct 24:29', 'Date & Time: 28 Oct 09:60', 'Date & Time: 28 Oct 13:29 pm', 'Received: 28 Oct 09:29']) {
    assert.equal(extract(text).time, '');
  }
});

test('Yearless Chinese and English dates use the local current year without rolling forward', () => {
  for (const text of ['October 17', '17th Oct.', '10月17日', '10月17号']) {
    assert.deepEqual(extract(text).dates, ['2026-10-17']);
    assert.equal(extract(text).assumedYear, 2026);
    assert.deepEqual(extract(text, 2027).dates, ['2027-10-17']);
  }
  assert.deepEqual(extract('Oct 17, 2027; 17 October 2025; 2024年10月17日').dates, ['2027-10-17','2025-10-17','2024-10-17']);
  assert.equal(extract('Oct 17, 2027').assumedYear, undefined);
  assert.deepEqual(extract('Feb 29', 2026).dates, []);
  assert.deepEqual(extract('Feb 29', 2028).dates, ['2028-02-29']);
  assert.deepEqual(extract('January 2; December 31').dates, ['2026-01-02','2026-12-31']);
  assert.deepEqual(extract('03/04').dates, []);
  const steps = JSON.parse(JSON.stringify(context.DeskTaskMail.milestones('Register before 2 November. Training on 4 November.', 2027)));
  assert.deepEqual(steps.map(step=>step.due_date), ['2027-11-02','2027-11-04']);
});
test('One email produces registration, training, slides and competition milestones', () => {
  const steps = JSON.parse(JSON.stringify(context.DeskTaskMail.milestones(multiDateMail)));
  assert.deepEqual(steps.map(({title,due_date,time,end_time})=>({title,due_date,time,end_time})),[
    {title:'报名',due_date:'2026-11-02',time:'16:00',end_time:''},
    {title:'培训',due_date:'2026-11-04',time:'',end_time:''},
    {title:'交 PPT',due_date:'2026-11-09',time:'16:00',end_time:''},
    {title:'比赛',due_date:'2026-11-17',time:'13:00',end_time:'16:00'},
  ]);
  assert.ok(steps.every(step=>step.evidence.length>0));
  assert.deepEqual(JSON.parse(JSON.stringify(context.DeskTaskMail.milestones('Meeting mentioned on 17 November 2026.'))),[]);
});
