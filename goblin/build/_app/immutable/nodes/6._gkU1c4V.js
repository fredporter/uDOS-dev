const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["../chunks/CvxpRb0P.js","../chunks/CHR-kdpd.js","../chunks/BSqd-cP5.js","../chunks/mPlcS5K-.js","../chunks/XUVl8-cR.js","../chunks/D9PjKXvN.js","../chunks/PPVm8Dsz.js","../chunks/B_OjSlQX.js","../chunks/DTxikevS.js","../chunks/mR0PQqwn.js","../chunks/BvgltCUz.js","../chunks/CCCdPpZ7.js","../chunks/BYKvG165.js","../chunks/Ds4DHZit.js"])))=>i.map(i=>d[i]);
import{_ as __vitePreload}from"../chunks/PPVm8Dsz.js";import{e as from_svg,a as append,f as from_html,c as comment}from"../chunks/DJBiFi07.js";import{o as onMount,a as onDestroy}from"../chunks/BzR243_0.js";import{p as push,z as user_effect,g as get,A as user_derived,$ as $document,c as child,f as first_child,r as reset,s as sibling,b as pop,t as template_effect,J as tick,x as state,y as proxy,d as set,U as next,bk as remove_textarea_child}from"../chunks/C1tFvGX1.js";import{s as set_text}from"../chunks/DKaewyD_.js";import{i as if_block}from"../chunks/Do373t0H.js";import{h as html}from"../chunks/DUCZTkoZ.js";import{d as delegate,e as event}from"../chunks/CciwqBTl.js";import{e as each,i as index,a as set_class}from"../chunks/DSzgAFR7.js";import{s as set_style}from"../chunks/BjDMEt5v.js";import{b as bind_value}from"../chunks/D3ueW3xG.js";import{p as prop,u as update_prop,s as setup_stores,a as store_get}from"../chunks/fGSS8G2I.js";import"../chunks/BRxpCUyw.js";import{F as FileSidebar}from"../chunks/BGC3Juze.js";import{invoke}from"../chunks/mPlcS5K-.js";import{listen}from"../chunks/BSqd-cP5.js";import{open}from"../chunks/XUVl8-cR.js";import{p as page}from"../chunks/nUADG8L5.js";import{g as getStateForMode,a as getLastFile,u as updateModeState}from"../chunks/BQcBsHRT.js";/* empty css                */import{g as getStyleState}from"../chunks/do9l82nx.js";var root$2=from_svg('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-5 w-5"><path fill-rule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clip-rule="evenodd"></path></svg>');function Arrow(h){var u=root$2();append(h,u)}const ssr=!1,prerender=!1,_page$1=Object.freeze(Object.defineProperty({__proto__:null,prerender,ssr},Symbol.toStringTag,{value:"Module"})),codeEval=()=>{const codeblocks=document.querySelectorAll("pre");for(const block of codeblocks){const input=block.firstChild;if(input instanceof HTMLElement){const lang=getLang(input);if(lang==="js"||lang==="ts"){block.classList.add("cursor-default","hover:shadow-md","hover:scale-[100.2%]","transition","active:scale-[99.8%]","active:shadow-none","group","flex","flex-col","gap-2");let code=input.textContent??"";const onClick=async e=>{if(e.stopImmediatePropagation(),lang==="ts"){const{default:h}=await __vitePreload(async()=>{const{default:u}=await import("../chunks/CvxpRb0P.js");return{default:u}},__vite__mapDeps([0,1]),import.meta.url);code=h(code)}const output=block.lastChild;if(output&&input!==output)block.removeChild(output);else{let result="",errorExists=!1;try{code&&(result=eval(code),typeof result=="string"&&(result=`"${result}"`),result===void 0&&(result="undefined"))}catch(h){errorExists=!0,result=String(h)}const newOutput=document.createElement("code");newOutput.classList.add("pt-2","border-t","border-gray-600"),errorExists&&newOutput.classList.add("text-rose-400"),newOutput.textContent=result,block.appendChild(newOutput)}};block.removeEventListener("click",onClick),block.addEventListener("click",onClick)}}}},getLang=h=>{for(const u of h.className.split(" "))if(u.startsWith("language-"))return u.substring(9);return""};var root_2$1=from_html("<section><!></section>"),root_3$1=from_html('<div class="sticky bottom-3 flex items-center justify-center font-sans tabular-nums"><div class="flex items-center justify-center gap-2 rounded-xl bg-white/40 p-1 backdrop-blur-lg dark:bg-gray-950/40"><button title="Previous Slide" class="button button-s rotate-180"><!></button> <div class="text-sm"> </div> <button title="Next Slide" class="button button-s"><!></button></div></div>'),root$1=from_html('<div class="flex h-full flex-col"><article class="flex grow flex-col justify-center p-8"></article> <!></div>');function Slides(h,u){push(u,!0);let L=prop(u,"html",3,""),v=prop(u,"currentSlide",15,0);const P=()=>L().split("<hr>");let r=user_derived(()=>P().length);user_effect(()=>{v()>=get(r)&&v(get(r)-1)});const _=async i=>{i==="next"&&v()<get(r)-1?update_prop(v):i==="previous"&&v()&&update_prop(v,-1),await tick(),codeEval()},l=({key:i})=>{u.viewMode&&(i==="ArrowRight"||i===" "?_("next"):i==="ArrowLeft"&&_("previous"))};var m=root$1();event("keydown",$document,l);var S=child(m);each(S,21,P,index,(i,x,b)=>{var n=comment(),E=first_child(n);{var A=w=>{var o=root_2$1(),y=child(o);html(y,()=>get(x)),reset(o),append(w,o)};if_block(E,w=>{b===v()&&w(A)})}append(i,n)}),reset(S);var F=sibling(S,2);{var d=i=>{var x=root_3$1(),b=child(x),n=child(b);n.__click=()=>_("previous");var E=child(n);Arrow(E),reset(n);var A=sibling(n,2),w=child(A);reset(A);var o=sibling(A,2);o.__click=()=>_("next");var y=child(o);Arrow(y),reset(o),reset(b),reset(x),template_effect(()=>{n.disabled=!v(),set_text(w,`${v()+1} / ${get(r)??""}`),o.disabled=v()>=get(r)-1}),append(i,x)};if_block(F,i=>{get(r)>1&&i(d)})}reset(m),append(h,m),pop()}delegate(["click"]);const printCss=`body {
	margin: 1rem;
	color: #1f2937;
	font-size: small;
	font-family: system-ui, sans-serif;
}
h1,
h2,
h3,
h4,
h5,
h6 {
	color: #030712;
}
a,
a:visited,
a:hover,
a:active {
	color: #1f2937;
	font-weight: 600;
	text-underline-offset: 2px;
}
pre {
	border: 0.5px solid #e5e7eb;
	border-radius: 0.5rem;
	padding: 1rem;
	font-family: monospace;
}
p,
li {
	line-height: 24px;
}
p code::before {
	content: "\`";
}
p code::after {
	content: "\`";
}
blockquote {
	font-style: italic;
	font-weight: bold;
}
blockquote p::before {
	content: '"';
}
blockquote p::after {
	content: '"';
}
img {
	border-radius: 1rem;
	width: 100%;
}
table {
	margin-bottom: 1rem;
	border-collapse: collapse;
	width: 100%;
}
th,
td {
	border-bottom: 1px solid #d1d5db;
	padding: 0.5rem;
	text-align: left;
}
th:first-child,
td:first-child {
	padding: 0.5rem 0.5rem 0.5rem 0rem;
}
th:last-child,
td:last-child {
	padding: 0.5rem 0rem 0.5rem 0.5rem;
}
hr {
	border: 0.5px solid #e5e7eb;
}
`,gettingStarted=`# Getting Started

Write content in [markdown](https://www.markdownguide.org/cheat-sheet/#basic-syntax)!

Typo is open source and distributed under the MIT License. Leave feedback, contribute, or fork the project on [GitHub](https://github.com/rossrobino/typo).

---

## View

Content can be viewed as a **document** or **slideshow**, separate slides with an \`<hr>\` tag (\`---\`).

## Format

Automatically format content with [Prettier](https://prettier.io) using the format button or <kbd>CTRL + S</kbd>.

## Save

When a file is opened or saved, all future changes are saved automatically.

Files are stored directly on the local computer, not in an online storage system.

---

## Execute Code

JavaScript and TypeScript code blocks can be executed in the browser by clicking the block.

\`\`\`\`ts
// add a TypeScript code block (\`\`\`ts)

function clickHere(): string {
	return "Hello world!";
}

clickHere();
\`\`\`\`

---

## Keyboard Shortcuts

| Function         | Key Combination                 |
| ---------------- | ------------------------------- |
| Focus text area  | <kbd>i</kbd>                    |
| Toggle view mode | <kbd>ESC</kbd>                  |
| Format           | <kbd>CTRL</kbd> + <kbd>S</kbd>  |
| Anchor           | <kbd>CTRL</kbd> + <kbd>\\[</kbd> |
| Image            | <kbd>CTRL</kbd> + <kbd>\\]</kbd> |
| Table            | <kbd>CTRL</kbd> + <kbd>\\\\</kbd> |
`;var root_1=from_html('<div class="w-1/2 flex flex-col min-h-0 overflow-hidden"><!></div>'),root_3=from_svg('<path d="M10 12.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z"></path><path fill-rule="evenodd" d="M.664 10.59a1.651 1.651 0 010-1.186A10.004 10.004 0 0110 3c4.257 0 7.893 2.66 9.336 6.41.147.381.146.804 0 1.186A10.004 10.004 0 0110 17c-4.257 0-7.893-2.66-9.336-6.41zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"></path>',1),root_4=from_svg('<path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"></path>'),root_5=from_html('<drab-editor><textarea class="h-full w-full resize-none bg-transparent p-4 font-mono text-base leading-normal text-gray-900 outline-none dark:text-gray-50" spellcheck="false"></textarea> <div class="flex flex-wrap gap-0.5 border-t p-0.5"><button data-trigger="" class="button" title="Heading" data-value="#" data-type="line">H</button> <button data-trigger="" class="button" title="Unordered List" data-value="-" data-type="line">•</button> <button data-trigger="" class="button" title="Ordered List" data-value="1." data-type="line">1.</button> <button data-trigger="" class="button" title="Task" data-value="- [ ]" data-type="line">☐</button> <button data-trigger="" class="button" title="Blockquote" data-value=">" data-type="line">❝</button> <button data-trigger="" class="button" title="Code Block" data-value="```" data-type="block"></button> <button data-trigger="" class="button" title="Divider" data-value="---" data-type="block">―</button> <button data-trigger="" class="button" title="Bold" data-value="**" data-type="inline"><strong>B</strong></button> <button data-trigger="" class="button" title="Italic" data-value="_" data-type="inline"><em>I</em></button> <button data-trigger="" class="button" title="Strikethrough" data-value="~~" data-type="inline"><s>S</s></button> <button data-trigger="" class="button" title="Link" data-value="[]()" data-type="inline">🔗</button></div></drab-editor>',2),root_6=from_html('<div><div class="text-gray-500">Loading editor...</div></div>'),root_2=from_html('<div class="flex flex-col min-h-0 overflow-hidden"><div class="flex flex-wrap gap-1 border-b border-gray-300 dark:border-gray-800 p-2 bg-gray-100 dark:bg-gray-900"><button title="Toggle File Picker (⌘B)"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-5 w-5"><path d="M4.75 3A1.75 1.75 0 003 4.75v2.752l.104-.002h13.792c.035 0 .07 0 .104.002V6.75A1.75 1.75 0 0015.25 5h-3.836a.25.25 0 01-.177-.073L9.823 3.513A1.75 1.75 0 008.586 3H4.75zM3.104 9a1.75 1.75 0 00-1.673 2.265l1.385 4.5A1.75 1.75 0 004.488 17h11.023a1.75 1.75 0 001.673-1.235l1.384-4.5A1.75 1.75 0 0016.896 9H3.104z"></path></svg> <span class="hidden lg:inline">Files</span></button> <button title="Toggle Edit/View Mode"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-5 w-5"><!></svg> <span class="hidden lg:inline"> </span></button> <div class="w-px h-6 bg-gray-300 dark:bg-gray-700"></div> <button title="Change Background Color" class="button"><div></div> <span class="hidden lg:inline">Color</span></button> <button title="Open File... (⌘O)" class="button"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-5 w-5"><path d="M4.75 3A1.75 1.75 0 003 4.75v2.752l.104-.002h13.792c.035 0 .07 0 .104.002V6.75A1.75 1.75 0 0015.25 5h-3.836a.25.25 0 01-.177-.073L9.823 3.513A1.75 1.75 0 008.586 3H4.75zM3.104 9a1.75 1.75 0 00-1.673 2.265l1.385 4.5A1.75 1.75 0 004.488 17h11.023a1.75 1.75 0 001.673-1.235l1.384-4.5A1.75 1.75 0 0016.896 9H3.104z"></path></svg> <span class="hidden lg:inline">Open</span></button> <button title="Save As... (⌘⇧S)" class="button"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-5 w-5"><path fill-rule="evenodd" d="M2 4.75C2 3.784 2.784 3 3.75 3h4.836c.464 0 .909.184 1.237.513l1.414 1.414a.25.25 0 00.177.073h4.836c.966 0 1.75.784 1.75 1.75v8.5A1.75 1.75 0 0116.25 17H3.75A1.75 1.75 0 012 15.25V4.75zm8.75 4a.75.75 0 00-1.5 0v2.546l-.943-1.048a.75.75 0 10-1.114 1.004l2.25 2.5a.75.75 0 001.114 0l2.25-2.5a.75.75 0 10-1.114-1.004l-.943 1.048V8.75z" clip-rule="evenodd"></path></svg> <span class="hidden lg:inline">Save As</span></button> <button title="Copy Markdown" class="button"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-5 w-5"><path d="M7 3.5A1.5 1.5 0 018.5 2h3.879a1.5 1.5 0 011.06.44l3.122 3.12A1.5 1.5 0 0117 6.622V12.5a1.5 1.5 0 01-1.5 1.5h-1v-3.379a3 3 0 00-.879-2.121L10.5 5.379A3 3 0 008.379 4.5H7v-1z"></path><path d="M4.5 6A1.5 1.5 0 003 7.5v9A1.5 1.5 0 004.5 18h7a1.5 1.5 0 001.5-1.5v-5.879a1.5 1.5 0 00-.44-1.06L9.44 6.439A1.5 1.5 0 008.378 6H4.5z"></path></svg> <span class="hidden lg:inline"> </span></button> <button title="Copy HTML" class="button"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-5 w-5"><path fill-rule="evenodd" d="M4.5 2A2.5 2.5 0 002 4.5v11A2.5 2.5 0 004.5 18h11a2.5 2.5 0 002.5-2.5v-11A2.5 2.5 0 0015.5 2h-11zm3.544 1.5a.5.5 0 01.353.146l1.5 1.5a.5.5 0 010 .708l-1.5 1.5a.5.5 0 01-.708-.708l.647-.646H5a.5.5 0 010-1h3.336l-.647-.646a.5.5 0 01.355-.854zm4.912 0a.5.5 0 01.353.854l-.647.646H16a.5.5 0 010 1h-3.336l.647.646a.5.5 0 01-.708.708l-1.5-1.5a.5.5 0 010-.708l1.5-1.5a.5.5 0 01.353-.146zM5.5 9A.5.5 0 015 9.5v6a.5.5 0 00.5.5h9a.5.5 0 00.5-.5v-6A.5.5 0 0014.5 9h-9z" clip-rule="evenodd"></path></svg> <span class="hidden lg:inline"> </span></button> <button title="Print" class="button"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-5 w-5"><path fill-rule="evenodd" d="M5 2.75C5 1.784 5.784 1 6.75 1h6.5c.966 0 1.75.784 1.75 1.75v3.552c.377.046.752.097 1.126.153A2.212 2.212 0 0118 8.653v4.097A2.25 2.25 0 0115.75 15h-.241l.305 1.984A1.75 1.75 0 0114.084 19H5.915a1.75 1.75 0 01-1.73-2.016L4.492 15H4.25A2.25 2.25 0 012 12.75V8.653c0-1.082.775-2.034 1.874-2.198.374-.056.75-.107 1.127-.153L5 2.75zm8.5 3.397a41.533 41.533 0 00-7 0V2.75a.25.25 0 01.25-.25h6.5a.25.25 0 01.25.25v3.397zM6.608 12.5a.25.25 0 00-.247.212l-.693 4.5a.25.25 0 00.247.288h8.17a.25.25 0 00.246-.288l-.692-4.5a.25.25 0 00-.247-.212H6.608z" clip-rule="evenodd"></path></svg> <span class="hidden lg:inline">Print</span></button> <button title="Format Document (⌘S)" class="button"><svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7"></path></svg> <span class="hidden lg:inline">Format</span></button></div> <!></div>'),root_7=from_html('<div class="p-8"><!></div>'),root=from_html('<div><main><div class="flex flex-1 min-h-0 overflow-hidden"><div class="flex-1 flex min-h-0 overflow-hidden"><!> <div><div><!> <div><div><!></div></div></div></div></div></div></main></div>');function _page(h,u){push(u,!0);const L=()=>store_get(page,"$page",v),[v,P]=setup_stores();let r=state(""),_=state(""),l=state(!1),m,S=state(0),F=state(!1),d=state(null),i=state(!0),x=state("pattern-solid-white"),b=state(null),n=[];const E=["prose-sm","prose-base","prose-lg","prose-xl","prose-2xl"],A=["font-sans","font-serif","font-mono"],w={medium:["bg-gray-500","bg-teal-500","bg-sky-500","bg-indigo-500"]};let o=state(proxy({proseSizeIndex:1,fontFamily:0,color:0,viewType:"document"}));const y=()=>{const t=getStyleState().darkMode;localStorage.setItem("preferences",JSON.stringify(get(o))),updateModeState("markdown",{proseSizeIndex:get(o).proseSizeIndex,color:get(o).color,viewType:get(o).viewType,viewMode:get(l),darkMode:t})},V=()=>{set(i,!get(i)),updateModeState("markdown",{sidebarOpen:get(i)}),__vitePreload(async()=>{const{emit:t}=await import("../chunks/BSqd-cP5.js");return{emit:t}},__vite__mapDeps([2,3]),import.meta.url).then(({emit:t})=>{t("sidebar-state-changed",{open:get(i)})})},ge=async()=>{get(o).viewType==="document"?get(o).viewType="slideshow":get(o).viewType="document",y(),__vitePreload(async()=>{const{emit:t}=await import("../chunks/BSqd-cP5.js");return{emit:t}},__vite__mapDeps([2,3]),import.meta.url).then(({emit:t})=>{t("read-view-type-changed",{viewType:get(o).viewType})}),await tick(),codeEval()},G=()=>{get(o).color<w.medium.length-1?get(o).color++:get(o).color=0,y()},ve=async()=>{set(r,""),set(d,null),await M()},Q=async()=>{try{const t=await open({multiple:!1,filters:[{name:"Markdown",extensions:["md","mdx","markdown"]}]});t&&(set(d,t,!0),set(r,await invoke("read_markdown_file",{path:get(d)}),!0),await M(),__vitePreload(async()=>{const{emit:a}=await import("../chunks/BSqd-cP5.js");return{emit:a}},__vite__mapDeps([2,3]),import.meta.url).then(({emit:a})=>{a("file-opened",{path:get(d),name:get(d).split("/").pop()||"Untitled"})}))}catch(t){console.error("Failed to open file:",t)}},D=async()=>{try{const{save:t}=await __vitePreload(async()=>{const{save:c}=await import("../chunks/XUVl8-cR.js");return{save:c}},__vite__mapDeps([4,3]),import.meta.url),a=await t({filters:[{name:"Markdown",extensions:["md","mdx","markdown"]}]});a&&(await invoke("write_markdown_file",{path:a,content:get(r)}),set(d,a,!0))}catch(t){console.error("Failed to save file:",t)}},X=async()=>{if(get(d)&&!get(l))try{await invoke("write_markdown_file",{path:get(d),content:get(r)})}catch(t){console.error("Failed to save:",t)}else get(d)||await D()},R=()=>{set(l,!get(l)),__vitePreload(async()=>{const{emit:t}=await import("../chunks/BSqd-cP5.js");return{emit:t}},__vite__mapDeps([2,3]),import.meta.url).then(({emit:t})=>{t("editing-mode-changed",{editing:!get(l)})})},me=t=>{X(),t.key==="i"&&m&&m.focus(),t.key==="Escape"?R():be()},z=async()=>{if(!m)return;const{formatMd:t}=await __vitePreload(async()=>{const{formatMd:c}=await import("../chunks/D9PjKXvN.js");return{formatMd:c}},__vite__mapDeps([5,6]),import.meta.url);let a=m.selectionStart-get(r).trim().length;set(r,await t(get(r)),!0),a+=get(r).trim().length,await M(),m.setSelectionRange(a,a)},he=t=>{(t.ctrlKey||t.metaKey)&&t.key==="s"&&(t.preventDefault(),z())};let B=state(!1),j=state(!1);const fe=async()=>{try{await navigator.clipboard.writeText(get(r)),set(B,!0),setTimeout(()=>set(B,!1),2e3)}catch(t){console.error("Failed to copy:",t)}},_e=async()=>{try{await navigator.clipboard.writeText(get(_)),set(j,!0),setTimeout(()=>set(j,!1),2e3)}catch(t){console.error("Failed to copy HTML:",t)}},Y=()=>{const t=window.open("","_blank");t&&(t.document.write(`<html><head><title>Print</title><style>${printCss}</style></head><body>`),t.document.write(get(_)),t.document.write("</body></html>"),t.document.close(),t.onload=()=>{t.print(),t.onafterprint=()=>{},t.close()})},M=async()=>{const{processor:t}=await __vitePreload(async()=>{const{processor:p}=await import("../chunks/B_OjSlQX.js");return{processor:p}},__vite__mapDeps([7,8,9]),import.meta.url);set(_,t.render(get(r)?get(r):gettingStarted.trim()),!0),await tick(),codeEval();const a=get(r).length,c=get(r).trim().split(/\s+/).filter(p=>p.length>0).length,k=Math.ceil(c/200);__vitePreload(async()=>{const{emit:p}=await import("../chunks/BSqd-cP5.js");return{emit:p}},__vite__mapDeps([2,3]),import.meta.url).then(({emit:p})=>{p("document-stats",{chars:a,words:c,readTime:k}),get(d)&&p("current-file-changed",{path:get(d)}),p("editing-mode-changed",{editing:!get(l)})})},be=()=>{if(get(o).viewType==="slideshow"&&!get(l)){if(!m)return;const t=get(r).slice(0,m.selectionStart);let a=t.split(`

---
`).length-1;t.startsWith(`---
`)&&a++,set(S,a,!0)}},Z=async t=>{try{set(r,await invoke("read_markdown_file",{path:t}),!0),set(d,t,!0),await M(),__vitePreload(async()=>{const{emit:a}=await import("../chunks/BSqd-cP5.js");return{emit:a}},__vite__mapDeps([2,3]),import.meta.url).then(({emit:a})=>{a("file-opened",{path:t,name:t.split("/").pop()||"Untitled"})})}catch(a){console.error("Failed to open file:",a)}};onMount(async()=>{const t=document.querySelector("textarea");t&&(m=t);const a=getStateForMode("markdown"),c=localStorage.getItem("preferences");c?set(o,JSON.parse(c),!0):(set(o,{proseSizeIndex:a.proseSizeIndex||1,fontFamily:0,color:a.color,viewType:a.viewType},!0),set(l,a.viewMode,!0),y()),a.darkMode??getStyleState().darkMode,set(i,a.sidebarOpen??!0,!0),n.push(await listen("menu-new",()=>ve())),n.push(await listen("menu-open",()=>Q())),n.push(await listen("menu-browse",()=>V())),n.push(await listen("menu-save",()=>X())),n.push(await listen("menu-save-as",()=>D())),n.push(await listen("menu-print",()=>Y())),n.push(await listen("menu-format",()=>z())),n.push(await listen("menu-format",()=>z())),n.push(await listen("file-open",s=>{const J=s.payload;Z(J)})),n.push(await listen("background-pattern-changed",s=>{set(x,s.payload.pattern,!0)})),n.push(await listen("edit-mode-changed",s=>{set(l,!s.payload.isEditing)})),n.push(await listen("change-color",s=>{set(b,s.payload.hex,!0)}));const k=L().url.searchParams.get("file"),p=L().url.searchParams.get("view"),T=getLastFile();if(k)try{set(r,await invoke("read_markdown_file",{path:k}),!0),set(d,k,!0),p==="slideshow"&&(get(o).viewType="slideshow",y())}catch(s){console.error("Failed to open file from URL:",s)}else if(T)try{set(r,await invoke("read_markdown_file",{path:T}),!0),set(d,T,!0)}catch(s){console.error("Failed to restore last file:",s),get(r)||set(r,gettingStarted,!0)}else get(r)||set(r,gettingStarted,!0);n.push(await listen("toggle-sidebar",s=>{set(i,s.payload.open,!0),updateModeState("markdown",{sidebarOpen:get(i)})})),n.push(await listen("toggle-edit",()=>{R()})),n.push(await listen("editing-mode-changed",s=>{set(l,!s.payload.editing)})),n.push(await listen("toggle-view-type",()=>{ge()})),n.push(await listen("change-color",()=>{G()})),n.push(await listen("dark-mode-changed",s=>{y()})),n.push(await listen("reset-mode-display",async()=>{console.log("[Editor] Reset display triggered"),localStorage.removeItem("preferences");const s=getStateForMode("markdown");get(o).proseSizeIndex=s.proseSizeIndex||1,get(o).fontFamily=0,get(o).color=s.color||0,get(o).viewType=s.viewType||"document",set(l,s.viewMode||!1,!0),set(b,null),console.log("[Editor] Preferences reset to:",get(o)),console.log("[Editor] editorBgColor cleared:",get(b)),y(),await tick(),await M()})),await M(),await __vitePreload(()=>import("../chunks/BvgltCUz.js"),__vite__mapDeps([10,11]),import.meta.url),await __vitePreload(()=>import("../chunks/BYKvG165.js"),__vite__mapDeps([12,11]),import.meta.url),await __vitePreload(()=>import("../chunks/Ds4DHZit.js"),__vite__mapDeps([13,11]),import.meta.url),await tick(),set(F,!0)}),onDestroy(()=>{n.forEach(t=>t())});var O=root();event("keyup",$document,me),event("keydown",$document,he);var K=child(O),ee=child(K),te=child(ee),ae=child(te);{var we=t=>{var a=root_1(),c=child(a);FileSidebar(c,{get isOpen(){return get(i)},get currentFilePath(){return get(d)},onFileSelect:Z,onToggle:V,mode:"markdown"}),reset(a),append(t,a)};if_block(ae,t=>{get(i)&&t(we)})}var q=sibling(ae,2);let oe;var U=child(q),re=child(U);{var ye=t=>{var a=root_2(),c=child(a),k=child(c);k.__click=V;var p=sibling(k,2);p.__click=R;var T=child(p),s=child(T);{var J=g=>{var f=root_3();next(),append(g,f)},Ae=g=>{var f=root_4();append(g,f)};if_block(s,g=>{get(l)?g(J):g(Ae,!1)})}reset(T);var ie=sibling(T,2),Me=child(ie,!0);reset(ie),reset(p);var I=sibling(p,4);I.__click=G;var Te=child(I);next(2),reset(I);var se=sibling(I,2);se.__click=Q;var le=sibling(se,2);le.__click=D;var $=sibling(le,2);$.__click=fe;var de=sibling(child($),2),Ee=child(de,!0);reset(de),reset($);var H=sibling($,2);H.__click=_e;var ce=sibling(child(H),2),Ce=child(ce,!0);reset(ce),reset(H);var pe=sibling(H,2);pe.__click=Y;var Le=sibling(pe,2);Le.__click=z,reset(c);var Pe=sibling(c,2);{var Fe=g=>{var f=root_5(),C=child(f);remove_textarea_child(C),C.__input=M;var ue=sibling(C,2),Oe=sibling(child(ue),10);Oe.textContent="{ }",next(10),reset(ue),reset(f),template_effect(()=>{set_class(f,1,`flex-1 overflow-hidden ${w.medium[get(o).color]??""}`),set_style(C,get(b)?`background-color: ${get(b)} !important;`:"")}),bind_value(C,()=>get(r),Ie=>set(r,Ie)),append(g,f)},ze=g=>{var f=root_6();template_effect(()=>set_class(f,1,`flex-1 overflow-hidden ${w.medium[get(o).color]??""} flex items-center justify-center`)),append(g,f)};if_block(Pe,g=>{get(F)?g(Fe):g(ze,!1)})}reset(a),template_effect(()=>{set_class(k,1,`button ${get(i)?"bg-gray-200 dark:bg-gray-700":""}`),set_class(p,1,`button ${get(l)?"bg-teal-600 dark:bg-teal-700":""}`),set_text(Me,get(l)?"View":"Edit"),set_class(Te,1,`h-5 w-5 rounded border-2 border-gray-400 dark:border-gray-600 ${w.medium[get(o).color]??""}`),set_text(Ee,get(B)?"✓ Copied!":"Copy MD"),set_text(Ce,get(j)?"✓ Copied!":"Copy HTML")}),append(t,a)};if_block(re,t=>{get(l)||t(ye)})}var N=sibling(re,2);let ne;var W=child(N),ke=child(W);{var xe=t=>{var a=root_7(),c=child(a);html(c,()=>get(_)),reset(a),append(t,a)},Se=t=>{Slides(t,{get html(){return get(_)},get viewMode(){return get(l)},set viewMode(a){set(l,a,!0)},get currentSlide(){return get(S)},set currentSlide(a){set(S,a,!0)}})};if_block(ke,t=>{get(o).viewType==="document"?t(xe):t(Se,!1)})}reset(W),reset(N),reset(U),reset(q),reset(te),reset(ee),reset(K),reset(O),template_effect(()=>{set_class(O,1,`flex flex-col h-full overflow-hidden bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-50 selection:bg-gray-400/40 ${A[get(o).fontFamily]??""}`),set_class(K,1,`flex flex-1 min-h-0 overflow-hidden ${get(x)??""}`),oe=set_class(q,1,"flex-1 flex min-h-0 overflow-hidden",null,oe,{"w-full":!get(i)}),set_class(U,1,`grid flex-1 min-h-0 overflow-hidden ${!get(l)&&"lg:grid-cols-2"}`),ne=set_class(N,1,"flex flex-col min-h-0 overflow-y-auto bg-white dark:bg-gray-950",null,ne,{"dark:border-none":get(o).viewType==="slideshow"&&get(l)}),set_class(W,1,`prose dark:prose-invert prose-img:rounded-lg mx-auto max-w-[72ch] break-words ${E[get(o).proseSizeIndex]??""}`)}),append(h,O),pop(),P()}delegate(["click","input"]);export{_page as component,_page$1 as universal};
