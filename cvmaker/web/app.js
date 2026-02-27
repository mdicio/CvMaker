/**
 * CV Maker — Web Builder  (app.js)
 *
 * Features:
 *  • Section-type templates: Work Experience, Education, Skills, Summary, Languages, Custom
 *  • Skill tag-chip input (press Enter / comma to add)
 *  • Autosave to localStorage (1.5 s debounce)
 *  • Collapsible sections
 *  • buildApiPayload() transforms frontend types → backend-compatible types before every API call
 *  • Smart section-type detection on markdown import
 */

'use strict';

// ─── ID generator ─────────────────────────────────────────────────────────
let _uid = 1;
const uid = () => _uid++;

// ─── Section type registry ────────────────────────────────────────────────
const SECTION_TYPES = {
  work: {
    label: 'Work Experience', icon: '💼',
    color: '#0284c7', bg: '#e0f2fe',
    defaultTitle: 'Work Experience', defaultDisplay: 'default',
    description: 'Job titles, companies & responsibilities',
    addLabel: 'Add Job', addItemType: 'work-entry',
  },
  education: {
    label: 'Education', icon: '🎓',
    color: '#7c3aed', bg: '#ede9fe',
    defaultTitle: 'Education', defaultDisplay: 'default',
    description: 'Degrees, institutions & qualifications',
    addLabel: 'Add Education', addItemType: 'education-entry',
  },
  skills: {
    label: 'Skills', icon: '🔧',
    color: '#059669', bg: '#d1fae5',
    defaultTitle: 'Skills', defaultDisplay: 'chips',
    description: 'Technical skills, tools & competencies',
    addLabel: 'Add Skill Group', addItemType: 'skill-group',
  },
  summary: {
    label: 'Profile / Summary', icon: '📝',
    color: '#d97706', bg: '#fef3c7',
    defaultTitle: 'Profile', defaultDisplay: 'default',
    description: 'Personal statement or career overview',
    addLabel: 'Add Paragraph', addItemType: 'paragraph',
  },
  languages: {
    label: 'Languages', icon: '🌐',
    color: '#db2777', bg: '#fce7f3',
    defaultTitle: 'Languages', defaultDisplay: 'default',
    description: 'Spoken languages & proficiency levels',
    addLabel: 'Add Language', addItemType: 'bullet',
  },
  custom: {
    label: 'Custom Section', icon: '📋',
    color: '#4f46e5', bg: '#e0e7ff',
    defaultTitle: 'New Section', defaultDisplay: 'default',
    description: 'Fully flexible — build any structure',
    addLabel: 'Add Item', addItemType: null, // shows dropdown
  },
};

// ─── Starter CV ─────────────────────────────────────────────────────────────
const STARTER_CV = {
  name: 'Jane Smith',
  subtitle: 'Software Engineer',
  contact: 'jane@example.com | +1 555 000 0000 | [LinkedIn](https://linkedin.com/in/janesmith) | London, UK',
  sections: [
    {
      sectionType: 'summary', title: 'Profile', display: 'default',
      content: [{ type: 'paragraph', text: 'Experienced software engineer with a passion for building scalable, user-friendly products. Adept at collaborating across teams and delivering high-quality solutions.' }],
    },
    {
      sectionType: 'work', title: 'Work Experience', display: 'default',
      content: [
        {
          type: 'work-entry', title: 'Senior Software Engineer', org: 'Tech Company Ltd',
          date: 'Jan 2022 – Present', location: 'London, UK', url: '',
          items: [
            { type: 'bullet', text: 'Led development of core product features used by 500K+ daily users', date: '' },
            { type: 'bullet', text: 'Mentored 3 junior engineers and conducted regular code reviews', date: '' },
          ],
        },
        {
          type: 'work-entry', title: 'Software Engineer', org: 'Startup Inc',
          date: 'Jun 2019 – Dec 2021', location: 'Remote', url: '',
          items: [
            { type: 'bullet', text: 'Built REST APIs serving 100K+ requests/day using Python and FastAPI', date: '' },
          ],
        },
      ],
    },
    {
      sectionType: 'education', title: 'Education', display: 'default',
      content: [{
        type: 'education-entry', title: 'BSc Computer Science', org: 'University of Example',
        date: '2015 – 2019', grade: 'First Class Hons', url: '', items: [],
      }],
    },
    {
      sectionType: 'skills', title: 'Skills', display: 'default',
      content: [
        { type: 'skill-group', category: 'Languages',           skills: ['Python', 'JavaScript', 'TypeScript', 'SQL'] },
        { type: 'skill-group', category: 'Frameworks & Tools',  skills: ['Django', 'React', 'Docker', 'AWS', 'Git'] },
      ],
    },
  ],
};

// ─── State ────────────────────────────────────────────────────────────────
const state = {
  cv: {
    name: '', subtitle: '', contact: '',
    sections: [],
  },
  template: 'default',
  previewTimer: null,
  autosaveTimer: null,
};

// ─── DOM helpers ──────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const el = (tag, cls, html) => {
  const e = document.createElement(tag);
  if (cls)  e.className = cls;
  if (html) e.innerHTML = html;
  return e;
};

// ─── Init ─────────────────────────────────────────────────────────────────
async function init() {
  await loadTemplates();
  loadFromStorage();
  buildSectionTypePicker();
  bindGlobalEvents();
  initResize();
  renderSections();
  schedulePreview(500);
}

