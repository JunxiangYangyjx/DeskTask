const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const context = vm.createContext({URL,URLSearchParams});
vm.runInContext(fs.readFileSync(path.join(__dirname,'../extensions/outlook/providers.js'),'utf8'),context);
const providers = context.DeskTaskMailProviders;
test('Providers accept only intended HTTPS mailbox hosts',()=>{
  for(const host of ['mail.google.com','mail.qq.com','wx.mail.qq.com','mail.163.com','hw.mail.163.com','webmail.mail.126.com']) assert.ok(providers.provider(host));
  for(const host of ['mail.qq.com.attacker.example','notmail.163.com','mail.google.com.evil']) assert.equal(providers.provider(host),undefined);
  for(const url of ['http://mail.qq.com/','https://user:pass@mail.qq.com/','https://mail.qq.com:444/']) assert.throws(()=>providers.safeUrl(url));
});
test('Session parameters are removed, including those in SPA routes',()=>{
  assert.equal(providers.safeUrl('https://mail.qq.com/cgi-bin/readmail?sid=PRIVATE&mailid=123'),'https://mail.qq.com/cgi-bin/readmail?mailid=123');
  assert.equal(providers.safeUrl('https://mail.163.com/js6/main.jsp?sid=PRIVATE#/read?mid=123&token=SECRET'),'https://mail.163.com/js6/main.jsp#/read?mid=123');
  assert.equal(providers.safeUrl('https://mail.google.com/mail/u/0/#inbox/message1'),'https://mail.google.com/mail/u/0/#inbox/message1');
});
