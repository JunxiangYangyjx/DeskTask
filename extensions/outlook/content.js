(() => {
  if (document.getElementById("desktask-outlook-extension")) return;
  const host = document.createElement("div");
  host.id = "desktask-outlook-extension";
  host.style.cssText = "position:fixed;bottom:24px;right:24px;z-index:2147483647";
  const root = host.attachShadow({mode: "closed"});
  const style = document.createElement("style");
  style.textContent = `
    :host{font:14px "Microsoft YaHei",sans-serif;color:#202124;letter-spacing:0}
    *{box-sizing:border-box}button,input,textarea,select{font:inherit}
    button{cursor:pointer;border:1px solid #d4d8de;border-radius:6px;background:white;color:#202124;padding:8px 12px}
    button:disabled{opacity:.6;cursor:wait}.primary{background:#176b55;color:white;border-color:#176b55}
    .overlay{position:fixed;inset:0;background:#0005;display:flex;align-items:center;justify-content:center;padding:16px}
    form{width:560px;max-width:100%;max-height:90vh;overflow:auto;background:#fff;padding:22px;border-radius:8px;box-shadow:0 12px 48px #0004}
    h2{margin:0 0 18px;font-size:18px}label{display:block;margin:12px 0 5px}
    input,textarea,select{width:100%;min-width:0;padding:8px;border:1px solid #b8bec7;border-radius:4px;background:white;color:#202124}
    textarea{min-height:110px;resize:vertical}.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    .actions{display:flex;justify-content:flex-end;gap:8px;margin-top:18px}.status{color:#a32121;margin-top:12px;white-space:pre-wrap;overflow-wrap:anywhere}
    .link{font-size:12px;color:#555;overflow-wrap:anywhere;margin-top:12px}.hint{font-size:12px;color:#665320;margin:6px 0}
    [hidden]{display:none!important}.check{display:flex;align-items:center;gap:8px}.check input{width:auto}
    h3{font-size:15px;margin:0}.step-head{display:flex;align-items:center;justify-content:space-between;margin-top:16px}
    .step{padding:12px 0;border-bottom:1px solid #e0e3e7}.step .check{margin:0 0 6px}
    .step-fields{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr) minmax(0,1fr);gap:8px}.step-fields label{font-size:12px}
    .evidence{font-size:12px;color:#555;margin-top:8px;overflow-wrap:anywhere;white-space:pre-wrap}
    .actions{position:sticky;bottom:-22px;background:white;padding:12px 0 4px;border-top:1px solid #e0e3e7}
    @media(max-width:440px){.row{grid-template-columns:1fr}form{padding:16px}.step-fields{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.step-fields>div:first-child{grid-column:1/-1}}
  `;
  root.append(style);
  const trigger = document.createElement("button");
  trigger.className = "primary";
  trigger.textContent = "加入 DeskTask";
  trigger.title = "将当前邮件加入本地待办";
  root.append(trigger);
  document.documentElement.append(host);
  trigger.addEventListener("click", () => {
    let mail;
    try { mail = DeskTaskOutlook.readMail(); } catch (error) { alert(error.message); return; }
    const overlay = document.createElement("div");
    overlay.className = "overlay";
    const form = document.createElement("form");
    form.setAttribute("role", "dialog");
    form.setAttribute("aria-modal", "true");
    form.setAttribute("aria-label", "加入 DeskTask");
    form.innerHTML = `<h2>加入 DeskTask</h2>
      <label for="title">事项</label><input id="title" name="title" maxlength="500" required>
      <label class="check"><input type="checkbox" name="grouped">同一日程，多个子事项</label>
      <section class="milestones" hidden><div class="step-head"><h3>子事项</h3><button type="button" id="add-step" title="添加子事项" aria-label="添加子事项">+</button></div><div class="steps"></div></section>
      <div class="row single-date"><div><label for="date">日期</label><input id="date" name="date" type="date"></div>
      <div><label for="time">提醒时间（本地时区）</label><input id="time" name="time" type="time"></div></div>
      <div class="hint"></div><label for="location">地点</label><input id="location" name="location" maxlength="1000">
      <label for="priority">类型</label><select id="priority" name="priority"><option value="reminder">提醒</option><option value="high">高优先级</option><option value="medium">中优先级</option><option value="low">低优先级</option></select>
      <label for="body">邮件摘录</label><textarea id="body" name="body" maxlength="20000" placeholder="可编辑或粘贴邮件正文"></textarea>
      <button type="button" id="rescan">重新识别子事项</button>
      <div class="link"></div><div class="status" role="status"></div>
      <div class="actions"><button type="button" id="cancel">取消</button><button type="submit" class="primary">确认加入</button></div>`;
    const field = name => form.elements.namedItem(name);
    field("title").value = mail.title;
    field("body").value = mail.body;
    field("location").value = mail.location;
    field("date").value = mail.dates.length === 1 ? mail.dates[0] : "";
    field("time").value = mail.dates.length === 1 ? mail.time : "";
    const defaultHint = mail.extractionWarning || (mail.dates.length > 1 ? `邮件含多个日期，请选择：${mail.dates.join("、")}` : mail.dates.length === 1 ? "请核对活动日期和时区。" : "未找到含年份的明确日期，可手动填写。");
    let nextStep = 0;
    const addStep = (step = {}) => {
      const index = ++nextStep;
      const row = document.createElement("div");
      row.className = "step";
      row.dataset.stepId = step.id || `manual-${index}`;
      row.innerHTML = `<label class="check"><input class="include" type="checkbox" checked>纳入日程</label>
        <label for="step-title-${index}">子事项名称</label><input class="step-title" id="step-title-${index}" maxlength="200" required>
        <div class="step-fields"><div><label for="step-date-${index}">日期</label><input class="step-date" id="step-date-${index}" type="date"></div>
        <div><label for="step-time-${index}">提醒 / 开始</label><input class="step-time" id="step-time-${index}" type="time"></div>
        <div><label for="step-end-${index}">结束</label><input class="step-end" id="step-end-${index}" type="time"></div></div>`;
      row.querySelector(".step-title").value = step.title || "";
      row.querySelector(".step-date").value = step.due_date || "";
      row.querySelector(".step-time").value = step.time || "";
      row.querySelector(".step-end").value = step.end_time || "";
      if (step.evidence) {
        const details = document.createElement("details");
        details.className = "evidence";
        const summary = document.createElement("summary");
        summary.textContent = "原文依据";
        const quote = document.createElement("p");
        quote.textContent = step.evidence;
        details.append(summary,quote);
        row.append(details);
      }
      row.dataset.evidence = step.evidence || "";
      row.querySelector(".include").onchange = event => {
        for (const input of row.querySelectorAll("input:not(.include)")) input.disabled = !event.target.checked;
      };
      form.querySelector(".steps").append(row);
    };
    for (const step of mail.milestones || []) addStep(step);
    field("grouped").checked = (mail.milestones || []).length > 1;
    const updateMode = () => {
      const grouped = field("grouped").checked;
      form.querySelector(".milestones").hidden = !grouped;
      form.querySelector(".single-date").hidden = grouped;
      field("date").disabled = grouped;
      field("time").disabled = grouped;
      for (const row of form.querySelectorAll(".step")) {
        for (const input of row.querySelectorAll("input:not(.include)")) input.disabled = !grouped || !row.querySelector(".include").checked;
      }
      form.querySelector(".hint").textContent = grouped ? "请核对子事项及各自日期、时间。" : defaultHint;
    };
    field("grouped").onchange = () => {
      if (field("grouped").checked && !form.querySelector(".step")) addStep();
      updateMode();
    };
    form.querySelector("#add-step").onclick = () => { addStep(); updateMode(); };
    form.querySelector("#rescan").onclick = () => {
      const steps = DeskTaskOutlook.milestones(field("body").value);
      form.querySelector(".steps").replaceChildren();
      nextStep = 0;
      for (const step of steps) addStep(step);
      field("grouped").checked = steps.length > 1;
      updateMode();
    };
    updateMode();
    form.querySelector(".link").textContent = mail.url;
    const close = () => { overlay.remove(); trigger.focus(); };
    form.querySelector("#cancel").onclick = close;
    overlay.addEventListener("keydown", event => {
      if (event.key === "Escape") close();
      if (event.key === "Tab") {
        const focusable = [...form.querySelectorAll("input,textarea,select,button")].filter(element => !element.disabled);
        const first = focusable[0], last = focusable.at(-1);
        if (event.shiftKey && root.activeElement === first) { event.preventDefault(); last.focus(); }
        if (!event.shiftKey && root.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    });
    form.onsubmit = async event => {
      event.preventDefault();
      const status = form.querySelector(".status");
      const grouped = field("grouped").checked;
      if (!grouped && field("time").value && !field("date").value) { status.textContent = "填写提醒时间时，请同时选择日期。"; return; }
      const steps = [...form.querySelectorAll(".step")].filter(row=>row.querySelector(".include").checked).map(row=>({
        id:row.dataset.stepId,title:row.querySelector(".step-title").value,
        due_date:row.querySelector(".step-date").value,time:row.querySelector(".step-time").value,
        end_time:row.querySelector(".step-end").value,evidence:row.dataset.evidence,
      }));
      if (grouped && !steps.length) { status.textContent = "请至少纳入一个子事项。"; return; }
      if (grouped && steps.some(step => (step.time || step.end_time) && !step.due_date)) { status.textContent = "有时间的子事项需要同时填写日期。"; return; }
      if (grouped && steps.some(step => step.end_time && (!step.time || step.end_time <= step.time))) { status.textContent = "结束时间需晚于当天开始时间。"; return; }
      if (location.href !== mail.url) { status.textContent = "当前邮件已改变，请取消后重新导入。"; return; }
      const submit = form.querySelector('[type="submit"]');
      submit.disabled = true;
      try {
        const {milestones:inferredSteps,...mailFields} = mail;
        const result = await chrome.runtime.sendMessage({type:"desktask-import", payload:{
          ...mailFields, title:field("title").value, body:field("body").value,
          due_date:grouped ? "" : field("date").value, time:grouped ? "" : field("time").value,
          location:field("location").value, priority:field("priority").value,
          ...(grouped ? {milestones:steps} : {}),
        }});
        if (!result?.ok) throw new Error(result?.error || "导入失败，请检查本地连接。");
        status.style.color = "#176b55";
        status.textContent = grouped ? `已发送至 DeskTask：1 条日程，${steps.length} 个子事项。` : "已发送至 DeskTask，程序启动后自动导入。";
        submit.hidden = true;
        form.querySelector("#cancel").textContent = "关闭";
      } catch (error) { status.style.color = "#a32121"; status.textContent = error.message; submit.disabled = false; }
    };
    overlay.append(form);
    root.append(overlay);
    field("title").focus();
  });
})();
