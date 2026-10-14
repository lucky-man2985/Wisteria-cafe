/* Analytics is disabled in this comparison build. */
(()=>{
 window.WISTERIA_ANALYTICS={enabled:false};
 document.querySelectorAll('[data-analytics-status]').forEach(node=>{
  node.textContent='Статистика отключена в версии для сравнения';
 });
 document.querySelectorAll('[data-analytics-accept],[data-analytics-deny]').forEach(node=>{
  node.disabled=true;node.hidden=true;
 });
})();
