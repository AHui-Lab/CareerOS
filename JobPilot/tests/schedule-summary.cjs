'use strict';
const assert=require('node:assert/strict');
const {nearTerm}=require('../jobpilot/static/schedule-summary.js');
const event=(id,date,time='',type='interview',source='manual')=>({id,event_date:date,event_time:time,event_type:type,source});
const result=nearTerm([
  event(5,'2026-10-13','08:00'),event(3,'2026-10-12','09:00','signing'),
  event(1,'2026-10-10','14:00'),event(2,'2026-10-11','10:00','written_test'),
  event(4,'2026-10-10'),event(6,'2026-10-09'),
  event(7,'2026-10-10','','application','opportunity'),
  event(8,'2026-10-10','11:00','application'),event(9,'not-a-date')
],new Date(2026,9,10,23,59));
assert.equal(result.start,'2026-10-10');assert.equal(result.end,'2026-10-12');
assert.deepEqual(result.items.map(x=>x.id),[8,1,4,2,3]);
// All appointments survive selection; only the UI caps its preview.
assert.equal(result.items.length,5);assert.ok(result.items.some(x=>x.event_type==='signing'));
const year=nearTerm([event(1,'2027-01-01'),event(2,'2027-01-02'),event(3,'2026-12-31')],new Date(2026,11,31));
assert.equal(year.end,'2027-01-02');assert.deepEqual(year.items.map(x=>x.id),[3,1,2]);
const leap=nearTerm([event(1,'2028-02-29'),event(2,'2028-03-01'),event(3,'2028-02-30')],new Date(2028,1,28));
assert.equal(leap.end,'2028-03-01');assert.deepEqual(leap.items.map(x=>x.id),[1,2]);
assert.deepEqual(nearTerm([],new Date(2026,9,10)).items,[]);
console.log('Three-day schedule selection: dates, sorting, signing, and full-list preservation passed.');