// ─── Load templates ────────────────────────────────────────────────────────
async function loadTemplates() {
  try {
    const res  = await fetch('/api/templates');
    const list = await res.json();
    const sel  = $('templateSelect');
    sel.innerHTML = '';
    list.forEach(t => {
      const o = document.createElement('option');
      o.value = t.id; o.textContent = t.name;
      if (t.description) o.title = t.description;
      sel.appendChild(o);
    });
    sel.value = state.template;
  } catch (_) {}
}

// ─── Section type picker ──────────────────────────────────────────────────
function buildSectionTypePicker() {
  const grid = $('sectionTypeGrid');
  if (!grid) return;
  grid.innerHTML = Object.entries(SECTION_TYPES).map(([type, cfg]) => `
    <button class="stp-card" data-type="${type}"
      style="--stp-color:${cfg.color};--stp-bg:${cfg.bg}">
      <span class="stp-icon">${cfg.icon}</span>
      <span class="stp-label">${cfg.label}</span>
      <span class="stp-desc">${cfg.description}</span>
    </button>`).join('');

  grid.addEventListener('click', e => {
    const card = e.target.closest('[data-type]');
    if (!card) return;
    closeSectionPicker();
    addSectionWithType(card.dataset.type);
  });
}

function openSectionPicker() { $('sectionPickerModal').hidden = false; }
function closeSectionPicker() { $('sectionPickerModal').hidden = true; }

