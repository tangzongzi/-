/* =================================================================
 * dashboard.js - 多赞采购单看板公共脚本
 * 包含：SVG icon 库 + 公共 resize 监听 + 工具函数
 * 用法：HTML 末尾加 <script src="../assets/dashboard.js"></script>
 * ================================================================= */

(function (global) {
  'use strict';

  // ============== SVG icon 库（Lucide 风格，24x24） ==============
  const ICONS = {
    chart:    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>',
    alert:    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    factory:  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/><path d="M17 18h1"/><path d="M12 18h1"/><path d="M7 18h1"/></svg>',
    store:    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m2 7 4.41-4.41A2 2 0 0 1 7.83 2h8.34a2 2 0 0 1 1.42.59L22 7"/><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><path d="M15 22v-4a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v4"/><path d="M2 7h20"/><path d="M22 7v3a2 2 0 0 1-2 2a2.27 2.27 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.27 2.27 0 0 1 16 12a2.27 2.27 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.27 2.27 0 0 1 12 12a2.27 2.27 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.27 2.27 0 0 1 8 12a2.27 2.27 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.27 2.27 0 0 1 4 12a2 2 0 0 1-2-2V7"/></svg>',
    package:  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16.5 9.4 7.55 4.24"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="M3.27 6.96 12 12.01l8.73-5.05"/><path d="M12 22.08V12"/></svg>',
    trend:    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>',
    trophy:   '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/></svg>',
    money:    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
    target:   '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    check:    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    bulb:     '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>',
    fire:     '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>',
    folder:   '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
    calendar: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
    clipboard:'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>',
    refresh:  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>'
  };

  // emoji → icon key 映射
  const EMOJI_MAP = {
    '📊': 'chart',
    '⚠': 'alert',
    '⚠️': 'alert',
    '🏭': 'factory',
    '🏪': 'store',
    '📦': 'package',
    '📈': 'trend',
    '🏆': 'trophy',
    '🏷': 'trophy',
    '💰': 'money',
    '🎯': 'target',
    '✅': 'check',
    '💡': 'bulb',
    '🔥': 'fire',
    '📁': 'folder',
    '📅': 'calendar',
    '📆': 'calendar',
    '🗓': 'calendar',
    '📋': 'clipboard',
    '🔄': 'refresh',
    '🛒': 'store',
    '🌟': 'trophy',
    '⭐': 'trophy',
    '📉': 'trend'
  };

  /**
   * 把 emoji 字符替换成 inline SVG
   * 用法：document.body.innerHTML = DASHBOARD.replaceEmojis(document.body.innerHTML);
   * 注意：会丢失 ECharts DOM 引用。谨慎用于动态内容，请用 replaceEmojisInTextNodes
   */
  function replaceEmojis(html) {
    return html.replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}]/gu, function (m) {
      // 去掉 VS16（变体选择符）后查表
      const normalized = m.replace(/\uFE0F/g, '');
      const key = EMOJI_MAP[normalized] || EMOJI_MAP[m];
      return key ? ICONS[key] : m;
    });
  }

  /**
   * 安全版：遍历文本节点替换 emoji，不破坏 DOM 结构（ECharts 友好）
   * 使用字符遍历避免全局 regex split 的 lastIndex bug
   */
  function replaceEmojisInTextNodes(root) {
    if (!root) return;
    const SHOW_TEXT = (typeof NodeFilter !== 'undefined' ? NodeFilter.SHOW_TEXT : 4);
    const walker = document.createTreeWalker(root, SHOW_TEXT, null, false);
    const targets = [];
    let n;
    while ((n = walker.nextNode())) {
      if (/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u.test(n.nodeValue)) targets.push(n);
    }
    targets.forEach(function (node) {
      const text = node.nodeValue;
      const frag = document.createDocumentFragment();
      // 拆成 code points 避免 surrogate pair 问题
      const codePoints = [];
      for (let k = 0; k < text.length; ) {
        const cp = text.codePointAt(k);
        codePoints.push({ cp, len: cp > 0xFFFF ? 2 : 1 });
        k += cp > 0xFFFF ? 2 : 1;
      }
      let i = 0;
      while (i < codePoints.length) {
        const { cp, len } = codePoints[i];
        const isEmoji = (cp >= 0x1F300 && cp <= 0x1FAFF) || (cp >= 0x2600 && cp <= 0x27BF);
        if (isEmoji) {
          // emoji 后可选 VS16
          let totalLen = len;
          if (i + 1 < codePoints.length && codePoints[i + 1].cp === 0xFE0F) {
            totalLen += codePoints[i + 1].len;
          }
          const emojiStr = String.fromCodePoint(cp) + (totalLen > len ? '\uFE0F' : '');
          const ch = String.fromCodePoint(cp);
          const key = EMOJI_MAP[emojiStr] || EMOJI_MAP[ch];
          if (key) {
            const span = document.createElement('span');
            span.style.cssText = 'display:inline-flex;vertical-align:-2px;margin-right:4px;color:var(--accent,#60a5fa)';
            span.innerHTML = ICONS[key];
            frag.appendChild(span);
          } else {
            frag.appendChild(document.createTextNode(emojiStr));
          }
          i++;
          if (totalLen > len) i++;  // 跳过 VS16
        } else {
          let next = i + 1;
          while (next < codePoints.length) {
            const ncp = codePoints[next].cp;
            if ((ncp >= 0x1F300 && ncp <= 0x1FAFF) || (ncp >= 0x2600 && ncp <= 0x27BF)) break;
            next++;
          }
          // 算 utf-16 offset
          let utf16Start = 0;
          for (let k = 0; k < i; k++) utf16Start += codePoints[k].len;
          let utf16End = utf16Start;
          for (let k = i; k < next; k++) utf16End += codePoints[k].len;
          frag.appendChild(document.createTextNode(text.slice(utf16Start, utf16End)));
          i = next;
        }
      }
      node.parentNode.replaceChild(frag, node);
    });
  }

  const EMOJI_REGEX = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}]/gu;

  /**
   * 公共 resize 监听（每个页面只需调用一次）
   */
  function initResize() {
    let timer;
    window.addEventListener('resize', function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        document.querySelectorAll('.chart, .chart-sm, .chart-lg, .chart-xl, [id^="chart-"]').forEach(function (el) {
          const inst = echarts.getInstanceByDom(el);
          if (inst) inst.resize();
        });
      }, 100);
    });
  }

  /**
   * 通用 fetch 加载 + 渲染
   * @param {string} url - 数据 JSON 路径
   * @param {function} renderFn - 渲染函数
   */
  async function load(url, renderFn) {
    try {
      const DATA = await fetch(url).then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      });
      if (typeof renderFn === 'function') renderFn(DATA);
    } catch (e) {
      console.error('[dashboard] 加载失败:', url, e);
      const root = document.querySelector('.dashboard, body');
      if (root) {
        const err = document.createElement('div');
        err.style.cssText = 'background:#450a0a;color:#fecaca;padding:16px;border-radius:8px;margin:20px 0;font-size:13px;';
        err.textContent = '❌ 数据加载失败: ' + url + ' (' + e.message + ')';
        root.prepend(err);
      }
    }
  }

  // ============== 自动启动 ==============
  function boot() {
    // 1. 初始 emoji 替换（DOM 已有内容）
    if (document.body) {
      replaceEmojisInTextNodes(document.body);
    }
    // 2. resize 监听
    if (typeof echarts !== 'undefined') {
      initResize();
    }
    // 3. 轮询检查：JS 动态填的 emoji
    // MutationObserver 在 ECharts 重度页面会被数十个内部 mutation 淹没，轮询更稳
    let lastCount = -1;
    setInterval(function () {
      if (!document.body) return;
      // 快速检查是否还有 emoji
      const text = document.body.textContent;
      if (text.length === 0) return;
      const re = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u;
      if (!re.test(text)) {
        // 没了就不扫
        if (lastCount !== 0) lastCount = 0;
        return;
      }
      replaceEmojisInTextNodes(document.body);
    }, 800);
  }

  // DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  // ============== 暴露 API ==============
  global.DASHBOARD = {
    icons: ICONS,
    icon: function (key) { return ICONS[key] || ''; },
    replaceEmojis: replaceEmojis,
    replaceEmojisInTextNodes: replaceEmojisInTextNodes,
    initResize: initResize,
    load: load
  };

})(window);

