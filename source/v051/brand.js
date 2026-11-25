/* PiShield Sentinel presentation only. Upstream engine and license files untouched. */
(()=>{
  const logo=new URL('/admin/img/pishield-sentinel.svg',location.origin).href;
  const brand=s=>s.replace(/\bPi-hole\b(?![.\w-])/gi,'PiShield');
  function apply(){
    document.title=brand(document.title);
    for(const a of document.querySelectorAll('a[href*="pi-hole.net/donate"], a[href*="pi-hole.net/donation"], a[href*="github.com/sponsors/pi-hole"], a[href*="patreon.com/pihole"]')){
      const li=a.closest('li'); (li||a).classList.add('ps-hide-donation');
    }
    for(const h of document.querySelectorAll('.sidebar-menu > li.header'))if(/^donate\s*$/i.test(h.textContent.trim()))h.classList.add('ps-hide-donation');
    for(const im of document.querySelectorAll('img'))if(/(?:^|\/)(?:logo(?:-dark|-light)?|pihole)(?:\.svg|\.png)(?:\?|$)/i.test(im.getAttribute('src')||'')||/pi-hole logo/i.test(im.alt)){if(im.src!==logo)im.src=logo;im.alt='PiShield logo';}
    for(const link of document.querySelectorAll('link[rel*="icon"]'))if(link.href!==logo)link.href=logo;
    for(const root of document.querySelectorAll('.main-header,.main-sidebar,.main-footer,.login-box,.login-logo,.content-header,.ps-native-banner,.content-wrapper h1,.content-wrapper h2,.content-wrapper h3,.content-wrapper label,.content-wrapper button')){
      const walk=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let n;
      while(n=walk.nextNode())if(!n.parentElement.closest('script,style,pre,code,textarea,input,select,option,table')){const v=brand(n.nodeValue);if(v!==n.nodeValue)n.nodeValue=v;}
    }
    for(const a of document.querySelectorAll('.main-header a,.main-sidebar a,.main-footer a,.login-box a'))if(/^\s*(donate|support pi-hole)\s*$/i.test(a.textContent))a.classList.add('ps-hide-donation');
  }
  function start(){apply();let pending=false;new MutationObserver(()=>{if(!pending){pending=true;requestAnimationFrame(()=>{pending=false;apply();});}}).observe(document.body,{childList:true,subtree:true,characterData:true});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
