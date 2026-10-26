(() => {
  const visible = node => node instanceof Element && node.getClientRects().length > 0 && getComputedStyle(node).visibility !== "hidden";
  const validDate = (year, month, day) => {
    const value = new Date(Date.UTC(+year, +month - 1, +day));
    return value.getUTCFullYear() === +year && value.getUTCMonth() === +month - 1 && value.getUTCDate() === +day
      ? `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}` : "";
  };
  function dateOccurrences(body) {
    const dates = [];
    for (const match of body.matchAll(/\b(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})(?:日)?/g)) {
      const value = validDate(match[1], match[2], match[3]);
      if (value) dates.push({date:value, start:match.index, end:match.index + match[0].length});
    }
    const months = {jan:1,feb:2,mar:3,apr:4,may:5,jun:6,jul:7,aug:8,sep:9,oct:10,nov:11,dec:12};
    const monthPattern = "(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)";
    for (const match of body.matchAll(new RegExp(`\\b(\\d{1,2})(?:st|nd|rd|th)?\\s+${monthPattern}[,\\s]+(20\\d{2})\\b`, "gi"))) {
      const value = validDate(match[3], months[match[2].slice(0,3).toLowerCase()], match[1]);
      if (value) dates.push({date:value, start:match.index, end:match.index + match[0].length});
    }
    for (const match of body.matchAll(new RegExp(`\\b${monthPattern}\\s+(\\d{1,2})(?:st|nd|rd|th)?[,\\s]+(20\\d{2})\\b`, "gi"))) {
      const value = validDate(match[3], months[match[1].slice(0,3).toLowerCase()], match[2]);
      if (value) dates.push({date:value, start:match.index, end:match.index + match[0].length});
    }
    return dates.sort((a,b) => a.start - b.start);
  }
  function candidates(body) {
    const dates = new Set(dateOccurrences(body).map(value=>value.date));
    const location = body.match(/(?:^|\n)\s*(?:地点|地址|Venue|Location)\s*[:：]\s*([^\n]+)/i)?.[1]?.trim() || "";
    // Only suggest a start time on a line explicitly labelled as an event time.
    const timeMatch = body.match(/(?:^|\n)\s*(?:时间|Time|Start)\s*[:：]\s*(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)?\b/i);
    let time = "";
    if (timeMatch) {
      let hour = +timeMatch[1];
      const minute = +(timeMatch[2] || 0);
      const meridiem = timeMatch[3]?.toLowerCase();
      const validHour = meridiem ? hour >= 1 && hour <= 12 : hour <= 23;
      if (meridiem && validHour) hour = hour % 12 + (meridiem === "pm" ? 12 : 0);
      if (validHour && minute <= 59) time = `${String(hour).padStart(2,"0")}:${String(minute).padStart(2,"0")}`;
    }
    return {dates: [...dates], location, time};
  }
  function milestones(body) {
    const rules = [
      {kind:'registration',title:'报名',pattern:/register(?:ing|ed)?|registration|报名/gi},
      {kind:'slides',title:'交 PPT',pattern:/(?:submit|submission|upload)[^.!?\n]{0,100}(?:slides?|ppt|powerpoint)|(?:slides?|ppt|powerpoint)[^.!?\n]{0,30}(?:submission|deadline)|交\s*ppt|提交[^。！？\n]{0,25}(?:ppt|幻灯片|演示文稿)/gi},
      {kind:'training',title:'培训',pattern:/workshop|training|preparatory course|培训|预备课程/gi},
      {kind:'event',title:/\b3mt\b|\bcompetition\b|比赛|竞赛/i.test(body)?'比赛':'参加活动',pattern:/oral presentation|competition|比赛|竞赛|(?:^|\n)\s*(?:Date|日期)\s*[:：]/gi},
    ];
    const found = new Map();
    const dates = dateOccurrences(body);
    const eventTime = candidates(body).time;
    const labelledTime = body.match(/(?:^|\n)\s*(?:时间|Time)\s*[:：]\s*([^\n]+(?:\n[^\n]+)?)/i)?.[1] || '';
    const rangeEnd = labelledTime.match(/[-–—至]\s*(\d{1,2}:\d{2})\b/)?.[1] || '';
    dates.forEach((occurrence,index) => {
      const start = Math.max(index ? dates[index-1].end : 0, occurrence.start - 300);
      const prefix = body.slice(start,occurrence.start);
      let chosen;
      for (const rule of rules) {
        rule.pattern.lastIndex = 0;
        for (const match of prefix.matchAll(rule.pattern)) {
          if (!chosen || match.index >= chosen.index) chosen = {...rule,index:match.index};
        }
      }
      if (!chosen) return;
      const times = [...prefix.slice(chosen.index).matchAll(/\b(\d{1,2}):(\d{2})\s*(am|pm)?\b/gi)];
      let clock = '';
      if (chosen.kind === 'event') clock = eventTime;
      else if (times.length) {
        const match = times.at(-1);
        let hour = +match[1];
        const valid = match[3] ? hour >= 1 && hour <= 12 : hour <= 23;
        if (match[3]) hour = hour % 12 + (match[3].toLowerCase() === 'pm' ? 12 : 0);
        if (valid && +match[2] <= 59) clock = `${String(hour).padStart(2,'0')}:${match[2]}`;
      }
      const identity = `${chosen.kind}-${occurrence.date}`;
      const step = {id:identity,title:chosen.title,due_date:occurrence.date,time:clock,
        end_time:chosen.kind === 'event' && clock && rangeEnd > clock ? rangeEnd : '',
        evidence:body.slice(start + chosen.index,Math.min(body.length,occurrence.end + 60)).trim()};
      const previous = found.get(identity);
      if (!previous || (!previous.time && step.time)) found.set(identity,step);
    });
    return [...found.values()].sort((a,b)=>a.due_date.localeCompare(b.due_date));
  }
  function readMail(doc = document) {
    const bodies = [...doc.querySelectorAll('[role="document"], .allowTextSelection [class*="Body"], [data-testid="message-body"]')]
      .filter(node => visible(node) && node.innerText.trim());
    const bodyNode = bodies.at(-1);
    const selected = doc.getSelection()?.toString().trim();
    const body = (selected || bodyNode?.innerText || "").trim().slice(0, 20000);
    const region = bodyNode?.closest('[role="main"], main') || doc.querySelector('[role="main"], main') || doc;
    // Outlook's conversation subject precedes level-3 sender/date headings.
    const headings = [...region.querySelectorAll('[data-testid="message-subject"], [role="heading"], h1, h2, h3')].filter(visible);
    const subject = headings.map(node => node.innerText.trim()).find(Boolean) || "邮件待办";
    const extractionWarning = body ? "" : "未识别到邮件正文，可在下方粘贴正文并填写事项。";
    return {title: subject, subject, body, url: location.href, extractionWarning, ...candidates(body), milestones:milestones(body)};
  }
  globalThis.DeskTaskOutlook = {readMail, candidates, milestones};
})();