// ============== ECharts 亮色主题 ==============
echarts.registerTheme('light', {
  color: ['#1677ff','#722ed1','#13c2c2','#fa8c16','#52c41a','#eb2f96','#faad14','#2f54eb'],
  backgroundColor: 'transparent',
  textStyle: { color: 'rgba(0,0,0,.65)' },
  title: { textStyle: { color: 'rgba(0,0,0,.88)' }, subtextStyle: { color: 'rgba(0,0,0,.45)' } },
  legend: { textStyle: { color: 'rgba(0,0,0,.65)' } },
  tooltip: {
    backgroundColor: 'rgba(255,255,255,.96)',
    borderColor: '#e8e8e8',
    borderWidth: 1,
    textStyle: { color: 'rgba(0,0,0,.88)' },
    extraCssText: 'box-shadow: 0 3px 8px rgba(0,0,0,.12);'
  },
  categoryAxis: {
    axisLine: { lineStyle: { color: '#e8e8e8' } },
    axisTick: { lineStyle: { color: '#e8e8e8' } },
    axisLabel: { color: 'rgba(0,0,0,.45)' },
    splitLine: { lineStyle: { color: '#f0f0f0' } }
  },
  valueAxis: {
    axisLine: { lineStyle: { color: '#e8e8e8' } },
    axisTick: { lineStyle: { color: '#e8e8e8' } },
    axisLabel: { color: 'rgba(0,0,0,.45)' },
    splitLine: { lineStyle: { color: '#f0f0f0' } }
  },
  dataZoom: {
    borderColor: '#e8e8e8',
    backgroundColor: '#fafafa',
    fillerColor: 'rgba(22,119,255,.08)',
    handleStyle: { color: '#1677ff' },
    textStyle: { color: 'rgba(0,0,0,.45)' }
  }
});

