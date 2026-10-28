const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname,'..');
test('Every declared Outlook domain passes background validation', () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(root,'extensions/outlook/manifest.json'),'utf8'));
  let listener;
  const calls = [];
  const chrome = {runtime:{id:'test-extension',onMessage:{addListener:fn=>listener=fn},sendNativeMessage:(host,payload,reply)=>{calls.push({host,payload});reply({ok:true});}}};
  const context = vm.createContext({chrome,URL,URLSearchParams});
  context.importScripts = filename=>vm.runInContext(fs.readFileSync(path.join(root,'extensions/outlook',filename),'utf8'),context);
  vm.runInContext(fs.readFileSync(path.join(root,'extensions/outlook/background.js'),'utf8'),context);
  assert.ok(manifest.content_scripts[0].matches.includes('https://outlook.cloud.microsoft/*'));
  for (const match of manifest.content_scripts[0].matches) {
    const url = match.replace('*.','webmail.').replace('*','mail/inbox/id/fixture');
    let result;
    assert.equal(listener({type:'desktask-import',payload:{title:'Test',url:'https://invalid.example/'}},{id:chrome.runtime.id,url},value=>result=value),true);
    assert.equal(result.ok,true);
    assert.equal(calls.at(-1).payload.url,url);
  }
  const count = calls.length;
  for (const url of ['https://outlook.cloud.microsoft.attacker.example/mail','http://outlook.cloud.microsoft/mail','https://mail.qq.com.evil.example/','https://mail.163.com.evil.example/']) {
    assert.equal(listener({type:'desktask-import',payload:{}},{id:chrome.runtime.id,url},()=>{}),false);
  }
  assert.equal(calls.length,count);
  listener({type:'desktask-import',payload:{}},{id:chrome.runtime.id,url:'https://mail.qq.com/cgi-bin/readmail?sid=PRIVATE&mailid=123'},()=>{});
  assert.equal(calls.at(-1).payload.url,'https://mail.qq.com/cgi-bin/readmail?mailid=123');
});
