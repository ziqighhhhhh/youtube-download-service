function fmtDate(s) { if(!s) return '-'; const d=new Date(s); return d.toLocaleDateString('zh-CN'); }
