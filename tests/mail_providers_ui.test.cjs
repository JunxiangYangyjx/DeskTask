const {test} = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {chromium} = require('../build/outlook-qa/node_modules/playwright');
const root = path.join(__dirname,'..');
test('Gmail, QQ and NetEase extraction and local preview handoff',async()=>{
  const browser = await chromium.launch({channel:'chrome',headless:true});
  try {
    const cases = [
      {provider:'gmail',url:'https://mail.google.com/mail/u/0/#inbox/message1',html:'<h2 class="hP">Gmail event</h2><div class="a3s aiL">日期：2026年11月16日<br>地点：Room A</div><div class="a3s aiL"></div>',title:'Gmail event'},
      {provider:'gmail',url:'https://mail.google.com/mail/u/0/#inbox/message2',html:'<h2 class="hP">Gmail date and time</h2><div class="a3s aiL"><table><tr><td>Date &amp; Time:</td><td>28 Oct 09:29 (SGT)</td></tr></table></div>',title:'Gmail date and time',date:'2026-10-28',time:'09:29',location:'',missingYear:true},
      {provider:'qq',url:'https://wx.mail.qq.com/#/read/123?sid=PRIVATE',html:'<h1 class="mail-title">QQ event</h1><iframe id="mailContentFrame" src="/body"></iframe>',frame:'<div id="mailContentContainer">日期：2026年11月16日<br>地点：Room A</div>',title:'QQ event'},
      {provider:'qq',url:'https://wx.mail.qq.com/#/read/456',html:'<div class="mail-detail-subject"><span class="mail-subject-text">QQ 公告</span></div><div class="mail-detail-content"><div class="qmbox"><h1>正文里的品牌名称</h1><p>有效期至： 2024-11-12 00:00:00</p></div></div>',title:'QQ 公告',date:'2024-11-12',time:'00:00',location:''},
      {provider:'netease',url:'https://mail.163.com/js6/main.jsp?sid=PRIVATE#/read?mid=123',html:'<h1 class="readMsgSubject">网易 event</h1><iframe id="mailContentFrame" src="/body"></iframe>',frame:'日期：2026年11月16日<br>地点：Room A',title:'网易 event'},
      {provider:'netease',url:'https://mail.126.com/js6/main.jsp#/read?mid=123',html:'<h1 class="readMsgSubject">126 event</h1><div class="mailContent">日期：2026年11月16日<br>地点：Room A</div>',title:'126 event'},
    ];
    for(const example of cases){
      const page = await browser.newPage({viewport:{width:1100,height:820}});
      await page.clock.setFixedTime(new Date('2026-10-28T12:00:00+08:00'));
      await page.route('**/*',route=>route.fulfill({contentType:'text/html',body:`<!doctype html><meta charset="utf-8">${new URL(route.request().url()).pathname==='/body'?example.frame:example.html}`}));
      await page.goto(example.url);
      if(example.frame) await page.frameLocator('#mailContentFrame').locator('body').waitFor();
      await page.evaluate(()=>{
        const attach=Element.prototype.attachShadow;
        Element.prototype.attachShadow=function(options){return attach.call(this,{...options,mode:'open'});};
        window.chrome={runtime:{sendMessage:async message=>{window.sentImport=message;return {ok:true};}}};
      });
      for(const file of ['providers.js','extract.js','content.js']) await page.addScriptTag({path:path.join(root,'extensions/outlook',file)});
      await page.getByRole('button',{name:'加入 DeskTask',exact:true}).click();
      assert.equal(await page.getByLabel('事项',{exact:true}).inputValue(),example.title);
      assert.equal(await page.locator('input[name="date"]').inputValue(),example.date ?? '2026-11-16');
      assert.equal(await page.getByLabel('地点',{exact:true}).inputValue(),example.location ?? 'Room A');
      if(example.time) {
        assert.equal(await page.getByLabel('提醒时间（本地时区）',{exact:true}).inputValue(),example.time);
        if(example.date === '2024-11-12') await page.getByText('邮件日期 2024-11-12 已过去，请核对是否仍要导入。',{exact:true}).waitFor();
      }
      if(example.missingYear) {
        await page.getByText('邮件中未写年份的日期已按今年（2026 年）补全。',{exact:false}).waitFor();
      }
      await page.screenshot({path:path.join(root,`build/outlook-qa/provider-${example.provider}.png`)});
      await page.getByRole('button',{name:'确认加入',exact:true}).click();
      await page.getByRole('status').filter({hasText:'已发送至 DeskTask'}).waitFor();
      const payload=await page.evaluate(()=>window.sentImport.payload);
      assert.equal(payload.provider,example.provider);
      assert.equal(payload.due_date,example.date ?? '2026-11-16');
      assert.ok(!payload.url.includes('PRIVATE'));
      await page.close();
    }
  } finally {await browser.close();}
});