// ============== Tooltip CSS 注入 ==============
(function() {
  function inject() {
    if (document.getElementById('tooltip-fix')) return;
    var s = document.createElement('style');
    s.id = 'tooltip-fix';
    s.textContent = 
      '.has-tip{position:relative;cursor:help;display:inline-block}' +
      '.tip-icon{display:inline-flex;align-items:center;justify-content:center;width:16px;height:16px;border-radius:50%;background:#f2f3f5;color:#86909c;font-size:10px;font-weight:700;line-height:1;flex-shrink:0;transition:all .15s ease}' +
      '.has-tip:hover .tip-icon{background:rgba(22,93,255,.08);color:#165dff}' +
      '.tip-text{visibility:hidden!important;opacity:0!important;position:absolute!important;bottom:calc(100% + 8px);left:0;background:#1d2129;color:#fff;padding:8px 12px;border-radius:6px;font-size:12px;font-weight:400;line-height:1.6;white-space:normal;min-width:160px;max-width:280px;z-index:999;pointer-events:none;box-shadow:0 4px 12px rgba(0,0,0,.15);transition:opacity .15s ease,visibility .15s ease}' +
      '.tip-text::after{content:"";position:absolute;top:100%;left:16px;border:5px solid transparent;border-top-color:#1d2129}' +
      '.has-tip:hover .tip-text{visibility:visible!important;opacity:1!important}';
    document.head.appendChild(s);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
})();