// ─── Global event bindings ─────────────────────────────────────────────────
function bindGlobalEvents() {
  // Personal info
  $('cvName').addEventListener('input',     e => { state.cv.name     = e.target.value; onChange(); });
  $('cvSubtitle').addEventListener('input', e => { state.cv.subtitle = e.target.value; onChange(); });
  $('cvContact').addEventListener('input',  e => { state.cv.contact  = e.target.value; onChange(); });

  // Template
  $('templateSelect').addEventListener('change', e => { state.template = e.target.value; schedulePreview(200); });

  // Toolbar
  $('newCvBtn').addEventListener('click',       newCv);
  $('addSectionBtn').addEventListener('click',  openSectionPicker);
  $('exportPdfBtn').addEventListener('click',   () => exportFile('pdf'));
  $('exportDocxBtn').addEventListener('click',  () => exportFile('docx'));
  $('exportMdBtn').addEventListener('click',    () => exportFile('markdown'));
  $('importBtn').addEventListener('click',      () => { $('importModal').hidden = false; });
  $('refreshPreviewBtn').addEventListener('click', forcePreview);
  $('printBtn').addEventListener('click',       printPreview);

  // Section picker modal
  $('closeSectionPickerBtn').addEventListener('click', closeSectionPicker);
  $('sectionPickerBackdrop').addEventListener('click', closeSectionPicker);

  // Import modal
  $('closeModalBtn').addEventListener('click',  closeModal);
  $('modalBackdrop').addEventListener('click',  closeModal);
  $('fileInput').addEventListener('change', e => { if (e.target.files[0]) importMarkdownFile(e.target.files[0]); });

  // Drop zone
  const dz = $('dropZone');
  dz.addEventListener('dragover',  e => { e.preventDefault(); dz.classList.add('dragover'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
  dz.addEventListener('drop', e => {
    e.preventDefault(); dz.classList.remove('dragover');
    const f = e.dataTransfer.files[0];
    if (f) importMarkdownFile(f);
  });

  // Section list delegation
  $('sectionsList').addEventListener('click',  onSectionsClick);
  $('sectionsList').addEventListener('input',  onSectionsInput);
  $('sectionsList').addEventListener('change', onSectionsChange);
  $('sectionsList').addEventListener('keydown', onSectionsKeydown);

  // Close menus on outside click
  document.addEventListener('click', () => {
    document.querySelectorAll('.add-item-menu.open').forEach(m => m.classList.remove('open'));
  });

  // Keyboard shortcuts
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { closeModal(); closeSectionPicker(); return; }
    const mod = e.ctrlKey || e.metaKey;
    if (mod && !e.shiftKey && e.key === 's') { e.preventDefault(); saveToStorage(); toast('Saved', 'success'); }
    if (mod && e.key === 'p') { e.preventDefault(); printPreview(); }
  });
}

// ─── onChange wrapper ──────────────────────────────────────────────────────
function onChange() {
  schedulePreview();
  scheduleAutosave();
  document.title = (state.cv.name ? `${state.cv.name} — ` : '') + 'CV Maker';
}

// ─── Click delegation ──────────────────────────────────────────────────────
function onSectionsClick(e) {
  const btn = e.target.closest('[data-action]');
  if (!btn || btn.disabled) return;
  const action = btn.dataset.action;
  const si = intOf(btn.dataset.si ?? btn.closest('[data-si]')?.dataset.si);
  const ii = intOf(btn.dataset.ii ?? btn.closest('[data-ii]')?.dataset.ii);
  const bi = intOf(btn.dataset.bi ?? btn.closest('[data-bi]')?.dataset.bi);

  switch (action) {
    case 'delete-section':    e.stopPropagation(); deleteSection(si);          break;
    case 'move-section-up':   moveSection(si, -1);                             break;
    case 'move-section-down': moveSection(si,  1);                             break;
    case 'toggle-section':    e.stopPropagation(); toggleSection(si);          break;
    case 'add-item-toggle':   e.stopPropagation(); toggleAddMenu(btn, si);     break;
    case 'add-item':          addItem(si, btn.dataset.type);                   break;
    case 'delete-item':       e.stopPropagation(); deleteItem(si, ii);         break;
    case 'move-item-up':      moveItem(si, ii, -1);                            break;
    case 'move-item-down':    moveItem(si, ii,  1);                            break;
    case 'add-sub-bullet':    addSubItem(si, ii);                              break;
    case 'delete-sub-item':   e.stopPropagation(); deleteSubItem(si, ii, bi);  break;
    case 'remove-skill-tag':    e.stopPropagation(); removeSkillTag(si, ii, bi);  break;
    case 'duplicate-section':   duplicateSection(si);                             break;
    case 'load-starter':        loadStarterCv();                                  break;
  }
}

// ─── Input delegation ─────────────────────────────────────────────────────
function onSectionsInput(e) {
  const t = e.target;
  const field = t.dataset.field;
  if (!field) return;
  const si = intOf(t.dataset.si);
  const ii = intOf(t.dataset.ii);
  const bi = intOf(t.dataset.bi);
  const sec = state.cv.sections[si];
  if (!sec) return;

  if (field === 'section-title') { sec.title = t.value; onChange(); return; }

  const item = sec.content[ii];
  if (!item) return;

  switch (field) {
    case 'item-title':    item.title    = t.value; break;
    case 'item-org':      item.org      = t.value; break;
    case 'item-date':     item.date     = t.value; break;
    case 'item-url':      item.url      = t.value; break;
    case 'item-text':     item.text     = t.value; break;
    case 'item-location': item.location = t.value; break;
    case 'item-grade':    item.grade    = t.value; break;
    case 'item-category': item.category = t.value; break;
    case 'sub-text':
      if (!isNaN(bi) && item.items?.[bi]) item.items[bi].text = t.value;
      break;
    case 'sub-date':
      if (!isNaN(bi) && item.items?.[bi]) item.items[bi].date = t.value;
      break;
  }
  onChange();
}

function onSectionsChange(e) {
  const t = e.target;
  if (t.dataset.field !== 'section-display') return;
  const si = intOf(t.dataset.si);
  if (!isNaN(si) && state.cv.sections[si]) {
    state.cv.sections[si].display = t.value;
    onChange();
  }
}

// ─── Skill tag keyboard handler ────────────────────────────────────────────
function onSectionsKeydown(e) {
  const t = e.target;
  if (t.dataset.field !== 'skill-input') return;
  const si = intOf(t.dataset.si);
  const ii = intOf(t.dataset.ii);
  const item = state.cv.sections[si]?.content[ii];
  if (!item || item.type !== 'skill-group') return;
  if (!item.skills) item.skills = [];

  if (e.key === 'Enter' || e.key === ',') {
    e.preventDefault();
    const raw = t.value.trim().replace(/,$/, '');
    if (!raw) return;
    raw.split(',').map(s => s.trim()).filter(Boolean).forEach(s => {
      if (!item.skills.includes(s)) item.skills.push(s);
    });
    t.value = '';
    renderSections();
    onChange();
    refocusSkillInput(si, ii);
  } else if (e.key === 'Backspace' && t.value === '') {
    if (item.skills.length) {
      item.skills.pop();
      renderSections();
      onChange();
      refocusSkillInput(si, ii);
    }
  }
}

function refocusSkillInput(si, ii) {
  setTimeout(() => {
    const inp = document.querySelector(`[data-field="skill-input"][data-si="${si}"][data-ii="${ii}"]`);
    if (inp) inp.focus();
  }, 10);
}

// ─── State mutations ───────────────────────────────────────────────────────
function addSectionWithType(sectionType) {
  const cfg = SECTION_TYPES[sectionType] || SECTION_TYPES.custom;
  state.cv.sections.push({
    id: uid(),
    title: cfg.defaultTitle,
    sectionType,
    display: cfg.defaultDisplay,
    collapsed: false,
    content: [],
  });
  renderSections();
  onChange();
  setTimeout(() => {
    const cards = $('sectionsList').querySelectorAll('.section-card');
    cards[cards.length - 1]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, 50);
}

function deleteSection(si) {
  state.cv.sections.splice(si, 1);
  renderSections();
  onChange();
}

function moveSection(si, dir) {
  const arr = state.cv.sections;
  const ni = si + dir;
  if (ni < 0 || ni >= arr.length) return;
  [arr[si], arr[ni]] = [arr[ni], arr[si]];
  renderSections();
  onChange();
}

function toggleSection(si) {
  const sec = state.cv.sections[si];
  if (sec) { sec.collapsed = !sec.collapsed; renderSections(); }
}

function duplicateSection(si) {
  const sec = deepClone(state.cv.sections[si]);
  sec.id = uid();
  sec.content = sec.content.map(item => ({
    ...item, id: uid(),
    items: (item.items || []).map(sub => ({ ...sub, id: uid() })),
  }));
  state.cv.sections.splice(si + 1, 0, sec);
  renderSections();
  onChange();
  toast('Section duplicated', 'info');
}

function newCv() {
  if ((state.cv.name || state.cv.sections.length > 0) &&
      !confirm('Start a new CV? Your current work will be cleared.')) return;
  state.cv = { name: '', subtitle: '', contact: '', sections: [] };
  $('cvName').value = '';
  $('cvSubtitle').value = '';
  $('cvContact').value = '';
  renderSections();
  forcePreview();
  saveToStorage();
  document.title = 'CV Maker';
  toast('New CV started', 'info');
}

function loadStarterCv() {
  loadCvData(deepClone(STARTER_CV));
  toast('Starter CV loaded — edit the fields to personalise it', 'success');
}

function printPreview() {
  const frame = $('previewFrame');
  if (frame && frame.contentWindow) {
    frame.contentWindow.focus();
    frame.contentWindow.print();
  }
}

function addItem(si, type) {
  const sec = state.cv.sections[si];
  if (!sec) return;
  const cfg = SECTION_TYPES[sec.sectionType] || SECTION_TYPES.custom;
  const itemType = type || cfg.addItemType || 'paragraph';
  const base = { id: uid(), type: itemType };

  switch (itemType) {
    case 'work-entry':      sec.content.push({ ...base, title: '', org: '', date: '', location: '', url: '', items: [] }); break;
    case 'education-entry': sec.content.push({ ...base, title: '', org: '', date: '', grade: '', url: '', items: [] }); break;
    case 'skill-group':     sec.content.push({ ...base, category: '', skills: [] }); break;
    case 'subsection':      sec.content.push({ ...base, title: '', org: '', date: '', url: '', items: [] }); break;
    case 'bullet':          sec.content.push({ ...base, text: '', date: '' }); break;
    default:                sec.content.push({ ...base, type: 'paragraph', text: '' }); break;
  }
  renderSections();
  onChange();
}

function deleteItem(si, ii) {
  state.cv.sections[si]?.content.splice(ii, 1);
  renderSections();
  onChange();
}

function moveItem(si, ii, dir) {
  const content = state.cv.sections[si]?.content;
  if (!content) return;
  const ni = ii + dir;
  if (ni < 0 || ni >= content.length) return;
  [content[ii], content[ni]] = [content[ni], content[ii]];
  renderSections();
  onChange();
}

function addSubItem(si, ii) {
  const item = state.cv.sections[si]?.content[ii];
  if (!item) return;
  if (!item.items) item.items = [];
  item.items.push({ id: uid(), type: 'bullet', text: '', date: '' });
  renderSections();
  onChange();
}

function deleteSubItem(si, ii, bi) {
  const item = state.cv.sections[si]?.content[ii];
  if (!item) return;
  item.items.splice(bi, 1);
  renderSections();
  onChange();
}

function removeSkillTag(si, ii, tagIndex) {
  const item = state.cv.sections[si]?.content[ii];
  if (!item || item.type !== 'skill-group') return;
  item.skills.splice(tagIndex, 1);
  renderSections();
  onChange();
}

// ─── Add-item dropdown ─────────────────────────────────────────────────────
function toggleAddMenu(btn, si) {
  const menu = btn.nextElementSibling;
  if (!menu) return;
  const wasOpen = menu.classList.contains('open');
  document.querySelectorAll('.add-item-menu.open').forEach(m => m.classList.remove('open'));
  if (!wasOpen) {
    menu.querySelectorAll('[data-action="add-item"]').forEach(b => { b.dataset.si = si; });
    menu.classList.add('open');
  }
}

// ─── Rendering ────────────────────────────────────────────────────────────
function renderSections() {
  const container = $('sectionsList');
  if (state.cv.sections.length === 0) {
    container.innerHTML = `
      <div class="empty-sections">
        <div class="empty-sections-icon">📄</div>
        <p class="empty-sections-headline">Start building your CV</p>
        <p>Add sections one by one, or jump in with a ready-made starter:</p>
        <div class="empty-actions">
          <button class="btn btn-accent" data-action="load-starter">⚡ Load Starter CV</button>
        </div>
        <p class="empty-actions-hint">or click <strong>+ Add Section</strong> above to build from scratch</p>
      </div>`;
    return;
  }
  container.innerHTML = state.cv.sections.map(renderSectionHTML).join('');
}

function renderSectionHTML(sec, si) {
  const first = si === 0;
  const last  = si === state.cv.sections.length - 1;
  const cfg   = SECTION_TYPES[sec.sectionType] || SECTION_TYPES.custom;
  const collapsed = !!sec.collapsed;

  const itemsHTML = collapsed ? '' : (
    sec.content.length === 0
      ? `<div class="empty-items">No items yet — click <em>${esc(cfg.addLabel)}</em> below.</div>`
      : sec.content.map((item, ii) => renderItemHTML(item, si, ii, sec.sectionType)).join('')
  );

  // Show display select only for custom sections
  const displayCtrl = (sec.sectionType === 'custom' || !sec.sectionType) ? `
    <select class="section-display-select" data-field="section-display" data-si="${si}"
      title="Display style" onclick="event.stopPropagation()">
      <option value="default" ${sec.display === 'default' ? 'selected' : ''}>Default</option>
      <option value="chips"   ${sec.display === 'chips'   ? 'selected' : ''}>Chips</option>
    </select>` : '';

  return `
<div class="section-card${collapsed ? ' collapsed' : ''}" data-si="${si}" data-section-type="${sec.sectionType || 'custom'}"
  style="--sec-color:${cfg.color};--sec-bg:${cfg.bg}">
  <div class="section-header" onclick="event.stopPropagation()">
    <span class="sec-type-stripe"></span>
    <input class="section-title-input" type="text"
      value="${esc(sec.title)}" placeholder="Section Title"
      data-field="section-title" data-si="${si}" />
    <span class="sec-type-pill">${cfg.icon} ${cfg.label}</span>
    ${displayCtrl}
    <div class="section-controls">
      <button class="btn-icon" data-action="move-section-up"   data-si="${si}" title="Move up"   ${first ? 'disabled' : ''}>↑</button>
      <button class="btn-icon" data-action="move-section-down" data-si="${si}" title="Move down" ${last  ? 'disabled' : ''}>↓</button>
      <button class="btn-icon" data-action="duplicate-section" data-si="${si}" title="Duplicate section">⧉</button>
      <button class="btn-icon danger" data-action="delete-section" data-si="${si}" title="Delete section">✕</button>
      <button class="btn-icon collapse-btn" data-action="toggle-section" data-si="${si}"
        title="${collapsed ? 'Expand' : 'Collapse'}">${collapsed ? '▾' : '▴'}</button>
    </div>
  </div>
  ${collapsed ? '' : `
  <div class="section-body">${itemsHTML}</div>
  <div class="add-item-wrap">${buildAddButton(sec, si)}</div>
  `}
</div>`;
}

function buildAddButton(sec, si) {
  const cfg = SECTION_TYPES[sec.sectionType] || SECTION_TYPES.custom;
  if (cfg.addItemType !== null) {
    return `<button class="btn btn-sm add-typed-btn" data-action="add-item"
      data-type="${cfg.addItemType}" data-si="${si}"
      style="--stp-color:${cfg.color}">
      + ${esc(cfg.addLabel)}
    </button>`;
  }
  return `
    <div class="add-item-trigger">
      <button class="btn btn-sm btn-accent" data-action="add-item-toggle" data-si="${si}">
        + Add Item
      </button>
      <div class="add-item-menu">
        <button class="menu-item" data-action="add-item" data-type="subsection" data-si="${si}">
          <span class="menu-item-icon">📋</span>
          <span><span class="menu-item-label">Entry</span><span class="menu-item-desc">Title + org + date + bullets</span></span>
        </button>
        <button class="menu-item" data-action="add-item" data-type="bullet" data-si="${si}">
          <span class="menu-item-icon">•</span>
          <span><span class="menu-item-label">Bullet Point</span><span class="menu-item-desc">Single line with optional date</span></span>
        </button>
        <button class="menu-item" data-action="add-item" data-type="paragraph" data-si="${si}">
          <span class="menu-item-icon">¶</span>
          <span><span class="menu-item-label">Paragraph</span><span class="menu-item-desc">Free-form text block</span></span>
        </button>
        <button class="menu-item" data-action="add-item" data-type="skill-group" data-si="${si}">
          <span class="menu-item-icon">🏷️</span>
          <span><span class="menu-item-label">Skill Group</span><span class="menu-item-desc">Tag chips with category</span></span>
        </button>
      </div>
    </div>`;
}

function renderItemHTML(item, si, ii, sectionType) {
  switch (item.type) {
    case 'work-entry':      return renderWorkEntryHTML(item, si, ii);
    case 'education-entry': return renderEducationEntryHTML(item, si, ii);
    case 'skill-group':     return renderSkillGroupHTML(item, si, ii);
    case 'subsection':      return renderSubsectionHTML(item, si, ii);
    case 'bullet':          return renderBulletHTML(item, si, ii);
    default:                return renderParagraphHTML(item, si, ii);
  }
}

function itemControls(si, ii) {
  const first = ii === 0;
  const last  = ii === state.cv.sections[si]?.content.length - 1;
  return `<div class="item-controls">
    <button class="btn-icon" data-action="move-item-up"   data-si="${si}" data-ii="${ii}" title="Move up"   ${first ? 'disabled' : ''}>↑</button>
    <button class="btn-icon" data-action="move-item-down" data-si="${si}" data-ii="${ii}" title="Move down" ${last  ? 'disabled' : ''}>↓</button>
    <button class="btn-icon danger" data-action="delete-item" data-si="${si}" data-ii="${ii}" title="Remove">✕</button>
  </div>`;
}

function subBulletsHTML(items, si, ii, placeholder) {
  return (items || []).map((sub, bi) => `
    <div class="sub-item-row">
      <span class="sub-item-dot"></span>
      <input class="input f-grow" type="text" placeholder="${esc(placeholder)}"
        value="${esc(sub.text)}"
        data-field="sub-text" data-si="${si}" data-ii="${ii}" data-bi="${bi}" />
      <input class="input f-date" type="text" placeholder="Date"
        value="${esc(sub.date || '')}"
        data-field="sub-date" data-si="${si}" data-ii="${ii}" data-bi="${bi}" />
      <button class="btn-icon danger" data-action="delete-sub-item"
        data-si="${si}" data-ii="${ii}" data-bi="${bi}" title="Remove">✕</button>
    </div>`).join('');
}

// ── Work Experience ────────────────────────────────────────────────────────
function renderWorkEntryHTML(item, si, ii) {
  const bullets = subBulletsHTML(item.items, si, ii, 'Responsibility or achievement…');
  return `
<div class="item-card item-card--work" data-si="${si}" data-ii="${ii}">
  <div class="item-header">
    <span class="type-badge badge-work">💼 Job</span>
    ${itemControls(si, ii)}
  </div>
  <div class="item-body">
    <div class="form-row">
      <div class="form-field f-grow2">
        <label class="field-label-sm">Job Title</label>
        <input class="input" type="text" placeholder="e.g. Senior Software Engineer"
          value="${esc(item.title)}" data-field="item-title" data-si="${si}" data-ii="${ii}" />
      </div>
      <div class="form-field f-grow2">
        <label class="field-label-sm">Company</label>
        <input class="input" type="text" placeholder="e.g. Acme Corp"
          value="${esc(item.org || '')}" data-field="item-org" data-si="${si}" data-ii="${ii}" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-field f-grow">
        <label class="field-label-sm">Period</label>
        <input class="input" type="text" placeholder="e.g. Jan 2022 – Present"
          value="${esc(item.date || '')}" data-field="item-date" data-si="${si}" data-ii="${ii}" />
      </div>
      <div class="form-field f-grow">
        <label class="field-label-sm">Location <span class="opt-hint">(optional)</span></label>
        <input class="input" type="text" placeholder="e.g. London, UK"
          value="${esc(item.location || '')}" data-field="item-location" data-si="${si}" data-ii="${ii}" />
      </div>
      <div class="form-field f-url-sm">
        <label class="field-label-sm">URL <span class="opt-hint">(optional)</span></label>
        <input class="input" type="text" placeholder="https://…"
          value="${esc(item.url || '')}" data-field="item-url" data-si="${si}" data-ii="${ii}" />
      </div>
    </div>
  </div>
  <div class="sub-items-wrap">
    <div class="sub-items-label">Responsibilities / Achievements</div>
    <div class="sub-items-list">${bullets}</div>
    <div class="add-sub-row">
      <button class="btn btn-xs btn-ghost-light" data-action="add-sub-bullet" data-si="${si}" data-ii="${ii}">
        + Add bullet
      </button>
    </div>
  </div>
</div>`;
}

// ── Education ──────────────────────────────────────────────────────────────
function renderEducationEntryHTML(item, si, ii) {
  const notes = subBulletsHTML(item.items, si, ii, 'Course, module or relevant note…');
  const hasNotes = (item.items || []).length > 0;
  return `
<div class="item-card item-card--edu" data-si="${si}" data-ii="${ii}">
  <div class="item-header">
    <span class="type-badge badge-edu">🎓 Entry</span>
    ${itemControls(si, ii)}
  </div>
  <div class="item-body">
    <div class="form-row">
      <div class="form-field f-grow2">
        <label class="field-label-sm">Degree / Qualification</label>
        <input class="input" type="text" placeholder="e.g. BSc Computer Science"
          value="${esc(item.title)}" data-field="item-title" data-si="${si}" data-ii="${ii}" />
      </div>
      <div class="form-field f-grow2">
        <label class="field-label-sm">Institution</label>
        <input class="input" type="text" placeholder="e.g. University of Example"
          value="${esc(item.org || '')}" data-field="item-org" data-si="${si}" data-ii="${ii}" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-field f-grow">
        <label class="field-label-sm">Year / Period</label>
        <input class="input" type="text" placeholder="e.g. 2018 – 2022"
          value="${esc(item.date || '')}" data-field="item-date" data-si="${si}" data-ii="${ii}" />
      </div>
      <div class="form-field f-grow">
        <label class="field-label-sm">Grade / Result <span class="opt-hint">(optional)</span></label>
        <input class="input" type="text" placeholder="e.g. First Class, 3.9 GPA"
          value="${esc(item.grade || '')}" data-field="item-grade" data-si="${si}" data-ii="${ii}" />
      </div>
      <div class="form-field f-url-sm">
        <label class="field-label-sm">URL <span class="opt-hint">(optional)</span></label>
        <input class="input" type="text" placeholder="https://…"
          value="${esc(item.url || '')}" data-field="item-url" data-si="${si}" data-ii="${ii}" />
      </div>
    </div>
  </div>
  <div class="sub-items-wrap">
    <div class="sub-items-label">Notes / Courses <span class="opt-hint">(optional)</span></div>
    <div class="sub-items-list">${notes}</div>
    <div class="add-sub-row">
      <button class="btn btn-xs btn-ghost-light" data-action="add-sub-bullet" data-si="${si}" data-ii="${ii}">
        + Add note
      </button>
    </div>
  </div>
</div>`;
}

// ── Skills Group ───────────────────────────────────────────────────────────
function renderSkillGroupHTML(item, si, ii) {
  const skills = item.skills || [];
  const tagsHTML = skills.map((s, ti) => `
    <span class="skill-tag">
      ${esc(s)}
      <button class="skill-tag-rm" data-action="remove-skill-tag"
        data-si="${si}" data-ii="${ii}" data-bi="${ti}" title="Remove">×</button>
    </span>`).join('');

  return `
<div class="item-card item-card--skills" data-si="${si}" data-ii="${ii}">
  <div class="item-header">
    <span class="type-badge badge-skills">🏷️ Group</span>
    ${itemControls(si, ii)}
  </div>
  <div class="item-body">
    <div class="form-field">
      <label class="field-label-sm">Category <span class="opt-hint">(optional)</span></label>
      <input class="input" type="text" placeholder="e.g. Programming Languages, Frameworks, Tools…"
        value="${esc(item.category || '')}" data-field="item-category" data-si="${si}" data-ii="${ii}" />
    </div>
    <div class="form-field">
      <label class="field-label-sm">
        Skills
        <span class="opt-hint">— type and press <kbd>Enter</kbd> or <kbd>,</kbd> to add</span>
      </label>
      <div class="skill-tags-wrap">
        ${tagsHTML}
        <input class="skill-tags-input" type="text"
          placeholder="${skills.length === 0 ? 'Type a skill, press Enter…' : 'Add more…'}"
          data-field="skill-input" data-si="${si}" data-ii="${ii}" />
      </div>
    </div>
  </div>
</div>`;
}

// ── Generic subsection ─────────────────────────────────────────────────────
function renderSubsectionHTML(item, si, ii) {
  const bullets = subBulletsHTML(item.items, si, ii, 'Bullet text…  supports **bold**, *italic*, [link](url)');
  return `
<div class="item-card" data-si="${si}" data-ii="${ii}">
  <div class="item-header">
    <span class="type-badge badge-sub">📋 Entry</span>
    ${itemControls(si, ii)}
  </div>
  <div class="item-body">
    <div class="form-row">
      <input class="input f-grow2" type="text" placeholder="Title"
        value="${esc(item.title)}" data-field="item-title" data-si="${si}" data-ii="${ii}" />
      <input class="input f-grow2" type="text" placeholder="Organisation"
        value="${esc(item.org || '')}" data-field="item-org" data-si="${si}" data-ii="${ii}" />
      <input class="input f-date" type="text" placeholder="Date"
        value="${esc(item.date || '')}" data-field="item-date" data-si="${si}" data-ii="${ii}" />
    </div>
    <div class="form-row">
      <input class="input f-url" type="text" placeholder="URL (optional)"
        value="${esc(item.url || '')}" data-field="item-url" data-si="${si}" data-ii="${ii}" />
    </div>
  </div>
  <div class="sub-items-wrap">
    <div class="sub-items-label">Bullets</div>
    <div class="sub-items-list">${bullets}</div>
    <div class="add-sub-row">
      <button class="btn btn-xs btn-ghost-light"
        data-action="add-sub-bullet" data-si="${si}" data-ii="${ii}">
        + Add bullet
      </button>
    </div>
  </div>
</div>`;
}

function renderBulletHTML(item, si, ii) {
  return `
<div class="item-card" data-si="${si}" data-ii="${ii}">
  <div class="item-header">
    <span class="type-badge badge-bullet">• Bullet</span>
    ${itemControls(si, ii)}
  </div>
  <div class="item-body">
    <div class="form-row">
      <input class="input f-grow3" type="text"
        placeholder="Text…  supports **bold**, *italic*, [link](url)"
        value="${esc(item.text)}"
        data-field="item-text" data-si="${si}" data-ii="${ii}" />
      <input class="input f-date" type="text" placeholder="Date (opt.)"
        value="${esc(item.date || '')}"
        data-field="item-date" data-si="${si}" data-ii="${ii}" />
    </div>
  </div>
</div>`;
}

function renderParagraphHTML(item, si, ii) {
  return `
<div class="item-card" data-si="${si}" data-ii="${ii}">
  <div class="item-header">
    <span class="type-badge badge-para">¶ Text</span>
    ${itemControls(si, ii)}
  </div>
  <div class="item-body">
    <textarea class="textarea f-grow"
      placeholder="Free-form text…  supports **bold**, *italic*, [link](url)"
      data-field="item-text" data-si="${si}" data-ii="${ii}"
    >${esc(item.text)}</textarea>
  </div>
</div>`;
}

// ─── Build API payload ─────────────────────────────────────────────────────
// Transforms frontend-specific types into backend-compatible types
function buildApiPayload() {
  const cv = deepClone(state.cv);
  cv.sections.forEach(sec => {
    delete sec.sectionType;
    delete sec.collapsed;
    const out = [];
    for (const item of sec.content) {
      if (item.type === 'work-entry') {
        const locPart = (item.location || '').trim();
        const org = locPart
          ? `${(item.org || '').trim()}${item.org ? ' · ' : ''}${locPart}`
          : (item.org || '').trim();
        out.push({ type: 'subsection', title: item.title || '', org, date: item.date || '',
                   url: item.url || '', items: item.items || [] });
      } else if (item.type === 'education-entry') {
        const gradePart = (item.grade || '').trim();
        const title = gradePart ? `${item.title || ''} (${gradePart})` : (item.title || '');
        out.push({ type: 'subsection', title, org: item.org || '', date: item.date || '',
                   url: item.url || '', items: item.items || [] });
      } else if (item.type === 'skill-group') {
        const skills = item.skills || [];
        const cat = (item.category || '').trim();
        if (cat) {
          out.push({ type: 'subsection', title: cat, org: '', date: '', url: '',
                     items: skills.map(s => ({ type: 'bullet', text: s, date: '' })) });
        } else {
          skills.forEach(s => out.push({ type: 'bullet', text: s, date: '' }));
        }
      } else {
        out.push(item);
      }
    }
    sec.content = out;
  });
  return cv;
}

function deepClone(obj) { return JSON.parse(JSON.stringify(obj)); }

// ─── Preview ──────────────────────────────────────────────────────────────
function schedulePreview(delay = 650) {
  clearTimeout(state.previewTimer);
  setStatus('updating', '● Updating…');
  state.previewTimer = setTimeout(forcePreview, delay);
}

async function forcePreview() {
  clearTimeout(state.previewTimer);
  $('previewFrame').classList.add('loading');
  try {
    const payload = buildApiPayload();
    const res = await fetch('/api/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cv: payload, template: state.template }),
    });
    if (!res.ok) throw new Error(await res.text());
    $('previewFrame').srcdoc = await res.text();
    setStatus('', '');
  } catch (err) {
    setStatus('error', '⚠ Preview failed');
    console.error('Preview error:', err);
  } finally {
    $('previewFrame').classList.remove('loading');
  }
}

function setStatus(cls, text) {
  const s = $('previewStatus');
  s.className = 'preview-status' + (cls ? ' ' + cls : '');
  s.textContent = text;
}

// ─── Export ───────────────────────────────────────────────────────────────
async function exportFile(format) {
  const ids = { pdf: 'exportPdfBtn', docx: 'exportDocxBtn', markdown: 'exportMdBtn' };
  const btn = $(ids[format]);
  const orig = btn.innerHTML;
  btn.disabled = true; btn.innerHTML = '⏳';
  try {
    const payload = buildApiPayload();
    const res = await fetch(`/api/export/${format}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cv: payload, template: state.template }),
    });
    if (!res.ok) throw new Error(await res.text());
    const blob  = await res.blob();
    const cd    = res.headers.get('Content-Disposition') || '';
    const match = cd.match(/filename[^;=\n]*=(['"]?)([^'";\n]+)\1/);
    const fname = match ? match[2] : `cv.${format === 'markdown' ? 'md' : format}`;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = fname; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
    toast(`Downloaded ${fname}`, 'success');
  } catch (err) {
    toast(`Export failed: ${err.message}`, 'error');
    console.error('Export error:', err);
  } finally {
    btn.disabled = false; btn.innerHTML = orig;
  }
}

// ─── Import ───────────────────────────────────────────────────────────────
async function importMarkdownFile(file) {
  const fd = new FormData();
  fd.append('file', file);
  try {
    const res = await fetch('/api/import/markdown', { method: 'POST', body: fd });
    if (!res.ok) throw new Error(await res.text());
    loadCvData(await res.json());
    closeModal();
    toast('CV imported successfully', 'success');
  } catch (err) {
    toast(`Import failed: ${err.message}`, 'error');
    console.error('Import error:', err);
  }
}

function loadCvData(data) {
  const stampIds = (sections) => (sections || []).map(sec => {
    const guessed = sec.sectionType || guessTypeFromSection(sec);
    return {
      ...sec,
      id: uid(),
      sectionType: guessed,
      collapsed: false,
      content: (sec.content || []).map(item => ({
        ...item,
        id: uid(),
        type: upgradeItemType(item, guessed),
        items: (item.items || []).map(si => ({ ...si, id: uid() })),
      })),
    };
  });

  state.cv = {
    name: data.name || '', subtitle: data.subtitle || '', contact: data.contact || '',
    sections: stampIds(data.sections),
  };

  $('cvName').value     = state.cv.name;
  $('cvSubtitle').value = state.cv.subtitle;
  $('cvContact').value  = state.cv.contact;

  renderSections();
  forcePreview();
  saveToStorage();
}

function upgradeItemType(item, sectionType) {
  if (item.type === 'subsection') {
    if (sectionType === 'work')      return 'work-entry';
    if (sectionType === 'education') return 'education-entry';
  }
  return item.type;
}

function guessTypeFromSection(sec) {
  const t = (sec.title || '').toLowerCase();
  if (/work|experience|employ|career|job|position/i.test(t))       return 'work';
  if (/education|study|academic|degree|qualif|school|university/i.test(t)) return 'education';
  if (/skill|technical|competenc|tool|technolog/i.test(t))         return 'skills';
  if (/profile|summary|about|objective|overview/i.test(t))         return 'summary';
  if (/language/i.test(t))                                          return 'languages';
  return 'custom';
}

function closeModal() {
  $('importModal').hidden = true;
  $('fileInput').value = '';
}

// ─── Autosave ──────────────────────────────────────────────────────────────
const STORAGE_KEY = 'cvmaker_v3';

function scheduleAutosave() {
  clearTimeout(state.autosaveTimer);
  state.autosaveTimer = setTimeout(saveToStorage, 1500);
}

function saveToStorage() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ cv: state.cv, template: state.template }));
    flashAutosave();
  } catch (e) { console.warn('Autosave failed:', e); }
}

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    if (saved.cv) {
      state.cv = saved.cv;
      state.cv.sections = (state.cv.sections || []).map(sec => ({
        ...sec,
        id: sec.id || uid(),
        collapsed: sec.collapsed || false,
        content: (sec.content || []).map(item => ({
          ...item,
          id: item.id || uid(),
          items: (item.items || []).map(si => ({ ...si, id: si.id || uid() })),
        })),
      }));
      $('cvName').value     = state.cv.name || '';
      $('cvSubtitle').value = state.cv.subtitle || '';
      $('cvContact').value  = state.cv.contact || '';
    }
    if (saved.template) {
      state.template = saved.template;
      const sel = $('templateSelect');
      if (sel) sel.value = state.template;
    }
    if (state.cv.name || state.cv.sections.length > 0) {
      toast('Session restored', 'info');
    }
  } catch (e) { console.warn('Could not restore session:', e); }
}

function flashAutosave() {
  const el = $('autosaveStatus');
  if (!el) return;
  el.textContent = '✓ Saved';
  el.className = 'autosave-status show';
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.className = 'autosave-status'; }, 2000);
}

// ─── Resize handle ─────────────────────────────────────────────────────────
function initResize() {
  const handle    = $('resizeHandle');
  const workspace = document.querySelector('.workspace');
  let dragging = false, startX, startW;

  handle.addEventListener('mousedown', e => {
    dragging = true;
    startX   = e.clientX;
    startW   = document.querySelector('.editor-panel').getBoundingClientRect().width;
    handle.classList.add('dragging');
    document.body.style.cursor     = 'col-resize';
    document.body.style.userSelect = 'none';
    $('previewFrame').style.pointerEvents = 'none';
  });
  document.addEventListener('mousemove', e => {
    if (!dragging) return;
    const totalW = workspace.getBoundingClientRect().width;
    const newW   = Math.min(Math.max(280, startW + (e.clientX - startX)), totalW - 280);
    document.documentElement.style.setProperty('--editor-w', newW + 'px');
  });
  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    handle.classList.remove('dragging');
    document.body.style.cursor     = '';
    document.body.style.userSelect = '';
    $('previewFrame').style.pointerEvents = '';
  });
}

// ─── Toast ────────────────────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const t = el('div', `toast ${type}`, msg);
  $('toastContainer').appendChild(t);
  setTimeout(() => { t.classList.add('removing'); setTimeout(() => t.remove(), 220); }, 3000);
}

// ─── Utilities ────────────────────────────────────────────────────────────
function esc(str) {
  return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function intOf(val) { const n = parseInt(val, 10); return isNaN(n) ? undefined : n; }

// ─── Boot ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
